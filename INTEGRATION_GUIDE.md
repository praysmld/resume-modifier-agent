# Integration Guide: Adding RenderCV to Your FastAPI Application

This guide shows how to integrate the new RenderCV endpoints with your existing FastAPI application.

## 1. Update your main.py file

Add the RenderCV router to your existing FastAPI application:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your existing endpoints
from app.api.endpoints import router  # Your existing router
from app.api.rendercv_endpoints import router as rendercv_router  # New RenderCV router

app = FastAPI(
    title="Resume Modifier Agent with RenderCV",
    description="AI-powered resume modification with professional PDF generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)  # Your existing endpoints
app.include_router(rendercv_router)  # New RenderCV endpoints

@app.get("/")
async def root():
    return {
        "message": "Resume Modifier Agent with RenderCV",
        "endpoints": {
            "existing": "/docs",
            "rendercv_health": "/rendercv/health",
            "modify_with_rendercv": "/rendercv/modify-resume"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 2. Update your requirements.txt

Ensure you have the RenderCV dependency:

```txt
# Your existing dependencies...
fastapi==0.104.1
uvicorn[standard]==0.24.0
# ... other dependencies ...

# Add RenderCV
rendercv
pyyaml==6.0.1
```

## 3. Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Verify RenderCV installation
rendercv --version
```

## 4. Test the Integration

### Start your server:
```bash
python main.py
```

### Test the health endpoint:
```bash
curl http://localhost:8000/rendercv/health
```

Expected response:
```json
{
    "status": "healthy",
    "rendercv_version": "2.2",
    "message": "RenderCV is installed and working"
}
```

### Test the complete workflow:
```bash
curl -X POST "http://localhost:8000/rendercv/modify-resume" \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "Senior Python Developer with FastAPI experience",
       "company_name": "TechCorp",
       "position_title": "Senior Python Developer"
     }'
```

## 5. File Structure After Integration

Your project structure should look like:

```
resume-modifier-agent/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── graph.py  # Updated with RenderCV integration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py  # Your existing endpoints
│   │   └── rendercv_endpoints.py  # New RenderCV endpoints
│   └── config.py
├── cv/
│   └── main.tex  # Your LaTeX resume
├── output/  # Generated files will be saved here
├── requirements.txt  # Updated with RenderCV
├── main.py  # Updated with new router
├── README_RENDERCV.md  # RenderCV documentation
└── INTEGRATION_GUIDE.md  # This file
```

## 6. Available Endpoints After Integration

### Existing Endpoints
- Your original endpoints remain unchanged
- Backward compatibility is maintained

### New RenderCV Endpoints
- `GET /rendercv/health` - Check RenderCV status
- `POST /rendercv/modify-resume` - AI modification + PDF generation
- `GET /rendercv/download/{session_id}/{file_type}` - Download files
- `POST /rendercv/render-yaml` - Direct YAML to PDF rendering
- `POST /rendercv/upload-yaml` - Upload YAML file for rendering
- `GET /rendercv/session/{session_id}` - Session information

## 7. Environment Variables

Update your `.env` file:

```env
# Existing variables...
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Directories (ensure these exist)
OUTPUT_DIRECTORY=./output
CV_DIRECTORY=./cv
```

## 8. Testing the Complete Workflow

### Python Testing Script:
```python
import requests
import json

# Test the complete workflow
base_url = "http://localhost:8000"

# 1. Check RenderCV health
health = requests.get(f"{base_url}/rendercv/health")
print("Health:", health.json())

# 2. Modify resume
modify_data = {
    "job_description": "Senior FastAPI Developer position requiring Python, microservices experience.",
    "company_name": "TechCorp",
    "position_title": "Senior FastAPI Developer"
}

response = requests.post(f"{base_url}/rendercv/modify-resume", json=modify_data)
result = response.json()

print(f"Session ID: {result['session_id']}")
print(f"Files available: {[k for k in result.keys() if '_file' in k]}")

# 3. Download the RenderCV PDF
session_id = result['session_id']
pdf_response = requests.get(f"{base_url}/rendercv/download/{session_id}/pdf-rendercv")

if pdf_response.status_code == 200:
    with open("modified_resume.pdf", "wb") as f:
        f.write(pdf_response.content)
    print("PDF downloaded successfully!")
else:
    print(f"Failed to download PDF: {pdf_response.status_code}")
```

## 9. Error Handling

The integration provides robust error handling:

### RenderCV Not Available
- Falls back to LaTeX compilation
- Logs warnings but doesn't fail
- Health endpoint shows status

### Invalid YAML
- Clear error messages
- Validation before processing
- Fallback options available

### File Issues
- Automatic directory creation
- Proper cleanup of temp files
- Session-based file management

## 10. Benefits of This Integration

### For Users:
- Professional PDF output using modern Typst engine
- Multiple output formats (LaTeX, YAML, PDF)
- Better typography and formatting than traditional LaTeX
- Mobile-friendly and ATS-optimized PDFs

### For Developers:
- Clean separation of concerns
- RESTful API design
- Session-based file management
- Comprehensive error handling
- Backward compatibility maintained

### For CI/CD:
- Docker-compatible (RenderCV includes TinyTeX)
- No external LaTeX installation required
- Stateless operation
- Health checks for monitoring

## 11. Next Steps

1. **Test the integration** with your existing resume
2. **Customize RenderCV themes** by modifying the YAML output
3. **Set up monitoring** using the health endpoint
4. **Configure file cleanup** for the output directory
5. **Add authentication** if needed for production use

This integration transforms your resume modification system into a complete, professional resume generation platform while maintaining all existing functionality. 