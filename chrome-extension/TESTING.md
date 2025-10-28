# Chrome Extension Testing Guide

Quick guide to test the Resume Modifier Chrome extension.

## Pre-Testing Checklist

- [ ] Backend server is running (`python main.py`)
- [ ] Backend is accessible at `http://localhost:8000`
- [ ] Extension is loaded in Chrome (`chrome://extensions/`)
- [ ] Have a test resume file (PDF or DOCX) ready

## Test Scenarios

### 1. Installation & First Launch

**Steps:**
1. Load extension in Chrome (Developer mode → Load unpacked)
2. Click extension icon in toolbar
3. Should see login/register screen

**Expected:**
- ✅ Popup opens (400px x 500px)
- ✅ Two tabs: "Login" and "Register"
- ✅ Clean, professional UI

### 2. User Registration

**Steps:**
1. Click "Register" tab
2. Enter:
   - Full Name: "Test User"
   - Email: "test@example.com"
   - Password: "password123"
3. Click "Register" button

**Expected:**
- ✅ No errors
- ✅ Automatically switches to main screen
- ✅ Shows status card

### 3. Master Resume Upload

**Steps:**
1. Should see "Upload Master Resume" section
2. Click file input, select resume PDF/DOCX
3. Click "Upload" button

**Expected:**
- ✅ Shows "Processing..." loading message
- ✅ Success: Status changes to "Uploaded" (green badge)
- ✅ Upload section hides
- ✅ Quick Modify section appears

### 4. Extension Status Check

**Steps:**
1. Look at status card after upload

**Expected:**
- ✅ Master Resume: "Uploaded" (green)
- ✅ Quota Remaining: "20/20"

### 5. Job Description Extraction (LinkedIn)

**Steps:**
1. Navigate to: `https://www.linkedin.com/jobs/`
2. Open any job posting
3. Wait for page to fully load
4. Look for injected button at top of job description

**Expected:**
- ✅ Blue button appears: "📄 Generate Custom Resume"
- ✅ Button is styled correctly
- ✅ Button is clickable

### 6. Quick Modify from LinkedIn

**Steps:**
1. On LinkedIn job posting page
2. Click extension icon
3. Click "Generate Resume for This Job"
4. Wait for processing

**Expected:**
- ✅ Shows "Processing..." message
- ✅ Browser download dialog appears
- ✅ PDF file downloads with format: `resume_CompanyName_timestamp.pdf`
- ✅ Success notification appears
- ✅ Quota decrements to "19/20"

### 7. Quick Modify from Indeed

**Steps:**
1. Navigate to: `https://www.indeed.com/`
2. Search for jobs and open a posting
3. Click extension icon
4. Click "Generate Resume for This Job"

**Expected:**
- ✅ Extracts job description correctly
- ✅ PDF downloads successfully
- ✅ Quota decrements

### 8. Recent Resumes History

**Steps:**
1. After generating 2-3 resumes
2. Open extension popup
3. Scroll to "Recent Resumes" section

**Expected:**
- ✅ Lists recent resumes with:
  - Job title
  - Company name
  - Date generated
- ✅ Items are clickable

### 9. Re-download Resume

**Steps:**
1. Click on any resume in "Recent Resumes" list

**Expected:**
- ✅ Shows loading message
- ✅ Download dialog appears
- ✅ PDF downloads with filename: `resume_[id].pdf`

### 10. Logout and Re-login

**Steps:**
1. Click "Logout" button
2. Should return to auth screen
3. Login with same credentials

**Expected:**
- ✅ Returns to login screen
- ✅ Can re-login successfully
- ✅ Master resume status persists
- ✅ Recent resumes still visible

### 11. Content Script Injection

**Steps:**
1. Navigate to supported job sites:
   - LinkedIn: `https://www.linkedin.com/jobs/`
   - Indeed: `https://www.indeed.com/viewjob?jk=[job_id]`
   - Glassdoor: `https://www.glassdoor.com/job-listing/`
2. Open job posting

