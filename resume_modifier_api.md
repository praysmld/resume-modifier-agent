# Resume Modifier Chrome Extension - REST API Design

## Core Endpoints

### 1. User Management

#### `POST /api/users/register`
**Purpose**: Register a new user account
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```
**Response**: User ID, authentication token

#### `POST /api/users/login`
**Purpose**: Authenticate user and get access token
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```
**Response**: Authentication token, user profile

#### `GET /api/users/profile`
**Purpose**: Get user profile information
**Headers**: `Authorization: Bearer <token>`
**Response**: User details, account settings

### 2. Master Resume Management

#### `POST /api/resumes/upload`
**Purpose**: Upload and store user's comprehensive master resume
**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `multipart/form-data`
```
- file: PDF/DOCX file
- metadata: JSON with additional info
```
**Explanation**: This is crucial as it stores the complete CV that will be used as the source for all modifications.

#### `GET /api/resumes/master`
**Purpose**: Retrieve the user's master resume
**Headers**: `Authorization: Bearer <token>`
**Response**: Master resume data in structured format (JSON) plus original file

#### `PUT /api/resumes/master`
**Purpose**: Update the master resume
**Headers**: `Authorization: Bearer <token>`
**Body**: Updated resume data or new file upload

#### `DELETE /api/resumes/master`
**Purpose**: Delete the master resume
**Headers**: `Authorization: Bearer <token>`

### 3. Job Description Processing

#### `POST /api/jobs/analyze`
**Purpose**: Analyze job description and extract key requirements
**Headers**: `Authorization: Bearer <token>`
```json
{
  "job_description": "Full job description text",
  "company_name": "Company ABC",
  "job_title": "Software Engineer",
  "job_url": "https://example.com/job"
}
```
**Response**: Extracted keywords, required skills, experience level, industry focus
**Explanation**: This endpoint processes the job description to identify what modifications are needed.

### 4. Resume Modification (Core Feature)

#### `POST /api/modify-resume`
**Purpose**: Generate tailored resume based on job description
**Headers**: `Authorization: Bearer <token>`
```json
{
  "job_description": "Full job description text",
  "job_title": "Software Engineer",
  "company_name": "Company ABC",
  "customizations": {
    "emphasize_skills": ["Python", "React"],
    "include_sections": ["projects", "certifications"],
    "tone": "technical|creative|corporate"
  }
}
```
**Response**: Generated PDF file + metadata about modifications made

#### `POST /api/modify-resume/preview`
**Purpose**: Preview modifications without generating final PDF
**Headers**: `Authorization: Bearer <token>`
**Body**: Same as above
**Response**: JSON showing what changes would be made
**Explanation**: Allows users to see modifications before generating the final document.

### 5. Resume History & Management

#### `GET /api/resumes/generated`
**Purpose**: Get list of all previously generated resumes
**Headers**: `Authorization: Bearer <token>`
**Query Params**: `?limit=10&offset=0&company=CompanyName`
**Response**: List of generated resumes with metadata

#### `GET /api/resumes/generated/{resume_id}`
**Purpose**: Download a specific generated resume
**Headers**: `Authorization: Bearer <token>`
**Response**: PDF file

#### `DELETE /api/resumes/generated/{resume_id}`
**Purpose**: Delete a generated resume
**Headers**: `Authorization: Bearer <token>`

#### `POST /api/resumes/generated/{resume_id}/regenerate`
**Purpose**: Regenerate a resume with updated master CV or different settings
**Headers**: `Authorization: Bearer <token>`

### 6. Templates & Customization

#### `GET /api/templates`
**Purpose**: Get available resume templates
**Response**: List of available templates with previews

#### `POST /api/templates/custom`
**Purpose**: Create or upload custom template
**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `multipart/form-data`

#### `GET /api/user-preferences`
**Purpose**: Get user's default preferences for resume generation
**Headers**: `Authorization: Bearer <token>`

#### `PUT /api/user-preferences`
**Purpose**: Update user's default preferences
**Headers**: `Authorization: Bearer <token>`
```json
{
  "default_template": "modern",
  "always_include_sections": ["education", "experience"],
  "default_tone": "professional",
  "color_scheme": "blue"
}
```

### 7. Analytics & Insights

#### `GET /api/analytics/keywords`
**Purpose**: Get trending keywords from recent job applications
**Headers**: `Authorization: Bearer <token>`
**Response**: Most common keywords, skills in demand

#### `GET /api/analytics/success-rate`
**Purpose**: Track which modifications lead to better results
**Headers**: `Authorization: Bearer <token>`
**Response**: Success metrics, suggested improvements

#### `POST /api/analytics/feedback`
**Purpose**: Record user feedback on generated resumes
**Headers**: `Authorization: Bearer <token>`
```json
{
  "resume_id": "generated_resume_123",
  "got_interview": true,
  "rating": 5,
  "feedback": "Great customization"
}
```

### 8. Chrome Extension Support

#### `POST /api/extension/quick-modify`
**Purpose**: Streamlined endpoint for Chrome extension direct usage
**Headers**: `Authorization: Bearer <token>`, `X-Extension-Version: 1.0`
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
**Response**: Direct PDF download link
**Explanation**: Optimized for the extension's right-click functionality.

#### `GET /api/extension/status`
**Purpose**: Check if user is logged in and has master resume uploaded
**Headers**: `Authorization: Bearer <token>`
**Response**: Extension readiness status

### 9. File Management

#### `POST /api/files/temp-upload`
**Purpose**: Temporary file upload for processing
**Content-Type**: `multipart/form-data`
**Response**: Temporary file ID

#### `GET /api/files/download/{file_id}`
**Purpose**: Download generated files
**Headers**: `Authorization: Bearer <token>`

### 10. Health & Utilities

#### `GET /api/health`
**Purpose**: API health check
**Response**: Service status

#### `POST /api/parse-resume`
**Purpose**: Parse uploaded resume into structured data
**Content-Type**: `multipart/form-data`
**Response**: Structured resume data in JSON format

## Additional Considerations

### Rate Limiting
- `/modify-resume`: 10 requests per hour per user
- `/quick-modify`: 20 requests per hour per user
- Other endpoints: 100 requests per hour per user

### Authentication
- JWT tokens with 24-hour expiry
- Refresh token mechanism for seamless extension usage

### File Storage
- Master resumes stored permanently
- Generated resumes cached for 30 days
- Temporary files cleaned after 24 hours

### Error Handling
- Consistent error response format
- Specific error codes for extension handling
- Graceful degradation for processing failures