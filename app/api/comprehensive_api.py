import logging
import asyncio
import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Header, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer

from app.models.schemas import (
    UserRegistration, UserLogin, UserProfile, AuthToken,
    JobAnalysisRequest, JobAnalysisResponse,
    ResumeModificationRequest, ResumeModificationPreview,
    ResumeCustomizations, GeneratedResume,
    ResumeTemplate, UserPreferences,
    ResumeFeedback, KeywordAnalytics, SuccessMetrics,
    ExtensionQuickModifyRequest, ExtensionStatus, QuickSettings,
    TempFileUpload, FileDownload,
    HealthResponse, ParsedResumeData,
    PaginationParams, ResumeHistoryResponse, ResumeHistoryFilter,
    RateLimitInfo, APIError, MasterResume, ResumeMetadata
)
from app.auth.dependencies import get_current_user_id, get_optional_user_id, verify_extension_version
from app.services.user_service import UserService
from app.agents.graph import ResumeModifierAgent
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for demo (replace with database)
master_resumes_db: Dict[str, Dict[str, Any]] = {}
generated_resumes_db: Dict[str, Dict[str, Any]] = {}
user_preferences_db: Dict[str, Dict[str, Any]] = {}
analytics_db: Dict[str, Any] = {"feedback": [], "keywords": {}, "success_metrics": {}}
temp_files_db: Dict[str, Dict[str, Any]] = {}
rate_limits_db: Dict[str, Dict[str, Any]] = {}

# Available templates
AVAILABLE_TEMPLATES = [
    {"id": "modern", "name": "Modern", "type": "modern", "description": "Clean and contemporary design"},
    {"id": "classic", "name": "Classic", "type": "classic", "description": "Traditional professional layout"},
    {"id": "creative", "name": "Creative", "type": "creative", "description": "Innovative and artistic design"},
    {"id": "minimal", "name": "Minimal", "type": "minimal", "description": "Simple and clean layout"},
]


# Rate limiting decorator
def check_rate_limit(endpoint: str, limit: int):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or args[0] if args else None
            if user_id:
                key = f"{user_id}:{endpoint}"
                now = datetime.utcnow()
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                
                if key not in rate_limits_db:
                    rate_limits_db[key] = {"count": 0, "reset_time": hour_start + timedelta(hours=1)}
                
                rate_data = rate_limits_db[key]
                if now >= rate_data["reset_time"]:
                    rate_data["count"] = 0
                    rate_data["reset_time"] = hour_start + timedelta(hours=1)
                
                if rate_data["count"] >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
                
                rate_data["count"] += 1
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 1. User Management Endpoints
@router.post("/users/register", response_model=AuthToken)
async def register_user(user_data: UserRegistration):
    """Register a new user account"""
    return await UserService.register_user(user_data)


@router.post("/users/login", response_model=AuthToken)
async def login_user(login_data: UserLogin):
    """Authenticate user and get access token"""
    return await UserService.login_user(login_data)


@router.get("/users/profile", response_model=UserProfile)
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """Get user profile information"""
    return await UserService.get_user_profile(user_id)


# 2. Master Resume Management
@router.post("/resumes/upload")
async def upload_master_resume(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id)
):
    """Upload and store user's comprehensive master resume"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and DOCX files are allowed"
            )
        
        # Create unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"master_resume_{user_id}_{uuid.uuid4()}{file_extension}"
        file_path = Path(settings.output_directory) / unique_filename
        
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create resume record
        resume_id = str(uuid.uuid4())
        resume_metadata = ResumeMetadata(
            original_filename=file.filename,
            file_size=len(content),
            upload_date=datetime.utcnow(),
            file_type=file.content_type,
            parsed_sections=["experience", "education", "skills"]  # Mock data
        )
        
        # Parse resume (simplified)
        structured_data = {
            "personal_info": {"name": "User Name", "email": "user@example.com"},
            "experience": [],
            "education": [],
            "skills": []
        }
        
        master_resume = {
            "id": resume_id,
            "user_id": user_id,
            "file_path": str(file_path),
            "structured_data": structured_data,
            "metadata": resume_metadata.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        master_resumes_db[user_id] = master_resume
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume_id,
            "filename": unique_filename
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {str(e)}"
        )


@router.get("/resumes/master", response_model=MasterResume)
async def get_master_resume(user_id: str = Depends(get_current_user_id)):
    """Retrieve the user's master resume"""
    if user_id not in master_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master resume not found"
        )
    
    resume_data = master_resumes_db[user_id]
    return MasterResume(**resume_data)


