import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agents.graph import ResumeModifierAgent
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class JobDescriptionRequest(BaseModel):
    job_description: str
    company_name: str
    position_title: str
    requirements: Optional[str] = None
    session_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.version
    )


@router.post("/modify-resume")
async def modify_resume(request: JobDescriptionRequest):
    """
    Modify the resume based on job description input and return PDF file
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Starting resume modification for session {session_id}")
        
        # Initialize the resume modifier agent
        agent = ResumeModifierAgent()
        
        # Process the job description and modify the resume
        result = await agent.modify_resume(
            job_description=request.job_description,
            company_name=request.company_name,
            position_title=request.position_title,
            requirements=request.requirements,
            session_id=session_id
        )
        
        # Create a sanitized filename for the PDF
        company_safe = "".join(c for c in request.company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        position_safe = "".join(c for c in request.position_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"modified_resume_{company_safe}_{position_safe}_{session_id[:8]}.pdf"
        
        # Return RenderCV PDF file if available
        if result.get("pdf_file_rendercv") and os.path.exists(result["pdf_file_rendercv"]):
            logger.info(f"Returning RenderCV PDF: {result['pdf_file_rendercv']}")
            return FileResponse(
                path=result["pdf_file_rendercv"],
                media_type='application/pdf',
                filename=filename,
                headers={
                    "X-Session-ID": session_id,
                    "X-Company": request.company_name,
                    "X-Position": request.position_title,
                    "X-PDF-Source": "RenderCV"
                }
            )
        # Fallback to LaTeX PDF if available
        elif result.get("pdf_file_latex") and os.path.exists(result["pdf_file_latex"]):
            logger.info(f"Returning LaTeX PDF: {result['pdf_file_latex']}")
            return FileResponse(
                path=result["pdf_file_latex"],
                media_type='application/pdf',
                filename=filename,
                headers={
                    "X-Session-ID": session_id,
                    "X-Company": request.company_name,
                    "X-Position": request.position_title,
                    "X-PDF-Source": "LaTeX"
                }
            )
        # Fallback to LaTeX source file if PDF compilation failed
        elif result.get("tex_file") and os.path.exists(result["tex_file"]):
            logger.warning("PDF compilation failed, returning LaTeX source file")
            tex_filename = f"modified_resume_{company_safe}_{position_safe}_{session_id[:8]}.tex"
            return FileResponse(
                path=result["tex_file"],
                media_type='application/x-latex',
                filename=tex_filename,
                headers={
                    "X-Session-ID": session_id,
                    "X-Company": request.company_name,
                    "X-Position": request.position_title,
                    "X-Warning": "PDF compilation failed, returning LaTeX source",
                    "X-PDF-Source": "LaTeX-Source"
                }
            )
        else:
            logger.error("No output file was generated")
            raise HTTPException(
                status_code=500,
                detail="No output file was generated. Please check the logs for more details."
            )
        
    except Exception as e:
        logger.error(f"Error modifying resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to modify resume: {str(e)}"
        )


@router.post("/modify-resume-pdf")
async def modify_resume_pdf_only(request: JobDescriptionRequest):
    """
    Modify the resume based on job description and return only PDF file.
    This endpoint will fail if PDF generation is not successful.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Starting resume modification for PDF output for session {session_id}")
        
        # Initialize the resume modifier agent
        agent = ResumeModifierAgent()
        
        # Process the job description and modify the resume
        result = await agent.modify_resume(
            job_description=request.job_description,
            company_name=request.company_name,
            position_title=request.position_title,
            requirements=request.requirements,
            session_id=session_id
        )
        
        # Create a sanitized filename for the PDF
        company_safe = "".join(c for c in request.company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        position_safe = "".join(c for c in request.position_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"modified_resume_{company_safe}_{position_safe}_{session_id[:8]}.pdf"
        
        # Only return PDF files, prioritizing RenderCV
        if result.get("pdf_file_rendercv") and os.path.exists(result["pdf_file_rendercv"]):
            logger.info(f"Returning RenderCV PDF: {result['pdf_file_rendercv']}")
            return FileResponse(
                path=result["pdf_file_rendercv"],
                media_type='application/pdf',
                filename=filename,
                headers={
                    "X-Session-ID": session_id,
                    "X-Company": request.company_name,
                    "X-Position": request.position_title,
                    "X-PDF-Source": "RenderCV"
                }
            )
        elif result.get("pdf_file_latex") and os.path.exists(result["pdf_file_latex"]):
            logger.info(f"Returning LaTeX PDF: {result['pdf_file_latex']}")
            return FileResponse(
                path=result["pdf_file_latex"],
                media_type='application/pdf',
                filename=filename,
                headers={
                    "X-Session-ID": session_id,
                    "X-Company": request.company_name,
                    "X-Position": request.position_title,
                    "X-PDF-Source": "LaTeX"
                }
            )
        else:
            logger.error("PDF generation failed for both RenderCV and LaTeX")
            raise HTTPException(
                status_code=500,
                detail="PDF generation failed. Please try again or check the logs for more details."
            )
        
    except Exception as e:
        logger.error(f"Error modifying resume for PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to modify resume and generate PDF: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """
    Get modification history for a session
    """
    try:
        agent = ResumeModifierAgent()
        history = await agent.get_session_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session history: {str(e)}"
        ) 