**Expected:**
- ✅ Button appears on all supported sites
- ✅ Button positioned correctly
- ✅ Button doesn't interfere with page layout

### 12. Error Handling

**Test A: No Resume Uploaded**
1. Create new account
2. Try to generate resume before uploading
3. **Expected:** ❌ Error message or disabled button

**Test B: Invalid Job Page**
1. Navigate to non-job page (e.g., Google)
2. Click extension icon
3. Click "Generate Resume"
4. **Expected:** ❌ Error: "Could not find job description"

**Test C: Backend Offline**
1. Stop backend server
2. Try to generate resume
3. **Expected:** ❌ Network error message

**Test D: Rate Limit**
1. Generate 20 resumes rapidly
2. Try 21st generation
3. **Expected:** ❌ "Rate limit exceeded" error

### 13. Download Notification

**Steps:**
1. Generate a resume
2. Wait for download to complete

**Expected:**
- ✅ Chrome notification appears
- ✅ Message: "Your customized resume has been downloaded successfully!"
- ✅ Notification shows extension icon

### 14. Token Expiration (24h)

**Steps:**
1. Login to extension
2. Manually set system time forward 25 hours (or wait)
3. Try to generate resume

**Expected:**
- ✅ Gets 401 error
- ✅ Automatically logs out
- ✅ Returns to login screen

## Manual API Testing

### Test Backend Endpoints

```bash
# Register user
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Check extension status (use token from login)
curl -X GET "http://localhost:8000/api/extension/status" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Health check
curl http://localhost:8000/api/health
```

## Browser Console Testing

### Check Storage

```javascript
// View stored auth token
chrome.storage.local.get(['authToken'], (result) => {
  console.log('Token:', result.authToken);
});

// Clear storage (force logout)
chrome.storage.local.clear(() => {
  console.log('Storage cleared');
});
```

### Test API Client Directly

```javascript
// In extension popup (right-click icon → Inspect)
apiClient.checkHealth().then(console.log);
apiClient.getExtensionStatus().then(console.log);
```

## Performance Testing

- [ ] Popup opens in < 500ms
- [ ] Login/register completes in < 2s
- [ ] Resume upload completes in < 5s (for 1MB file)
- [ ] Resume generation completes in < 10s
- [ ] Recent resumes loads in < 1s

## Cross-Browser Testing

While built for Chrome, test on:
- [ ] Chrome (primary)
- [ ] Edge (Chromium-based, should work)
- [ ] Brave (Chromium-based, should work)

## Known Issues & Limitations

1. **Cannot programmatically open popup in Manifest V3**
   - Injected button can't directly open popup
   - User must click extension icon

2. **Job description extraction may fail on:**
   - Dynamically loaded content
   - Non-standard job page layouts
   - Pages that require login

3. **Rate limiting per hour (not per day)**
   - 20 quick-modify requests per hour
   - Resets every hour

## Test Results Template

```
Date: ___________
Tester: ___________

✅ Installation & First Launch
✅ User Registration
✅ Master Resume Upload
✅ Extension Status Check
✅ Job Extraction (LinkedIn)
✅ Quick Modify (LinkedIn)
✅ Quick Modify (Indeed)
✅ Recent Resumes History
✅ Re-download Resume
✅ Logout/Login
✅ Content Script Injection
✅ Error Handling
✅ Download Notification

Issues Found:
1. _______________________
2. _______________________
3. _______________________
```

## Debugging Tips

### Popup Not Opening
- Check for JavaScript errors in console
- Verify manifest.json is valid JSON
- Reload extension

### API Calls Failing
- Check CORS settings in backend
- Verify backend is running
- Check network tab in DevTools

### Content Script Not Injecting
- Verify URL matches patterns in manifest.json
- Check for CSP (Content Security Policy) errors
- Refresh the job posting page

### Icons Not Showing
- Verify icon files exist in `icons/` folder
- Check file permissions
- Reload extension

## Next Steps After Testing

1. Fix any bugs found
2. Improve error messages
3. Add loading states
4. Optimize performance
5. Prepare for production deployment