@router.put("/resumes/master")
async def update_master_resume(
    file: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id)
):
    """Update the master resume"""
    if user_id not in master_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master resume not found"
        )
    
    if file:
        # Upload new file (similar to upload endpoint)
        return await upload_master_resume(file, metadata, user_id)
    
    # Update metadata only
    resume_data = master_resumes_db[user_id]
    resume_data["updated_at"] = datetime.utcnow()
    
    return {"message": "Master resume updated successfully"}


@router.delete("/resumes/master")
async def delete_master_resume(user_id: str = Depends(get_current_user_id)):
    """Delete the master resume"""
    if user_id not in master_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master resume not found"
        )
    
    # Delete file
    resume_data = master_resumes_db[user_id]
    file_path = Path(resume_data["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Remove from database
    del master_resumes_db[user_id]
    
    return {"message": "Master resume deleted successfully"}


# 3. Job Description Processing
@router.post("/jobs/analyze", response_model=JobAnalysisResponse)
async def analyze_job_description(
    request: JobAnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Analyze job description and extract key requirements"""
    try:
        # Mock analysis (replace with actual LLM analysis)
        keywords = ["Python", "FastAPI", "React", "Machine Learning", "API", "Database"]
        required_skills = ["Python", "Web Development", "Problem Solving"]
        
        return JobAnalysisResponse(
            keywords=keywords,
            required_skills=required_skills,
            experience_level="Mid-Senior",
            industry_focus="Technology",
            extracted_requirements={
                "technical_skills": required_skills,
                "soft_skills": ["Communication", "Team Work"],
                "years_experience": "3-5"
            },
            analysis_metadata={
                "confidence_score": 0.85,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze job description: {str(e)}"
        )


# 4. Resume Modification (Core Feature)
@router.post("/modify-resume")
@check_rate_limit("modify-resume", 10)
async def modify_resume(
    request: ResumeModificationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate tailored resume based on job description"""
    try:
        # Check if user has master resume
        if user_id not in master_resumes_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a master resume first"
            )
        
        # Use existing resume modification logic
        session_id = str(uuid.uuid4())
        agent = ResumeModifierAgent()
        
        result = await agent.modify_resume(
            job_description=request.job_description,
            company_name=request.company_name,
            position_title=request.job_title,
            session_id=session_id
        )
        
        # Store generated resume record
        resume_id = str(uuid.uuid4())
        generated_resume = {
            "id": resume_id,
            "user_id": user_id,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "file_path": result.get("pdf_file_rendercv") or result.get("pdf_file_latex"),
            "file_url": f"/api/files/download/{resume_id}",
            "created_at": datetime.utcnow(),
            "modification_metadata": {
                "session_id": session_id,
                "customizations": request.customizations.dict() if request.customizations else {},
                "source": "RenderCV" if result.get("pdf_file_rendercv") else "LaTeX"
            },
            "match_score": 0.85  # Mock score
        }
        
        generated_resumes_db[resume_id] = generated_resume
        
        # Return file
        if result.get("pdf_file_rendercv") and os.path.exists(result["pdf_file_rendercv"]):
            return FileResponse(
                path=result["pdf_file_rendercv"],
                media_type='application/pdf',
                filename=f"modified_resume_{request.company_name}_{request.job_title}.pdf",
                headers={"X-Resume-ID": resume_id}
            )
        elif result.get("pdf_file_latex") and os.path.exists(result["pdf_file_latex"]):
            return FileResponse(
                path=result["pdf_file_latex"],
                media_type='application/pdf',
                filename=f"modified_resume_{request.company_name}_{request.job_title}.pdf",
                headers={"X-Resume-ID": resume_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate resume"
            )
            
    except Exception as e:
        logger.error(f"Error modifying resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify resume: {str(e)}"
        )


@router.post("/modify-resume/preview", response_model=ResumeModificationPreview)
async def preview_resume_modifications(
    request: ResumeModificationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Preview modifications without generating final PDF"""
    try:
        if user_id not in master_resumes_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a master resume first"
            )
        
        # Mock preview (replace with actual analysis)
        preview = ResumeModificationPreview(
            proposed_changes={
                "summary": "Updated to highlight relevant experience",
                "skills": "Emphasized Python and FastAPI",
                "experience": "Reordered to show most relevant first"
            },
            sections_to_modify=["summary", "skills", "experience"],
            skills_to_emphasize=request.customizations.emphasize_skills if request.customizations else [],
            estimated_match_score=0.85,
            preview_metadata={
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.9
            }
        )
        
        return preview
        
    except Exception as e:
        logger.error(f"Error previewing modifications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview modifications: {str(e)}"
        )


# 5. Resume History & Management
@router.get("/resumes/generated", response_model=ResumeHistoryResponse)
async def get_generated_resumes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    company: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """Get list of all previously generated resumes"""
    user_resumes = [
        resume for resume in generated_resumes_db.values()
        if resume["user_id"] == user_id
    ]
    
    # Filter by company if specified
    if company:
        user_resumes = [
            resume for resume in user_resumes
            if company.lower() in resume["company_name"].lower()
        ]
    
    # Sort by creation date (newest first)
    user_resumes.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Paginate
    total = len(user_resumes)
    paginated_resumes = user_resumes[offset:offset + limit]
    
    # Convert to response models
    resume_models = [GeneratedResume(**resume) for resume in paginated_resumes]
    
    return ResumeHistoryResponse(
        items=resume_models,
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + limit < total,
        has_previous=offset > 0
    )


@router.get("/resumes/generated/{resume_id}")
async def download_generated_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Download a specific generated resume"""
    if resume_id not in generated_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    resume = generated_resumes_db[resume_id]
    if resume["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    file_path = resume["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=f"resume_{resume['company_name']}_{resume['job_title']}.pdf"
    )


@router.delete("/resumes/generated/{resume_id}")
async def delete_generated_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a generated resume"""
    if resume_id not in generated_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    resume = generated_resumes_db[resume_id]
    if resume["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete file
    file_path = resume["file_path"]
    if os.path.exists(file_path):
        os.unlink(file_path)
    
    # Remove from database
    del generated_resumes_db[resume_id]
    
    return {"message": "Resume deleted successfully"}


# 6. Templates & Customization
@router.get("/templates")
async def get_templates():
    """Get available resume templates"""
    return {"templates": AVAILABLE_TEMPLATES}


@router.get("/user-preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: str = Depends(get_current_user_id)):
    """Get user's default preferences for resume generation"""
    if user_id not in user_preferences_db:
        # Return default preferences
        return UserPreferences()
    
    return UserPreferences(**user_preferences_db[user_id])


@router.put("/user-preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    user_id: str = Depends(get_current_user_id)
):
    """Update user's default preferences"""
    user_preferences_db[user_id] = preferences.dict()
    return preferences


# 7. Analytics & Insights
@router.get("/analytics/keywords", response_model=KeywordAnalytics)
async def get_keyword_analytics(user_id: str = Depends(get_current_user_id)):
    """Get trending keywords from recent job applications"""
    # Mock data
    return KeywordAnalytics(
        trending_keywords=["Python", "FastAPI", "React", "Machine Learning"],
        skill_demand={"Python": 150, "React": 120, "FastAPI": 80},
        industry_keywords={
            "Technology": ["Python", "JavaScript", "API"],
            "Finance": ["SQL", "Excel", "Analysis"]
        },
        analysis_period="Last 30 days"
    )


@router.get("/analytics/success-rate", response_model=SuccessMetrics)
async def get_success_metrics(user_id: str = Depends(get_current_user_id)):
    """Track which modifications lead to better results"""
    # Mock data
    return SuccessMetrics(
        total_resumes_generated=25,
        interview_rate=0.32,
        top_performing_modifications=["Skills emphasis", "Experience reordering"],
        success_by_industry={"Technology": 0.35, "Finance": 0.28},
        suggestions=[
            "Add more technical skills",
            "Include quantified achievements"
        ]
    )


@router.post("/analytics/feedback")
async def submit_feedback(
    feedback: ResumeFeedback,
    user_id: str = Depends(get_current_user_id)
):
    """Record user feedback on generated resumes"""
    # Verify resume belongs to user
    if feedback.resume_id not in generated_resumes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    resume = generated_resumes_db[feedback.resume_id]
    if resume["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Store feedback
    feedback_record = feedback.dict()
    feedback_record["user_id"] = user_id
    feedback_record["submitted_at"] = datetime.utcnow()
    
    analytics_db["feedback"].append(feedback_record)
    
    return {"message": "Feedback submitted successfully"}


# 8. Chrome Extension Support
@router.post("/extension/quick-modify")
@check_rate_limit("quick-modify", 20)
async def extension_quick_modify(
    request: ExtensionQuickModifyRequest,
    user_id: str = Depends(get_current_user_id),
    extension_version: str = Depends(verify_extension_version)
):
    """Streamlined endpoint for Chrome extension direct usage"""
    try:
        if user_id not in master_resumes_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a master resume first"
            )
        
        # Extract company name and job title from URL or text
        company_name = request.page_url.split("//")[1].split(".")[0] if "//" in request.page_url else "Unknown Company"
        job_title = "Unknown Position"  # Could be extracted from selected text
        
        # Create modification request
        modification_request = ResumeModificationRequest(
            job_description=request.selected_text,
            job_title=job_title,
            company_name=company_name,
            customizations=ResumeCustomizations()
        )
        
        # Use existing modification logic
        return await modify_resume(modification_request, user_id)
        
    except Exception as e:
        logger.error(f"Error in extension quick modify: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify resume: {str(e)}"
        )


@router.get("/extension/status", response_model=ExtensionStatus)
async def get_extension_status(
    user_id: str = Depends(get_current_user_id),
    extension_version: str = Depends(verify_extension_version)
):
    """Check if user is logged in and has master resume uploaded"""
    has_master_resume = user_id in master_resumes_db
    
    # Calculate remaining quota
    key = f"{user_id}:quick-modify"
    remaining_quota = 20  # Default
    if key in rate_limits_db:
        remaining_quota = max(0, 20 - rate_limits_db[key]["count"])
    
    return ExtensionStatus(
        is_authenticated=True,
        has_master_resume=has_master_resume,
        remaining_quota=remaining_quota,
        extension_version=extension_version
    )


# 9. File Management
@router.post("/files/temp-upload", response_model=TempFileUpload)
async def temp_file_upload(file: UploadFile = File(...)):
    """Temporary file upload for processing"""
    try:
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        temp_filename = f"temp_{file_id}{file_extension}"
        temp_path = Path(settings.output_directory) / "temp" / temp_filename
        
        # Ensure directory exists
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Store temp file record
        expires_at = datetime.utcnow() + timedelta(hours=24)
        temp_files_db[file_id] = {
            "file_path": str(temp_path),
            "original_filename": file.filename,
            "expires_at": expires_at
        }
        
        return TempFileUpload(
            file_id=file_id,
            original_filename=file.filename,
            upload_url=f"/api/files/download/{file_id}",
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Error uploading temp file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/files/download/{file_id}")
async def download_file(
    file_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Download generated files"""
    # Check temp files first
    if file_id in temp_files_db:
        temp_file = temp_files_db[file_id]
        if datetime.utcnow() > temp_file["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File expired"
            )
        
        return FileResponse(
            path=temp_file["file_path"],
            filename=temp_file["original_filename"]
        )
    
    # Check generated resumes
    if file_id in generated_resumes_db:
        resume = generated_resumes_db[file_id]
        if user_id and resume["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return FileResponse(
            path=resume["file_path"],
            filename=f"resume_{resume['company_name']}_{resume['job_title']}.pdf"
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="File not found"
    )


# 10. Health & Utilities
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """API health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        service_status={
            "database": "connected",
            "llm_service": "available",
            "file_storage": "available"
        }
    )


@router.post("/parse-resume", response_model=ParsedResumeData)
async def parse_resume(file: UploadFile = File(...)):
    """Parse uploaded resume into structured data"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and DOCX files are allowed"
            )
        
        # Mock parsing (replace with actual parsing logic)
        parsed_data = ParsedResumeData(
            personal_info={
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-0123",
                "location": "New York, NY"
            },
            experience=[
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2021-2023",
                    "description": "Developed web applications using Python and React"
                }
            ],
            education=[
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of Technology",
                    "year": "2021"
                }
            ],
            skills=["Python", "JavaScript", "React", "FastAPI", "SQL"],
            projects=[
                {
                    "name": "Resume Modifier",
                    "description": "AI-powered resume customization tool",
                    "technologies": ["Python", "FastAPI", "React"]
                }
            ]
        )
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}"
        ) 