import logging
import re
import os
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
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
    analysis_results: Dict[str, Any]
    suggestions: List[str]
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
        """Initialize the language model"""
        if settings.openai_api_key:
            return ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.3
            )
        elif settings.anthropic_api_key:
            return ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                temperature=0.3
            )
        else:
            raise ValueError("No API key provided for language model")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(ResumeState)
        
        # Add nodes
        workflow.add_node("load_resume", self._load_resume_node)
        workflow.add_node("analyze_job", self._analyze_job_node)
        workflow.add_node("identify_gaps", self._identify_gaps_node)
        workflow.add_node("modify_content", self._modify_content_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Add edges
        workflow.set_entry_point("load_resume")
        workflow.add_edge("load_resume", "analyze_job")
        workflow.add_edge("analyze_job", "identify_gaps")
        workflow.add_edge("identify_gaps", "modify_content")
        workflow.add_edge("modify_content", "format_output")
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
    
    async def _analyze_job_node(self, state: ResumeState) -> ResumeState:
        """Analyze the job description to extract key requirements"""
        try:
            logger.info(f"Analyzing job description for session {state['session_id']}")
            
            analysis_prompt = f"""
            Analyze this job description and extract key information:
            
            Company: {state['company_name']}
            Position: {state['position_title']}
            Job Description: {state['job_description']}
            Additional Requirements: {state.get('requirements', 'None')}
            
            Extract and return:
            1. Key technical skills required
            2. Soft skills mentioned
            3. Experience level expected
            4. Industry/domain knowledge
            5. Specific technologies/tools mentioned
            6. Company culture indicators
            7. Key responsibilities
            8. Preferred qualifications vs requirements
            
            Return as structured JSON.
            """
            
            messages = [
                SystemMessage(content="You are an expert job description analyzer. Extract key requirements and qualifications from job postings."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the analysis (assuming JSON response)
            try:
                analysis_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: create structured analysis from text
                analysis_data = {
                    "raw_analysis": response.content,
                    "extraction_method": "text_fallback"
                }
            
            state["analysis_results"] = analysis_data
            state["current_step"] = "job_analyzed"
            logger.info("Job description analysis completed")
            
        except Exception as e:
            state["error"] = f"Error analyzing job description: {str(e)}"
            logger.error(f"Error analyzing job description: {str(e)}", exc_info=True)
            
        return state
    
    async def _identify_gaps_node(self, state: ResumeState) -> ResumeState:
        """Identify gaps between resume and job requirements"""
        try:
            logger.info(f"Identifying gaps for session {state['session_id']}")
            
            gap_analysis_prompt = f"""
            Compare this resume with the job requirements and identify gaps:
            
            RESUME CONTENT:
            {state['original_resume']}
            
            JOB ANALYSIS:
            {json.dumps(state['analysis_results'], indent=2)}
            
            Identify:
            1. Missing technical skills
            2. Missing experience areas
            3. Weak points in current content
            4. Opportunities to better align with job requirements
            5. Keywords that should be added
            6. Experience that should be emphasized
            7. Skills that should be de-emphasized
            
            Provide specific, actionable recommendations for resume modification.
            """
            
            messages = [
                SystemMessage(content="You are an expert resume consultant. Identify gaps between resumes and job requirements."),
                HumanMessage(content=gap_analysis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Extract suggestions from the response
            suggestions = self._extract_suggestions(response.content)
            state["suggestions"] = suggestions
            state["current_step"] = "gaps_identified"
            logger.info(f"Identified {len(suggestions)} suggestions for improvement")
            
        except Exception as e:
            state["error"] = f"Error identifying gaps: {str(e)}"
            logger.error(f"Error identifying gaps: {str(e)}", exc_info=True)
            
        return state
    
    async def _modify_content_node(self, state: ResumeState) -> ResumeState:
        """Modify the resume content based on analysis"""
        try:
            logger.info(f"Modifying content for session {state['session_id']}")
            
            modification_prompt = f"""
            Modify this LaTeX resume to better align with the job requirements:
            
            ORIGINAL RESUME:
            {state['original_resume']}
            
            JOB REQUIREMENTS:
            {json.dumps(state['analysis_results'], indent=2)}
            
            SUGGESTIONS TO IMPLEMENT:
            {chr(10).join(state['suggestions'])}
            
            Rules for modification:
            1. Maintain the original LaTeX structure and formatting
            2. Keep all personal information unchanged
            3. Emphasize relevant experience and skills
            4. Add missing keywords naturally
            5. Reorder content if beneficial
            6. Enhance bullet points with quantifiable achievements
            7. Ensure readability and professional tone
            8. Maintain truthfulness - only enhance existing experience
            
            Return the complete modified LaTeX document.
            """
            
            messages = [
                SystemMessage(content="You are an expert resume writer specializing in LaTeX formatting. Modify resumes to match job requirements while maintaining accuracy and professionalism."),
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
    
    async def _format_output_node(self, state: ResumeState) -> ResumeState:
        """Format the final output and save results"""
        try:
            logger.info(f"Formatting output for session {state['session_id']}")
            
            # Save the modified resume
            output_dir = settings.output_directory
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"modified_resume_{state['session_id']}_{timestamp}.tex"
            output_path = os.path.join(output_dir, output_file)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(state["modified_resume"])
            
            # Store session data
            self.sessions[state["session_id"]] = {
                "timestamp": datetime.now(),
                "company_name": state["company_name"],
                "position_title": state["position_title"],
                "output_file": output_path,
                "suggestions": state["suggestions"],
                "analysis": state["analysis_results"]
            }
            
            state["current_step"] = "completed"
            logger.info(f"Output formatted and saved to {output_path}")
            
        except Exception as e:
            state["error"] = f"Error formatting output: {str(e)}"
            logger.error(f"Error formatting output: {str(e)}", exc_info=True)
            
        return state
    
    def _extract_suggestions(self, analysis_text: str) -> List[str]:
        """Extract actionable suggestions from analysis text"""
        suggestions = []
        
        # Simple extraction based on numbered lists or bullet points
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                line.startswith(('•', '-', '*')) or
                'should' in line.lower() or 'recommend' in line.lower()):
                if len(line) > 10:  # Filter out very short lines
                    suggestions.append(line)
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
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
            analysis_results={},
            suggestions=[],
            current_step="starting",
            error=None
        )
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        return {
            "modified_content": result["modified_resume"],
            "suggestions": result["suggestions"],
            "analysis": result["analysis_results"]
        }
    
    async def analyze_job_description(self, job_description: str, company_name: str, 
                                    position_title: str) -> Dict[str, Any]:
        """Analyze job description without modifying resume"""
        
        analysis_prompt = f"""
        Analyze this job description in detail:
        
        Company: {company_name}
        Position: {position_title}
        Job Description: {job_description}
        
        Provide comprehensive analysis including:
        - Key skills and technologies
        - Experience requirements
        - Company culture insights
        - Salary expectations (if mentioned)
        - Growth opportunities
        - Required vs preferred qualifications
        """
        
        messages = [
            SystemMessage(content="You are an expert job market analyzer."),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "analysis": response.content,
            "company": company_name,
            "position": position_title
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
