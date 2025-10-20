# Resume Modifier API Documentation

## Overview

The Resume Modifier API is a comprehensive REST API that provides intelligent resume customization capabilities. It allows users to upload their master resume and automatically generate tailored versions based on specific job descriptions. The API is designed to support a Chrome extension for seamless job application workflows.

## Base URL

```
http://localhost:8000/api
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Quick Start

1. **Register a new account**:
   ```bash
   curl -X POST "http://localhost:8000/api/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "securepassword123",
       "full_name": "John Doe"
     }'
   ```

2. **Upload your master resume**:
   ```bash
   curl -X POST "http://localhost:8000/api/resumes/upload" \
     -H "Authorization: Bearer <your_token>" \
     -F "file=@your_resume.pdf"
   ```

3. **Generate a tailored resume**:
   ```bash
   curl -X POST "http://localhost:8000/api/modify-resume" \
     -H "Authorization: Bearer <your_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "We are looking for a Python developer...",
       "job_title": "Senior Python Developer",
       "company_name": "Tech Corp"
     }' \
     --output modified_resume.pdf
   ```

## API Endpoints

### 1. User Management

#### `POST /users/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
}
```

#### `POST /users/login`
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as registration response.

#### `GET /users/profile`
Get user profile information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "is_active": true
}
```

### 2. Master Resume Management

#### `POST /resumes/upload`
Upload and store user's comprehensive master resume.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file`: PDF or DOCX file
- `metadata`: JSON string (optional)

**Response:**
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": "resume-uuid",
  "filename": "master_resume_user-id_unique-id.pdf"
}
```

#### `GET /resumes/master`
Retrieve the user's master resume data.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "resume-uuid",
  "user_id": "user-uuid",
  "structured_data": {
    "personal_info": {...},
    "experience": [...],
    "education": [...],
    "skills": [...]
  },
  "metadata": {
    "original_filename": "resume.pdf",
    "file_size": 1048576,
    "upload_date": "2024-01-01T00:00:00Z",
    "file_type": "application/pdf"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### `PUT /resumes/master`
Update the master resume.

**Headers:** `Authorization: Bearer <token>`

#### `DELETE /resumes/master`
Delete the master resume.

**Headers:** `Authorization: Bearer <token>`

### 3. Job Description Processing

#### `POST /jobs/analyze`
Analyze job description and extract key requirements.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "job_description": "We are seeking a Python developer with experience in FastAPI...",
  "company_name": "Tech Corp",
  "job_title": "Senior Python Developer",
  "job_url": "https://company.com/jobs/123"
}
```

**Response:**
```json
{
  "keywords": ["Python", "FastAPI", "React", "Machine Learning"],
  "required_skills": ["Python", "Web Development", "Problem Solving"],
  "experience_level": "Mid-Senior",
  "industry_focus": "Technology",
  "extracted_requirements": {
    "technical_skills": ["Python", "FastAPI"],
    "soft_skills": ["Communication", "Team Work"],
    "years_experience": "3-5"
  },
  "analysis_metadata": {
    "confidence_score": 0.85,
    "analysis_timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 4. Resume Modification (Core Feature)

#### `POST /modify-resume`
Generate tailored resume based on job description.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "job_description": "We are seeking a Python developer...",
  "job_title": "Senior Python Developer",
  "company_name": "Tech Corp",
  "customizations": {
    "emphasize_skills": ["Python", "React"],
    "include_sections": ["projects", "certifications"],
    "tone": "technical"
  }
}
```

**Response:** PDF file download

**Rate Limit:** 10 requests per hour per user

#### `POST /modify-resume/preview`
Preview modifications without generating final PDF.

**Headers:** `Authorization: Bearer <token>`

**Request Body:** Same as `/modify-resume`

**Response:**
```json
{
  "proposed_changes": {
    "summary": "Updated to highlight relevant experience",
    "skills": "Emphasized Python and FastAPI",
    "experience": "Reordered to show most relevant first"
  },
  "sections_to_modify": ["summary", "skills", "experience"],
  "skills_to_emphasize": ["Python", "React"],
  "estimated_match_score": 0.85,
  "preview_metadata": {
    "analysis_timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.9
  }
}
```

### 5. Resume History & Management

