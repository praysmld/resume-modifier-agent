# Resume Modifier Chrome Extension

AI-powered Chrome extension that automatically customizes your resume for any job posting.

## Features

- **Right-Click Context Menu**: Select any job description text, right-click, and generate resume instantly
- **One-Click Resume Generation**: Generate tailored resumes directly from job postings
- **Works on ANY Website**: Not limited to job boards - works wherever you find job descriptions
- **Multi-Platform Support**: Works on LinkedIn, Indeed, and Glassdoor
- **JWT Authentication**: Secure login and registration
- **Master Resume Management**: Upload once, customize many times
- **Resume History**: View and download previously generated resumes
- **Rate Limiting**: Track your daily quota (20 quick modifications per hour)
- **Injected Buttons**: Convenient buttons added directly to job posting pages

## Installation

### Development Setup

1. **Ensure Backend is Running**
   ```bash
   cd /mnt/d/project/resume-modifier-agent
   source .venv/bin/activate
   python main.py
   ```
   Backend should be running at `http://localhost:8000`

2. **Load Extension in Chrome**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `chrome-extension/` folder
   - Extension icon should appear in your browser toolbar

3. **First-Time Setup**
   - Click the extension icon
   - Register a new account or login
   - Upload your master resume (PDF or DOCX)
   - You're ready to generate customized resumes!

## Usage

### Method 1: Right-Click Context Menu (NEW! - Fastest Method)

1. **Find a job description** on ANY website (company careers page, job board, email, etc.)
2. **Select the job description text** with your mouse
3. **Right-click** the selected text
4. **Click "Generate Resume from Job Description"**
5. Your customized resume will be generated and downloaded automatically!

**Works on:**
- Company career pages
- Job boards (LinkedIn, Indeed, Glassdoor, etc.)
- Job descriptions in emails or documents
- Any webpage with job posting text

### Method 2: From Extension Popup

1. Navigate to any job posting on LinkedIn, Indeed, or Glassdoor
2. Click the Resume Modifier extension icon
3. Click "Generate Resume for This Job"
4. Choose where to save your customized resume

### Method 3: From Injected Button

1. Navigate to any job posting
2. Look for the blue "📄 Generate Custom Resume" button at the top
3. Click the button, then click the extension icon
4. Generate your customized resume

### View Recent Resumes

- Click the extension icon
- Scroll to "Recent Resumes" section
- Click any resume to re-download it

## Project Structure

```
chrome-extension/
├── manifest.json              # Extension configuration (Manifest V3)
├── popup/
│   ├── popup.html            # Extension popup UI
│   ├── popup.js              # UI logic and event handlers
│   └── popup.css             # Popup styling
├── background/
│   └── background.js         # Service worker for notifications
├── content/
│   ├── content.js            # Job page scraping & button injection
│   └── content.css           # Injected button styling
├── api/
│   └── api-client.js         # Backend API wrapper
└── icons/
    ├── icon16.png            # 16x16 extension icon
    ├── icon48.png            # 48x48 extension icon
    └── icon128.png           # 128x128 extension icon
```

## Supported Job Sites

- **LinkedIn**: `https://*.linkedin.com/jobs/*`
- **Indeed**: `https://*.indeed.com/viewjob*`
- **Glassdoor**: `https://*.glassdoor.com/job-listing/*`

## API Integration

The extension communicates with the Resume Modifier API:

- Base URL: `http://localhost:8000/api`
- Authentication: JWT Bearer tokens
- Key Endpoints:
  - `/users/register` - User registration
  - `/users/login` - Authentication
  - `/resumes/upload` - Master resume upload
  - `/extension/quick-modify` - One-click resume generation
  - `/extension/status` - Check user status and quota
  - `/resumes/generated` - List generated resumes

## Troubleshooting

### Extension Not Working

1. **Check Backend Status**
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return `{"status": "healthy"}`

2. **Clear Extension Storage**
   - Go to `chrome://extensions/`
   - Find Resume Modifier
   - Click "Details" → "Inspect views: service worker"
   - In console: `chrome.storage.local.clear()`

3. **Reload Extension**
   - Go to `chrome://extensions/`
   - Click reload icon for Resume Modifier

### CORS Errors

Ensure your backend has CORS properly configured in [main.py](../main.py):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Job Description Not Detected

- Make sure you're on a supported job site
- Wait for page to fully load before clicking
- Some job sites dynamically load content - try refreshing

### Rate Limit Exceeded

- You have 20 quick modifications per hour
- Wait for quota to reset
- Check remaining quota in extension popup

## Production Deployment

### Update API URL

Edit [api/api-client.js](api/api-client.js):
```javascript
constructor() {
  this.baseURL = 'https://your-production-api.com/api';
  // ...
}
```

### Update Manifest

Edit [manifest.json](manifest.json) to add production host permissions:
```json
"host_permissions": [
  "https://*.linkedin.com/*",
  "https://*.indeed.com/*",
  "https://*.glassdoor.com/*",
  "https://your-production-api.com/*"
]
```

### Package Extension

```bash
cd chrome-extension
zip -r resume-modifier-extension.zip . -x "*.git*" "*/create_icons.py"
```

### Submit to Chrome Web Store

1. Create a [Chrome Web Store Developer account](https://chrome.google.com/webstore/devconsole)
2. Pay one-time $5 registration fee
3. Upload `resume-modifier-extension.zip`
4. Fill in store listing details
5. Submit for review

## Development

### Key Files to Modify

- **API Endpoints**: [api/api-client.js](api/api-client.js)
- **UI Changes**: [popup/popup.html](popup/popup.html), [popup/popup.css](popup/popup.css)
- **Logic**: [popup/popup.js](popup/popup.js)
- **Job Scraping**: [content/content.js](content/content.js)

### Testing

1. Make changes to any file
2. Go to `chrome://extensions/`
3. Click reload icon for Resume Modifier
4. Test the extension

### Debugging

- **Popup Debugging**: Right-click extension icon → "Inspect"
- **Background Script**: Go to `chrome://extensions/` → "Inspect views: service worker"
- **Content Script**: Open DevTools on job posting page → Console tab

## Security Notes

- JWT tokens stored in `chrome.storage.local`
- Tokens expire after 24 hours
- No sensitive data stored in extension
- All API calls use HTTPS (in production)

## License

Part of the Resume Modifier project. See main repository for license details.

## Support

For issues and feature requests, see the main project documentation:
- [API Documentation](../API_DOCUMENTATION.md)
- [Integration Guide](../CHROME_EXTENSION_INTEGRATION.md)
