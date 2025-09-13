# Resume Modifier Agent

An intelligent agent that modifies resumes based on job descriptions using LangGraph and FastAPI.

## Features

- **Job Description Analysis**: Analyzes job postings to extract key requirements
- **Resume Modification**: Automatically modifies LaTeX resumes to match job requirements
- **Gap Identification**: Identifies missing skills and experience gaps
- **Session Management**: Tracks modification history and suggestions
- **RESTful API**: Easy-to-use API endpoints for integration

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

3. **Set API Keys**
   Add either OpenAI or Anthropic API key to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Usage

1. **Start the Server**
   ```bash
   python main.py
   ```

2. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### POST `/api/v1/modify-resume`
Modify resume based on job description
```json
{
  "job_description": "Job posting text...",
  "company_name": "Company Name",
  "position_title": "Position Title",
  "requirements": "Additional requirements (optional)"
}
```

### POST `/api/v1/analyze-job`
Analyze job description without modifying resume
```json
{
  "job_description": "Job posting text...",
  "company_name": "Company Name",
  "position_title": "Position Title"
}
```

### GET `/api/v1/resume-content`
Get current resume content

### GET `/api/v1/sessions/{session_id}`
Get modification history for a session

## Architecture

The agent uses LangGraph to orchestrate multiple specialized nodes:

1. **Load Resume**: Loads the LaTeX resume from `cv/main.tex`
2. **Analyze Job**: Extracts key requirements from job description
3. **Identify Gaps**: Compares resume with job requirements
4. **Modify Content**: Generates improved resume content
5. **Format Output**: Saves modified resume to output directory

## File Structure

```
resume-modifier-agent/
├── app/
│   ├── agents/
│   │   └── graph.py          # Main agent logic
│   ├── api/
│   │   └── endpoints.py      # API endpoints
│   └── config.py             # Configuration settings
├── cv/
│   └── main.tex             # Source resume (LaTeX)
├── output/                  # Modified resumes
├── main.py                 # FastAPI application
└── requirements.txt        # Python dependencies
```

## Future Enhancements

- PDF input/output support
- Multiple resume templates
- Advanced formatting options
- Integration with job boards
- Resume scoring and optimization
- A/B testing for different versions 