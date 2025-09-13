import logging
import re
import os
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json
import subprocess
import tempfile
import yaml

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.config import settings

logger = logging.getLogger(__name__)


class ResumeState(TypedDict):
    """State object for the resume modifier agent"""
    session_id: str
    job_description: str
    company_name: str
    position_title: str
    requirements: Optional[str]
    original_resume: str
    modified_resume: str
    rendercv_yaml: str
    current_step: str
    error: Optional[str]


class ResumeModifierAgent:
    """
    Main agent for modifying resumes based on job descriptions using LangGraph
    """
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.graph = self._build_graph()
        self.sessions = {}  # In-memory session storage (use Redis in production)
    
    def _initialize_llm(self):
        """Initialize the language model - only use Anthropic"""
        if settings.anthropic_api_key:
            return ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                temperature=0.3,
                max_tokens=10000
            )
        else:
            raise ValueError("Anthropic API key is required for LaTeX modification")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(ResumeState)
        
        # Add nodes
        workflow.add_node("load_resume", self._load_resume_node)
        workflow.add_node("modify_content", self._modify_content_node)
        workflow.add_node("convert_to_rendercv", self._convert_to_rendercv_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Add edges
        workflow.set_entry_point("load_resume")
        workflow.add_edge("load_resume", "modify_content")
        workflow.add_edge("modify_content", "convert_to_rendercv")
        workflow.add_edge("convert_to_rendercv", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    async def _load_resume_node(self, state: ResumeState) -> ResumeState:
        """Load the current resume content"""
        try:
            logger.info(f"Loading resume for session {state['session_id']}")
            
            # Load the LaTeX resume
            resume_path = os.path.join(settings.cv_directory, "main.tex")
            if os.path.exists(resume_path):
                with open(resume_path, 'r', encoding='utf-8') as file:
                    resume_content = file.read()
                
                state["original_resume"] = resume_content
                state["current_step"] = "resume_loaded"
                logger.info("Resume loaded successfully")
            else:
                state["error"] = "Resume file not found"
                logger.error("Resume file not found")
                
        except Exception as e:
            state["error"] = f"Error loading resume: {str(e)}"
            logger.error(f"Error loading resume: {str(e)}", exc_info=True)
            
        return state
    
    async def _modify_content_node(self, state: ResumeState) -> ResumeState:
        """Modify the resume content based on job description"""
        try:
            logger.info(f"Modifying content for session {state['session_id']}")
            
            modification_prompt = f"""
Task
You are a professional resume optimizer. Given a job description and a comprehensive resume, your task is to modify the resume by removing or reducing irrelevant experience points while maintaining the original LaTeX structure and formatting. You must NEVER add new information, skills, or experiences that are not already present in the original resume.

Instructions
Input Requirements

Job Description: A detailed job posting including required skills, qualifications, and responsibilities
Original Resume: A comprehensive resume in LaTeX format

Output Requirements

Modified resume in LaTeX format
Same structural layout as the original
Same formatting, fonts, and styling
Reduced content focused on relevance to the target job

Modification Rules
What You CAN Do:

Remove entire bullet points that are completely irrelevant to the job
Shorten bullet points by removing irrelevant details while keeping the core relevant information
Reorder bullet points to prioritize most relevant experiences first
Remove entire job positions if they add no value to the application
Consolidate similar experiences by combining related bullet points (only if they describe the same actual experience)
Remove irrelevant skills from skills sections
Remove irrelevant projects, certifications, or activities

What You CANNOT Do:

Add new experiences, skills, or qualifications not present in the original
Exaggerate or embellish existing experiences
Change job titles, company names, or dates
Add new technical skills not mentioned in the original
Create new bullet points with fabricated information
Change the fundamental structure of the LaTeX document
Modify contact information or personal details

Optimization Strategy

Analyze the job description for:

Required technical skills
Preferred qualifications
Key responsibilities
Industry-specific requirements
Soft skills mentioned


Evaluate each resume section for relevance:

Rate each bullet point's relevance (High/Medium/Low)
Identify transferable skills even from different industries
Look for quantifiable achievements that demonstrate required competencies


Apply modifications:

Remove Low relevance items
Shorten Medium relevance items to focus on relevant aspects
Prioritize High relevance items
Ensure most relevant experiences appear first


Maintain professional quality:

Keep 2-4 bullet points per relevant job
Maintain action-oriented language
Preserve quantifiable achievements
Ensure logical flow and readability



Example Transformation
Original bullet point:
\\item Managed a team of 5 developers to build a customer relationship management system using Java, Spring Boot, and MySQL, resulting in 30\\% improvement in sales team efficiency and \\$200K annual cost savings

For a Data Science position, modify to:
\\item Led technical team of 5 to develop data-driven CRM system with MySQL database, achieving 30\\% efficiency improvement through data analysis and optimization

For an unrelated position, remove entirely or significantly reduce:
\\item Managed cross-functional team of 5, delivering project 3 months ahead of schedule with \\$200K cost savings

Quality Checklist
Before outputting the modified resume, ensure:

☐ No fabricated information has been added
☐ LaTeX structure and formatting remain intact
☐ Most relevant experiences are prominently featured
☐ Resume length is appropriate (typically 1-2 pages)
☐ All claims are truthful and verifiable
☐ Professional tone and language are maintained
☐ Contact information and personal details are unchanged

Output Format
Provide the complete modified LaTeX resume code, ready to compile, with clear comments indicating major changes made.

Now apply this to the following:

Job Description:
Company: {state['company_name']}
Position: {state['position_title']}
Job Description: {state['job_description']}
Additional Requirements: {state.get('requirements', 'None')}

Original Resume:
{state['original_resume']}

Return the complete modified LaTeX document.
            """
            
            messages = [
                SystemMessage(content="You are a professional resume optimizer specializing in LaTeX formatting. Modify resumes to match job requirements while maintaining accuracy and professionalism. Never add new information that wasn't in the original resume."),
                HumanMessage(content=modification_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            state["modified_resume"] = response.content
            state["current_step"] = "content_modified"
            logger.info("Resume content modification completed")
            
        except Exception as e:
            state["error"] = f"Error modifying content: {str(e)}"
            logger.error(f"Error modifying content: {str(e)}", exc_info=True)
            
        return state
    
    async def _convert_to_rendercv_node(self, state: ResumeState) -> ResumeState:
        """Convert LaTeX resume to RenderCV YAML format"""
        try:
            logger.info(f"Converting to RenderCV format for session {state['session_id']}")
            
            conversion_prompt = f"""
Task: Convert a LaTeX resume to RenderCV YAML format.

You are an expert in both LaTeX and RenderCV YAML format. Convert the following LaTeX resume into a properly structured RenderCV YAML file.

RenderCV YAML Structure:
```yaml
cv:
  name: Full Name
  location: City, Country
  email: email@domain.com
  phone: "+1-234-567-8900"
  website: https://website.com
  social_networks:
    - network: LinkedIn
      username: username
    - network: GitHub
      username: username
  sections:
    summary:
      - Brief professional summary paragraph
    education:
      - institution: University Name
        area: Field of Study
        degree: Degree Type
        start_date: YYYY-MM
        end_date: YYYY-MM
        highlights:
          - GPA: 3.8/4.0
          - Relevant coursework: Course1, Course2
    experience:
      - company: Company Name
        position: Job Title
        location: City, State
        start_date: YYYY-MM
        end_date: YYYY-MM
        highlights:
          - Achievement or responsibility 1
          - Achievement or responsibility 2
    projects:
      - name: Project Name
        start_date: YYYY-MM
        end_date: YYYY-MM
        highlights:
          - Project description
          - Technologies used
    technologies:
      - label: Programming Languages
        details: Python, JavaScript, Java
      - label: Frameworks
        details: React, Flask, Django
    certifications:
      - name: Certification Name
        date: YYYY-MM
        details: Issuing organization
```

Instructions:
1. Extract personal information (name, contact details) from LaTeX
2. Parse education section with degrees, institutions, dates
3. Convert work experience with companies, positions, dates, and achievements
4. Extract skills/technologies and group them logically
5. Include projects, certifications, and other relevant sections
6. Maintain all important details while converting format
7. Use proper YAML syntax and indentation
8. Convert LaTeX date formats to YYYY-MM format
9. Convert LaTeX bullet points (\\item) to YAML list items
10. Extract meaningful section headers and content

LaTeX Resume to Convert:
{state['modified_resume']}

Return only the complete YAML content for RenderCV, properly formatted and ready to use.
            """
            
            messages = [
                SystemMessage(content="You are an expert in converting LaTeX resumes to RenderCV YAML format. Ensure accurate extraction of all information while maintaining proper YAML structure."),
                HumanMessage(content=conversion_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            state["rendercv_yaml"] = response.content
            state["current_step"] = "converted_to_rendercv"
            logger.info("Resume converted to RenderCV YAML format")
            
        except Exception as e:
            state["error"] = f"Error converting to RenderCV: {str(e)}"
            logger.error(f"Error converting to RenderCV: {str(e)}", exc_info=True)
            
        return state
    
    def _generate_pdf_with_rendercv(self, yaml_content: str, output_path: str) -> str:
        """Generate PDF using RenderCV"""
        try:
            # Create a temporary directory for RenderCV
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write YAML content to temporary file
                yaml_file = os.path.join(temp_dir, "resume.yaml")
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
                
                # Generate a temporary PDF path
                temp_pdf_path = os.path.join(temp_dir, "output.pdf")
                
                # Use RenderCV to generate PDF with specific output path
                result = subprocess.run(
                    ['rendercv', 'render', yaml_file, '--pdf-path', temp_pdf_path],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )
                
                if result.returncode != 0:
                    logger.error(f"RenderCV failed: {result.stderr}")
                    raise Exception(f"RenderCV failed: {result.stderr}")
                
                # Check if PDF was generated and copy to final output path
                if os.path.exists(temp_pdf_path):
                    import shutil
                    shutil.copy2(temp_pdf_path, output_path)
                    return output_path
                else:
                    raise Exception("PDF file was not generated by RenderCV")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"RenderCV subprocess error: {str(e)}")
            raise Exception(f"RenderCV subprocess error: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating PDF with RenderCV: {str(e)}")
            raise Exception(f"Error generating PDF with RenderCV: {str(e)}")
    
    def _compile_latex_to_pdf(self, latex_content: str, output_path: str) -> str:
        """Compile LaTeX content to PDF"""
        try:
            # Create a temporary directory for LaTeX compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write LaTeX content to temporary file
                tex_file = os.path.join(temp_dir, "resume.tex")
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Compile LaTeX to PDF
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )
                
                if result.returncode != 0:
                    logger.error(f"LaTeX compilation failed: {result.stderr}")
                    raise Exception(f"LaTeX compilation failed: {result.stderr}")
                
                # Copy PDF to output directory
                pdf_file = os.path.join(temp_dir, "resume.pdf")
                if os.path.exists(pdf_file):
                    import shutil
                    shutil.copy2(pdf_file, output_path)
                    return output_path
                else:
                    raise Exception("PDF file was not generated")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"LaTeX compilation error: {str(e)}")
            raise Exception(f"LaTeX compilation error: {str(e)}")
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {str(e)}")
            raise Exception(f"Error compiling LaTeX: {str(e)}")
    
    async def _format_output_node(self, state: ResumeState) -> ResumeState:
        """Format the final output and save results"""
        try:
            logger.info(f"Formatting output for session {state['session_id']}")
            
            # Save the modified resume
            output_dir = settings.output_directory
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tex_file = f"modified_resume_{state['session_id']}_{timestamp}.tex"
            yaml_file = f"modified_resume_{state['session_id']}_{timestamp}.yaml"
            pdf_file_latex = f"modified_resume_{state['session_id']}_{timestamp}_latex.pdf"
            pdf_file_rendercv = f"modified_resume_{state['session_id']}_{timestamp}_rendercv.pdf"
            
            tex_path = os.path.join(output_dir, tex_file)
            yaml_path = os.path.join(output_dir, yaml_file)
            pdf_path_latex = os.path.join(output_dir, pdf_file_latex)
            pdf_path_rendercv = os.path.join(output_dir, pdf_file_rendercv)
            
            # Save LaTeX file
            with open(tex_path, 'w', encoding='utf-8') as file:
                file.write(state["modified_resume"])
            
            # Save YAML file
            with open(yaml_path, 'w', encoding='utf-8') as file:
                file.write(state["rendercv_yaml"])
            
            # Try to generate PDF with RenderCV (primary method)
            rendercv_pdf_path = None
            try:
                self._generate_pdf_with_rendercv(state["rendercv_yaml"], pdf_path_rendercv)
                rendercv_pdf_path = pdf_path_rendercv
                logger.info(f"RenderCV PDF generated successfully: {pdf_path_rendercv}")
            except Exception as e:
                logger.warning(f"RenderCV PDF generation failed: {str(e)}")
            
            # Store session data
            self.sessions[state["session_id"]] = {
                "timestamp": datetime.now(),
                "company_name": state["company_name"],
                "position_title": state["position_title"],
                "tex_file": tex_path,
                "yaml_file": yaml_path,
                "pdf_file_rendercv": rendercv_pdf_path,
                "job_description": state["job_description"]
            }
            
            state["current_step"] = "completed"
            logger.info(f"Output formatted and saved")
            
        except Exception as e:
            state["error"] = f"Error formatting output: {str(e)}"
            logger.error(f"Error formatting output: {str(e)}", exc_info=True)
            
        return state
    
    async def modify_resume(self, job_description: str, company_name: str, 
                          position_title: str, requirements: Optional[str] = None,
                          session_id: str = None) -> Dict[str, Any]:
        """Main method to modify resume based on job description"""
        
        # Initialize state
        initial_state = ResumeState(
            session_id=session_id,
            job_description=job_description,
            company_name=company_name,
            position_title=position_title,
            requirements=requirements,
            original_resume="",
            modified_resume="",
            rendercv_yaml="",
            current_step="starting",
            error=None
        )
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        # Get session data to return file paths
        session_data = self.sessions.get(result["session_id"], {})
        
        return {
            "modified_content": result["modified_resume"],
            "rendercv_yaml": result["rendercv_yaml"],
            "tex_file": session_data.get("tex_file"),
            "yaml_file": session_data.get("yaml_file"),
            "pdf_file_latex": session_data.get("pdf_file_latex"),
            "pdf_file_rendercv": session_data.get("pdf_file_rendercv")
        }
    
    async def get_current_resume_content(self) -> str:
        """Get the current resume content"""
        resume_path = os.path.join(settings.cv_directory, "main.tex")
        
        if os.path.exists(resume_path):
            with open(resume_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            raise FileNotFoundError("Resume file not found")
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get modification history for a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            return {"message": "Session not found"}