#### `GET /resumes/generated`
Get list of all previously generated resumes.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit`: Number of results (1-100, default: 10)
- `offset`: Pagination offset (default: 0)
- `company`: Filter by company name (optional)

**Response:**
```json
{
  "items": [
    {
      "id": "resume-uuid",
      "user_id": "user-uuid",
      "job_title": "Senior Python Developer",
      "company_name": "Tech Corp",
      "file_path": "/path/to/file.pdf",
      "file_url": "/api/files/download/resume-uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "modification_metadata": {...},
      "match_score": 0.85
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0,
  "has_next": true,
  "has_previous": false
}
```

#### `GET /resumes/generated/{resume_id}`
Download a specific generated resume.

**Headers:** `Authorization: Bearer <token>`

**Response:** PDF file download

#### `DELETE /resumes/generated/{resume_id}`
Delete a generated resume.

**Headers:** `Authorization: Bearer <token>`

### 6. Templates & Customization

#### `GET /templates`
Get available resume templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "modern",
      "name": "Modern",
      "type": "modern",
      "description": "Clean and contemporary design"
    }
  ]
}
```

#### `GET /user-preferences`
Get user's default preferences.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "default_template": "modern",
  "always_include_sections": ["education", "experience"],
  "default_tone": "professional",
  "color_scheme": "blue"
}
```

#### `PUT /user-preferences`
Update user's default preferences.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "default_template": "modern",
  "always_include_sections": ["education", "experience"],
  "default_tone": "professional",
  "color_scheme": "blue"
}
```

### 7. Analytics & Insights

#### `GET /analytics/keywords`
Get trending keywords from recent job applications.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "trending_keywords": ["Python", "FastAPI", "React", "Machine Learning"],
  "skill_demand": {"Python": 150, "React": 120, "FastAPI": 80},
  "industry_keywords": {
    "Technology": ["Python", "JavaScript", "API"],
    "Finance": ["SQL", "Excel", "Analysis"]
  },
  "analysis_period": "Last 30 days"
}
```

#### `GET /analytics/success-rate`
Track which modifications lead to better results.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_resumes_generated": 25,
  "interview_rate": 0.32,
  "top_performing_modifications": ["Skills emphasis", "Experience reordering"],
  "success_by_industry": {"Technology": 0.35, "Finance": 0.28},
  "suggestions": [
    "Add more technical skills",
    "Include quantified achievements"
  ]
}
```

#### `POST /analytics/feedback`
Record user feedback on generated resumes.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "resume_id": "resume-uuid",
  "got_interview": true,
  "rating": 5,
  "feedback": "Great customization"
}
```

### 8. Chrome Extension Support

#### `POST /extension/quick-modify`
Streamlined endpoint for Chrome extension direct usage.

**Headers:** 
- `Authorization: Bearer <token>`
- `X-Extension-Version: 1.0`

**Request Body:**
```json
{
  "selected_text": "Job description text from webpage",
  "page_url": "https://jobsite.com/job/123",
  "quick_settings": {
    "format": "pdf",
    "template": "default"
  }
}
```

**Response:** PDF file download

**Rate Limit:** 20 requests per hour per user

#### `GET /extension/status`
Check if user is logged in and has master resume uploaded.

**Headers:** 
- `Authorization: Bearer <token>`
- `X-Extension-Version: 1.0`

**Response:**
```json
{
  "is_authenticated": true,
  "has_master_resume": true,
  "remaining_quota": 15,
  "extension_version": "1.0"
}
```

### 9. File Management

#### `POST /files/temp-upload`
Temporary file upload for processing.

**Form Data:**
- `file`: File to upload

**Response:**
```json
{
  "file_id": "temp-file-uuid",
  "original_filename": "document.pdf",
  "upload_url": "/api/files/download/temp-file-uuid",
  "expires_at": "2024-01-02T00:00:00Z"
}
```

#### `GET /files/download/{file_id}`
Download generated files.

**Headers:** `Authorization: Bearer <token>` (optional for temp files)

**Response:** File download

### 10. Health & Utilities

#### `GET /health`
API health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "service_status": {
    "database": "connected",
    "llm_service": "available",
    "file_storage": "available"
  }
}
```

#### `POST /parse-resume`
Parse uploaded resume into structured data.

**Form Data:**
- `file`: PDF or DOCX file

**Response:**
```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "location": "New York, NY"
  },
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Tech Corp",
      "duration": "2021-2023",
      "description": "Developed web applications using Python and React"
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University of Technology",
      "year": "2021"
    }
  ],
  "skills": ["Python", "JavaScript", "React", "FastAPI", "SQL"],
  "projects": [
    {
      "name": "Resume Modifier",
      "description": "AI-powered resume customization tool",
      "technologies": ["Python", "FastAPI", "React"]
    }
  ]
}
```

## Rate Limiting

Different endpoints have different rate limits per user per hour:

- `/modify-resume`: 10 requests per hour
- `/extension/quick-modify`: 20 requests per hour
- Other endpoints: 100 requests per hour

When rate limit is exceeded, the API returns HTTP 429 with rate limit information.

## Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## File Storage

- Master resumes are stored permanently
- Generated resumes are cached for 30 days
- Temporary files are cleaned after 24 hours

## Security

- JWT tokens with 24-hour expiry
- Password hashing using bcrypt
- CORS middleware configured
- Rate limiting implemented
- File type validation

## Environment Variables

Required environment variables (see `env_example.txt`):

```bash
# Security
SECRET_KEY=your-very-long-secret-key-for-jwt-tokens

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here

# Optional configurations
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

## Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp env_example.txt .env
   # Edit .env with your values
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Access the API documentation**:
   ```
   http://localhost:8000/docs
   ```

## Chrome Extension Integration

The API is specifically designed to support a Chrome extension with:

- Quick modify endpoint for one-click resume generation
- Extension status endpoint for checking readiness
- Streamlined authentication flow
- Rate limiting optimized for extension usage patterns

## Future Enhancements

- Database integration (currently using in-memory storage)
- Redis caching for improved performance
- Advanced resume parsing with AI
- Multiple resume template support
- Webhook notifications
- Batch processing capabilities 