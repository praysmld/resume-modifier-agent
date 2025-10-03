"""
RenderCV API endpoints for generating professional PDF resumes
"""
import os
import uuid
import tempfile
import subprocess
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agents.graph import ResumeModifierAgent
from app.config import settings

router = APIRouter(prefix="/rendercv", tags=["rendercv"])

# Pydantic models for request/response
class ResumeModificationRequest(BaseModel):
    job_description: str
    company_name: str
    position_title: str
    requirements: Optional[str] = None

class ResumeModificationResponse(BaseModel):
    session_id: str
    modified_content: str
    rendercv_yaml: str
    tex_file: Optional[str] = None
    yaml_file: Optional[str] = None
    pdf_file_latex: Optional[str] = None
    pdf_file_rendercv: Optional[str] = None
    message: str

# Initialize the resume modifier agent
agent = ResumeModifierAgent()

@router.post("/modify-resume", response_model=ResumeModificationResponse)
async def modify_resume_with_rendercv(request: ResumeModificationRequest):
    """
    Modify resume based on job description and generate PDF using RenderCV
    
    This endpoint:
    1. Loads the original LaTeX resume
    2. Modifies it based on the job description using AI
    3. Converts the modified resume to RenderCV YAML format
    4. Generates PDF using both LaTeX (fallback) and RenderCV (primary)
    5. Returns file paths and content
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Modify resume using the agent
        result = await agent.modify_resume(
            job_description=request.job_description,
            company_name=request.company_name,
            position_title=request.position_title,
            requirements=request.requirements,
            session_id=session_id
        )
        
        # Prepare response
        response = ResumeModificationResponse(
            session_id=session_id,
            modified_content=result.get("modified_content", ""),
            rendercv_yaml=result.get("rendercv_yaml", ""),
            tex_file=result.get("tex_file"),
            yaml_file=result.get("yaml_file"),
            pdf_file_latex=result.get("pdf_file_latex"),
            pdf_file_rendercv=result.get("pdf_file_rendercv"),
            message="Resume modified and PDF generated successfully"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error modifying resume: {str(e)}")

@router.get("/download/{session_id}/{file_type}")
async def download_resume_file(session_id: str, file_type: str):
    """
    Download generated resume files
    
    file_type options:
    - tex: Modified LaTeX file
    - yaml: RenderCV YAML file  
    - pdf-latex: PDF generated from LaTeX
    - pdf-rendercv: PDF generated from RenderCV
    """
    try:
        # Get session data
        session_data = await agent.get_session_history(session_id)
        
        if "message" in session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Determine file path based on file type
        file_path = None
        media_type = "application/octet-stream"
        filename = f"resume_{session_id}"
        
        if file_type == "tex":
            file_path = session_data.get("tex_file")
            media_type = "text/plain"
            filename += ".tex"
        elif file_type == "yaml":
            file_path = session_data.get("yaml_file")
            media_type = "text/yaml"
            filename += ".yaml"
        elif file_type == "pdf-latex":
            file_path = session_data.get("pdf_file_latex")
            media_type = "application/pdf"
            filename += "_latex.pdf"
        elif file_type == "pdf-rendercv":
            file_path = session_data.get("pdf_file_rendercv")
            media_type = "application/pdf"
            filename += "_rendercv.pdf"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.post("/render-yaml")
async def render_yaml_to_pdf(yaml_content: str = Form(...)):
    """
    Directly render YAML content to PDF using RenderCV
    
    This endpoint allows users to provide YAML content directly
    and get a PDF generated using RenderCV
    """
    try:
        # Generate unique session ID for this render
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        output_dir = settings.output_directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output paths
        yaml_file = f"direct_render_{session_id}_{timestamp}.yaml"
        pdf_file = f"direct_render_{session_id}_{timestamp}.pdf"
        yaml_path = os.path.join(output_dir, yaml_file)
        pdf_path = os.path.join(output_dir, pdf_file)
        
        # Save YAML content
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        # Generate PDF using RenderCV
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy YAML to temp directory
                temp_yaml = os.path.join(temp_dir, "resume.yaml")
                shutil.copy2(yaml_path, temp_yaml)
                
                # Run RenderCV
                result = subprocess.run(
                    ['rendercv', 'render', temp_yaml],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )
                
                if result.returncode != 0:
                    raise Exception(f"RenderCV failed: {result.stderr}")
                
                # Find generated PDF
                pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
                if pdf_files:
                    temp_pdf = os.path.join(temp_dir, pdf_files[0])
                    shutil.copy2(temp_pdf, pdf_path)
                else:
                    raise Exception("PDF file was not generated")
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"RenderCV generation failed: {str(e)}")
        
        # Return PDF file
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"resume_{session_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering YAML: {str(e)}")

@router.post("/upload-yaml")
async def upload_yaml_and_render(yaml_file: UploadFile = File(...)):
    """
    Upload a YAML file and render it to PDF using RenderCV
    """
    try:
        # Validate file type
        if not yaml_file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="File must be a YAML file")
        
        # Read YAML content
        yaml_content = await yaml_file.read()
        yaml_text = yaml_content.decode('utf-8')
        
        # Use the render-yaml endpoint functionality
        return await render_yaml_to_pdf(yaml_content=yaml_text)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {str(e)}")

@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a resume modification session
    """
    try:
        session_data = await agent.get_session_history(session_id)
        
        if "message" in session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Return session information (without file contents)
        return {
            "session_id": session_id,
            "timestamp": session_data.get("timestamp"),
            "company_name": session_data.get("company_name"),
            "position_title": session_data.get("position_title"),
            "files_available": {
                "tex": session_data.get("tex_file") is not None,
                "yaml": session_data.get("yaml_file") is not None,
                "pdf_latex": session_data.get("pdf_file_latex") is not None,
                "pdf_rendercv": session_data.get("pdf_file_rendercv") is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Check if RenderCV is installed and working
    """
    try:
        # Check if RenderCV is available
        result = subprocess.run(['rendercv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return {
                "status": "healthy",
                "rendercv_version": result.stdout.strip(),
                "message": "RenderCV is installed and working"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "RenderCV command failed",
                "error": result.stderr
            }
    except FileNotFoundError:
        return {
            "status": "unhealthy",
            "message": "RenderCV is not installed or not in PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking RenderCV: {str(e)}"
        } 