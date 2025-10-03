from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# User Management Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


# Resume Models
class ResumeMetadata(BaseModel):
    original_filename: str
    file_size: int
    upload_date: datetime
    file_type: str
    parsed_sections: Optional[List[str]] = None


class MasterResume(BaseModel):
    id: str
    user_id: str
    structured_data: Dict[str, Any]
    metadata: ResumeMetadata
    created_at: datetime
    updated_at: datetime


# Job Description Models
class JobAnalysisRequest(BaseModel):
    job_description: str
    company_name: str
    job_title: str
    job_url: Optional[str] = None


class JobAnalysisResponse(BaseModel):
    keywords: List[str]
    required_skills: List[str]
    experience_level: str
    industry_focus: str
    extracted_requirements: Dict[str, Any]
    analysis_metadata: Dict[str, Any]


# Resume Modification Models
class ToneType(str, Enum):
    technical = "technical"
    creative = "creative"
    corporate = "corporate"
    professional = "professional"


class ResumeCustomizations(BaseModel):
    emphasize_skills: Optional[List[str]] = None
    include_sections: Optional[List[str]] = None
    tone: Optional[ToneType] = ToneType.professional


class ResumeModificationRequest(BaseModel):
    job_description: str
    job_title: str
    company_name: str
    customizations: Optional[ResumeCustomizations] = None


class ResumeModificationPreview(BaseModel):
    proposed_changes: Dict[str, Any]
    sections_to_modify: List[str]
    skills_to_emphasize: List[str]
    estimated_match_score: float
    preview_metadata: Dict[str, Any]


class GeneratedResume(BaseModel):
    id: str
    user_id: str
    job_title: str
    company_name: str
    file_path: str
    file_url: str
    created_at: datetime
    modification_metadata: Dict[str, Any]
    match_score: Optional[float] = None


# Template Models
class TemplateType(str, Enum):
    modern = "modern"
    classic = "classic"
    creative = "creative"
    minimal = "minimal"
    professional = "professional"


class ResumeTemplate(BaseModel):
    id: str
    name: str
    type: TemplateType
    preview_url: Optional[str] = None
    description: str
    is_custom: bool = False


# User Preferences Models
class UserPreferences(BaseModel):
    default_template: str = "modern"
    always_include_sections: List[str] = ["education", "experience"]
    default_tone: ToneType = ToneType.professional
    color_scheme: str = "blue"


# Analytics Models
class ResumeFeedback(BaseModel):
    resume_id: str
    got_interview: bool
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class KeywordAnalytics(BaseModel):
    trending_keywords: List[str]
    skill_demand: Dict[str, int]
    industry_keywords: Dict[str, List[str]]
    analysis_period: str


class SuccessMetrics(BaseModel):
    total_resumes_generated: int
    interview_rate: float
    top_performing_modifications: List[str]
    success_by_industry: Dict[str, float]
    suggestions: List[str]


# Chrome Extension Models
class QuickSettings(BaseModel):
    format: str = "pdf"
    template: str = "default"


class ExtensionQuickModifyRequest(BaseModel):
    selected_text: str
    page_url: str
    quick_settings: Optional[QuickSettings] = None


class ExtensionStatus(BaseModel):
    is_authenticated: bool
    has_master_resume: bool
    remaining_quota: int
    extension_version: str


# File Management Models
class TempFileUpload(BaseModel):
    file_id: str
    original_filename: str
    upload_url: str
    expires_at: datetime


class FileDownload(BaseModel):
    file_id: str
    download_url: str
    filename: str
    expires_at: datetime


# Health and Utility Models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    service_status: Dict[str, str]


class ParsedResumeData(BaseModel):
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    additional_sections: Optional[Dict[str, Any]] = None


# Error Models
class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Pagination Models
class PaginationParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


# Resume History Models
class ResumeHistoryFilter(BaseModel):
    company: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    

class ResumeHistoryResponse(PaginatedResponse):
    items: List[GeneratedResume]


# Rate Limiting Models
class RateLimitInfo(BaseModel):
    requests_remaining: int
    reset_time: datetime
    quota_type: str 