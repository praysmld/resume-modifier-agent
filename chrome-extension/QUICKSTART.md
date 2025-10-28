# Quick Start Guide

Get the Resume Modifier Chrome extension up and running in 5 minutes.

## Step 1: Start the Backend (2 minutes)

```bash
# Navigate to project root
cd /mnt/d/project/resume-modifier-agent

# Activate virtual environment
source .venv/bin/activate

# Start the server
python main.py
```

**Verify backend is running:**
- Open browser: `http://localhost:8000/docs`
- You should see the API documentation

## Step 2: Load Extension in Chrome (1 minute)

1. Open Chrome browser
2. Navigate to: `chrome://extensions/`
3. Enable **"Developer mode"** (toggle switch in top-right corner)
4. Click **"Load unpacked"** button
5. Navigate to and select: `/mnt/d/project/resume-modifier-agent/chrome-extension/`
6. Extension should appear with a blue icon

## Step 3: First-Time Setup (2 minutes)

1. **Click the extension icon** in Chrome toolbar (blue square)

2. **Register an account:**
   - Click "Register" tab
   - Fill in:
     - Name: Your Name
     - Email: your.email@example.com
     - Password: (your password)
   - Click "Register"

3. **Upload your master resume:**
   - Click "Choose File"
   - Select your resume (PDF or DOCX)
   - Click "Upload"
   - Wait for upload to complete
   - Status should change to "Uploaded" ✅

## Step 4: Generate Your First Resume (1 minute)

### Method A: From Any Job Posting

1. Navigate to a job on:
   - LinkedIn: `https://www.linkedin.com/jobs/`
   - Indeed: `https://www.indeed.com/`
   - Glassdoor: `https://www.glassdoor.com/`

2. Open any job posting

3. **Click the extension icon**

4. Click **"Generate Resume for This Job"**

5. Choose where to save the PDF

6. Done! 🎉

### Method B: From Injected Button

1. Navigate to any job posting
2. Look for the blue button: **"📄 Generate Custom Resume"**
3. Click it, then click the extension icon
4. Click **"Generate Resume for This Job"**

## Troubleshooting

### Extension icon not visible?
- Go to `chrome://extensions/`
- Find "Resume Modifier - AI Resume Customizer"
- Click the puzzle piece icon in Chrome toolbar
- Pin the extension

### Backend connection error?
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Should return:
# {"status":"healthy", ...}
```

### Can't see job description button?
- Refresh the job posting page
- Make sure you're on a supported site (LinkedIn/Indeed/Glassdoor)
- Check that page fully loaded

### Upload failed?
- Check file is PDF or DOCX format
- File size should be under 10MB
- Make sure you're logged in

## What's Next?

- **View recent resumes**: Scroll down in the popup to see history
- **Re-download**: Click any resume in history to download again
- **Check quota**: See remaining generations (20 per hour)
- **Try different jobs**: Generate resumes for multiple positions

## Full Documentation

- [Complete README](README.md) - Full documentation
- [Testing Guide](TESTING.md) - Comprehensive testing scenarios
- [API Documentation](../API_DOCUMENTATION.md) - Backend API reference
- [Integration Guide](../CHROME_EXTENSION_INTEGRATION.md) - Technical details

## Need Help?

Common issues:
1. **CORS errors** → Backend CORS is configured for all origins (`*`)
2. **401 Unauthorized** → Token expired, logout and login again
3. **429 Rate Limit** → Wait an hour, you've used your 20 quick-modify quota
4. **Can't find job description** → Page not fully loaded or unsupported site

## Architecture Overview

```
User clicks extension → Popup opens (popup.js)
                     ↓
            Authenticate (api-client.js)
                     ↓
        Call backend API (localhost:8000)
                     ↓
          Generate custom resume (AI)
                     ↓
        Download PDF → Save to computer
```

Enjoy generating customized resumes! 🚀
