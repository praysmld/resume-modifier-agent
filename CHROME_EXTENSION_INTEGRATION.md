# Chrome Extension Integration Guide

## Overview

This guide provides a complete implementation plan for building a Chrome extension that integrates with the Resume Modifier API. The backend is already configured with extension-specific endpoints and CORS support.

## Backend API Status ✅

Your FastAPI backend already includes:

### Authentication
- `POST /api/users/register` - User registration
- `POST /api/users/login` - Login and get JWT token
- `GET /api/users/profile` - Get user profile

### Extension-Specific Endpoints
- `POST /api/extension/quick-modify` - One-click resume generation (20 req/hour)
- `GET /api/extension/status` - Check if user has master resume uploaded

### Resume Management
- `POST /api/resumes/upload` - Upload master resume
- `GET /api/resumes/master` - Get master resume data
- `GET /api/resumes/generated` - List all generated resumes
- `GET /api/resumes/generated/{resume_id}` - Download specific resume

### Job Description Processing
- `POST /api/jobs/analyze` - Analyze job description
- `POST /api/modify-resume` - Full resume modification with customizations

### Configuration
- CORS enabled for all origins
- JWT authentication with 24-hour expiry
- Rate limiting implemented
- File upload/download support

## Chrome Extension Architecture

```
chrome-extension/
├── manifest.json           # Extension configuration
├── popup/
│   ├── popup.html         # Extension popup UI
│   ├── popup.js           # Popup logic
│   └── popup.css          # Popup styles
├── background/
│   └── background.js      # Background service worker
├── content/
│   └── content.js         # Content script (inject into job pages)
├── auth/
│   └── auth.js            # Authentication helper
├── api/
│   └── api-client.js      # API communication layer
├── utils/
│   └── storage.js         # Chrome storage helper
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Step-by-Step Implementation

### 1. Create Extension Manifest

**File: `manifest.json`**

```json
{
  "manifest_version": 3,
  "name": "Resume Modifier - AI Resume Customizer",
  "version": "1.0.0",
  "description": "Automatically customize your resume for any job posting with AI",
  "permissions": [
    "storage",
    "activeTab",
    "scripting"
  ],
  "host_permissions": [
    "https://*.linkedin.com/*",
    "https://*.indeed.com/*",
    "https://*.glassdoor.com/*",
    "http://localhost:8000/*"
  ],
  "background": {
    "service_worker": "background/background.js"
  },
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [
    {
      "matches": [
        "https://*.linkedin.com/jobs/*",
        "https://*.indeed.com/viewjob*",
        "https://*.glassdoor.com/job-listing/*"
      ],
      "js": ["content/content.js"],
      "css": ["content/content.css"]
    }
  ],
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### 2. API Client

**File: `api/api-client.js`**

```javascript
class APIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000/api'; // Change for production
    this.extensionVersion = '1.0.0';
  }

  async getAuthToken() {
    const result = await chrome.storage.local.get(['authToken']);
    return result.authToken;
  }

  async setAuthToken(token) {
    await chrome.storage.local.set({ authToken: token });
  }

  async clearAuthToken() {
    await chrome.storage.local.remove(['authToken']);
  }

  async makeRequest(endpoint, options = {}) {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      'X-Extension-Version': this.extensionVersion,
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      await this.clearAuthToken();
      throw new Error('Authentication required. Please log in again.');
    }

    if (response.status === 429) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    // Handle file downloads
    if (options.responseType === 'blob') {
      return response.blob();
    }

    return response.json();
  }

  // Authentication
  async register(email, password, fullName) {
    const response = await this.makeRequest('/users/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName
      })
    });

    await this.setAuthToken(response.access_token);
    return response;
  }

  async login(email, password) {
    const response = await this.makeRequest('/users/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    await this.setAuthToken(response.access_token);
    return response;
  }

  async logout() {
    await this.clearAuthToken();
  }

  async getProfile() {
    return this.makeRequest('/users/profile');
  }

  // Extension-specific endpoints
  async getExtensionStatus() {
    return this.makeRequest('/extension/status');
  }

  async quickModifyResume(selectedText, pageUrl, quickSettings = {}) {
    return this.makeRequest('/extension/quick-modify', {
      method: 'POST',
      body: JSON.stringify({
        selected_text: selectedText,
        page_url: pageUrl,
        quick_settings: {
          format: 'pdf',
          template: 'default',
          ...quickSettings
        }
      }),
      responseType: 'blob'
    });
  }

  // Resume management
  async uploadMasterResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseURL}/resumes/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Extension-Version': this.extensionVersion
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async getMasterResume() {
    return this.makeRequest('/resumes/master');
  }

  async getGeneratedResumes(limit = 10, offset = 0) {
    return this.makeRequest(`/resumes/generated?limit=${limit}&offset=${offset}`);
  }

  async downloadResume(resumeId) {
    return this.makeRequest(`/resumes/generated/${resumeId}`, {
      responseType: 'blob'
    });
  }

  // Job analysis
  async analyzeJob(jobDescription, companyName, jobTitle, jobUrl) {
    return this.makeRequest('/jobs/analyze', {
      method: 'POST',
      body: JSON.stringify({
        job_description: jobDescription,
        company_name: companyName,
        job_title: jobTitle,
        job_url: jobUrl
      })
    });
  }

  async modifyResume(jobDescription, jobTitle, companyName, customizations = {}) {
    return this.makeRequest('/modify-resume', {
      method: 'POST',
      body: JSON.stringify({
        job_description: jobDescription,
        job_title: jobTitle,
        company_name: companyName,
        customizations
      }),
      responseType: 'blob'
    });
  }

  // Health check
  async checkHealth() {
    return this.makeRequest('/health');
  }
}

// Export singleton instance
const apiClient = new APIClient();
```

### 3. Popup UI

**File: `popup/popup.html`**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Resume Modifier</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div id="app">
    <!-- Login/Register Screen -->
    <div id="auth-screen" class="screen">
      <div class="header">
        <h1>Resume Modifier</h1>
        <p>AI-Powered Resume Customization</p>
      </div>

      <div class="tabs">
        <button id="login-tab" class="tab active">Login</button>
        <button id="register-tab" class="tab">Register</button>
      </div>

      <!-- Login Form -->
      <form id="login-form" class="auth-form">
        <input type="email" id="login-email" placeholder="Email" required>
        <input type="password" id="login-password" placeholder="Password" required>
        <button type="submit" class="btn-primary">Login</button>
      </form>

      <!-- Register Form -->
      <form id="register-form" class="auth-form hidden">
        <input type="text" id="register-name" placeholder="Full Name" required>
        <input type="email" id="register-email" placeholder="Email" required>
        <input type="password" id="register-password" placeholder="Password" required>
        <button type="submit" class="btn-primary">Register</button>
      </form>

      <div id="auth-error" class="error hidden"></div>
    </div>

    <!-- Main Screen (After Login) -->
    <div id="main-screen" class="screen hidden">
      <div class="header">
        <h2>Resume Modifier</h2>
        <button id="logout-btn" class="btn-text">Logout</button>
      </div>

      <div id="status-card" class="card">
        <div class="status-item">
          <span>Master Resume:</span>
          <span id="master-resume-status" class="status-badge">Loading...</span>
        </div>
        <div class="status-item">
          <span>Quota Remaining:</span>
          <span id="quota-status">--</span>
        </div>
      </div>

      <!-- Upload Master Resume Section -->
      <div id="upload-section" class="section hidden">
        <h3>Upload Master Resume</h3>
        <input type="file" id="resume-file" accept=".pdf,.docx">
        <button id="upload-btn" class="btn-primary">Upload</button>
      </div>

      <!-- Quick Modify Section -->
      <div id="modify-section" class="section hidden">
        <h3>Quick Modify</h3>
        <p class="hint">Navigate to a job posting and click "Generate Resume"</p>
        <button id="generate-resume-btn" class="btn-primary">
          Generate Resume for This Job
        </button>
        <div id="job-info" class="job-info hidden">
          <p><strong>Detected Job:</strong> <span id="job-title">--</span></p>
          <p><strong>Company:</strong> <span id="company-name">--</span></p>
        </div>
      </div>

      <!-- Recent Resumes -->
      <div id="recent-section" class="section">
        <h3>Recent Resumes</h3>
        <div id="recent-resumes" class="resume-list">
          <p class="hint">No resumes generated yet</p>
        </div>
      </div>

      <div id="main-error" class="error hidden"></div>
      <div id="loading" class="loading hidden">Processing...</div>
    </div>
  </div>

  <script src="../api/api-client.js"></script>
  <script src="popup.js"></script>
</body>
</html>
```

**File: `popup/popup.css`**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  width: 400px;
  min-height: 500px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
}

#app {
  background: white;
}

.screen {
  padding: 20px;
}

.hidden {
  display: none !important;
}

/* Header */
.header {
  margin-bottom: 20px;
  text-align: center;
}

.header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 5px;
}

.header h2 {
  font-size: 20px;
  color: #333;
  margin-bottom: 10px;
}

.header p {
  color: #666;
  font-size: 14px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
  border-radius: 5px;
  font-size: 14px;
  transition: all 0.3s;
}

.tab.active {
  background: #2563eb;
  color: white;
}

/* Forms */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
}

input:focus {
  outline: none;
  border-color: #2563eb;
}

/* Buttons */
.btn-primary {
  padding: 12px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.btn-text {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 14px;
  padding: 5px 10px;
}

/* Status Card */
.card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.ready {
  background: #dcfce7;
  color: #166534;
}

.status-badge.missing {
  background: #fee2e2;
  color: #991b1b;
}

/* Sections */
.section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.section:last-child {
  border-bottom: none;
}

.section h3 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #333;
}

.hint {
  color: #666;
  font-size: 13px;
  margin-bottom: 10px;
}

/* Job Info */
.job-info {
  background: #f1f5f9;
  padding: 12px;
  border-radius: 5px;
  margin-top: 10px;
  font-size: 13px;
}

.job-info p {
  margin: 5px 0;
}

/* Resume List */
.resume-list {
  max-height: 200px;
  overflow-y: auto;
}

.resume-item {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.resume-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.resume-item-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.resume-item-meta {
  font-size: 12px;
  color: #666;
}

/* Error */
.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 10px;
  border-radius: 5px;
  font-size: 13px;
  margin-top: 10px;
}

/* Loading */
.loading {
  text-align: center;
  padding: 20px;
  color: #2563eb;
  font-weight: 600;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
```

**File: `popup/popup.js`**

```javascript
// Initialize
let currentUser = null;
let extensionStatus = null;

document.addEventListener('DOMContentLoaded', async () => {
  await init();
});

async function init() {
  // Check if user is already logged in
  const token = await apiClient.getAuthToken();

  if (token) {
    await loadMainScreen();
  } else {
    showAuthScreen();
  }

  setupEventListeners();
}

function setupEventListeners() {
  // Auth tabs
  document.getElementById('login-tab').addEventListener('click', () => {
    switchTab('login');
  });

  document.getElementById('register-tab').addEventListener('click', () => {
    switchTab('register');
  });

  // Auth forms
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('register-form').addEventListener('submit', handleRegister);

  // Main actions
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('upload-btn').addEventListener('click', handleUpload);
  document.getElementById('generate-resume-btn').addEventListener('click', handleQuickModify);
}

function switchTab(tab) {
  const loginTab = document.getElementById('login-tab');
  const registerTab = document.getElementById('register-tab');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  if (tab === 'login') {
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  } else {
    registerTab.classList.add('active');
    loginTab.classList.remove('active');
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
  }
}

async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
    showAuthError('');
    await apiClient.login(email, password);
    await loadMainScreen();
  } catch (error) {
    showAuthError(error.message);
  }
}

async function handleRegister(e) {
  e.preventDefault();

  const name = document.getElementById('register-name').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;

  try {
    showAuthError('');
    await apiClient.register(email, password, name);
    await loadMainScreen();
  } catch (error) {
    showAuthError(error.message);
  }
}

async function handleLogout() {
  await apiClient.logout();
  showAuthScreen();
}

async function handleUpload() {
  const fileInput = document.getElementById('resume-file');
  const file = fileInput.files[0];

  if (!file) {
    showMainError('Please select a file');
    return;
  }

  try {
    showLoading(true);
    showMainError('');
    await apiClient.uploadMasterResume(file);
    await loadExtensionStatus();
    showLoading(false);
  } catch (error) {
    showLoading(false);
    showMainError(error.message);
  }
}

async function handleQuickModify() {
  try {
    showLoading(true);
    showMainError('');

    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Execute content script to extract job description
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractJobDescription
    });

    const jobData = results[0].result;

    if (!jobData.description) {
      throw new Error('Could not find job description on this page');
    }

    // Call quick modify API
    const pdfBlob = await apiClient.quickModifyResume(
      jobData.description,
      tab.url
    );

    // Download the PDF
    const url = URL.createObjectURL(pdfBlob);
    const filename = `resume_${jobData.company}_${Date.now()}.pdf`;

    await chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: true
    });

    showLoading(false);
    await loadRecentResumes();

  } catch (error) {
    showLoading(false);
    showMainError(error.message);
  }
}

// Content script function to extract job description
function extractJobDescription() {
  // This will run in the context of the job posting page
  const hostname = window.location.hostname;
  let description = '';
  let company = '';
  let title = '';

  if (hostname.includes('linkedin.com')) {
    description = document.querySelector('.jobs-description')?.innerText || '';
    company = document.querySelector('.jobs-unified-top-card__company-name')?.innerText || '';
    title = document.querySelector('.jobs-unified-top-card__job-title')?.innerText || '';
  } else if (hostname.includes('indeed.com')) {
    description = document.querySelector('#jobDescriptionText')?.innerText || '';
    company = document.querySelector('[data-testid="inlineHeader-companyName"]')?.innerText || '';
    title = document.querySelector('.jobsearch-JobInfoHeader-title')?.innerText || '';
  } else if (hostname.includes('glassdoor.com')) {
    description = document.querySelector('.job-description')?.innerText || '';
    company = document.querySelector('.employer-name')?.innerText || '';
    title = document.querySelector('.job-title')?.innerText || '';
  }

  return { description, company, title };
}

async function loadMainScreen() {
  try {
    currentUser = await apiClient.getProfile();
    await loadExtensionStatus();
    await loadRecentResumes();
    showMainScreen();
  } catch (error) {
    showAuthError('Failed to load user data. Please login again.');
    await apiClient.logout();
    showAuthScreen();
  }
}

async function loadExtensionStatus() {
  try {
    extensionStatus = await apiClient.getExtensionStatus();

    // Update UI
    const masterResumeStatus = document.getElementById('master-resume-status');
    const quotaStatus = document.getElementById('quota-status');
    const uploadSection = document.getElementById('upload-section');
    const modifySection = document.getElementById('modify-section');

    if (extensionStatus.has_master_resume) {
      masterResumeStatus.textContent = 'Uploaded';
      masterResumeStatus.className = 'status-badge ready';
      uploadSection.classList.add('hidden');
      modifySection.classList.remove('hidden');
    } else {
      masterResumeStatus.textContent = 'Not Uploaded';
      masterResumeStatus.className = 'status-badge missing';
      uploadSection.classList.remove('hidden');
      modifySection.classList.add('hidden');
    }

    quotaStatus.textContent = `${extensionStatus.remaining_quota}/20`;

  } catch (error) {
    console.error('Failed to load extension status:', error);
  }
}

async function loadRecentResumes() {
  try {
    const response = await apiClient.getGeneratedResumes(5, 0);
    const recentResumesDiv = document.getElementById('recent-resumes');

    if (response.items.length === 0) {
      recentResumesDiv.innerHTML = '<p class="hint">No resumes generated yet</p>';
      return;
    }

    recentResumesDiv.innerHTML = response.items.map(resume => `
      <div class="resume-item" data-id="${resume.id}">
        <div class="resume-item-title">${resume.job_title}</div>
        <div class="resume-item-meta">
          ${resume.company_name} • ${new Date(resume.created_at).toLocaleDateString()}
        </div>
      </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.resume-item').forEach(item => {
      item.addEventListener('click', async () => {
        const resumeId = item.dataset.id;
        await downloadResume(resumeId);
      });
    });

  } catch (error) {
    console.error('Failed to load recent resumes:', error);
  }
}

async function downloadResume(resumeId) {
  try {
    showLoading(true);
    const blob = await apiClient.downloadResume(resumeId);
    const url = URL.createObjectURL(blob);

    await chrome.downloads.download({
      url: url,
      filename: `resume_${resumeId}.pdf`,
      saveAs: true
    });

    showLoading(false);
  } catch (error) {
    showLoading(false);
    showMainError(error.message);
  }
}

// UI Helper Functions
function showAuthScreen() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('main-screen').classList.add('hidden');
}

function showMainScreen() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('main-screen').classList.remove('hidden');
}

function showAuthError(message) {
  const errorDiv = document.getElementById('auth-error');
  if (message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
  } else {
    errorDiv.classList.add('hidden');
  }
}

function showMainError(message) {
  const errorDiv = document.getElementById('main-error');
  if (message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
  } else {
    errorDiv.classList.add('hidden');
  }
}

function showLoading(show) {
  const loadingDiv = document.getElementById('loading');
  if (show) {
    loadingDiv.classList.remove('hidden');
  } else {
    loadingDiv.classList.add('hidden');
  }
}
```

### 4. Content Script (Optional Enhancement)

**File: `content/content.js`**

```javascript
// Inject a button into job posting pages
(function() {
  'use strict';

  const hostname = window.location.hostname;
  let targetSelector = '';

  // Define where to inject button for different job sites
  if (hostname.includes('linkedin.com')) {
    targetSelector = '.jobs-details__main-content';
  } else if (hostname.includes('indeed.com')) {
    targetSelector = '.jobsearch-JobComponent';
  } else if (hostname.includes('glassdoor.com')) {
    targetSelector = '.job-view';
  }

  if (targetSelector) {
    injectButton(targetSelector);
  }

  function injectButton(selector) {
    const container = document.querySelector(selector);
    if (!container) return;

    // Check if button already exists
    if (document.getElementById('resume-modifier-btn')) return;

    const button = document.createElement('button');
    button.id = 'resume-modifier-btn';
    button.className = 'resume-modifier-inject-btn';
    button.innerHTML = '📄 Generate Custom Resume';

    button.addEventListener('click', async () => {
      // Open extension popup programmatically or show notification
      chrome.runtime.sendMessage({ action: 'generateResume' });
    });

    container.insertBefore(button, container.firstChild);
  }
})();
```

**File: `content/content.css`**

```css
.resume-modifier-inject-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin: 16px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.resume-modifier-inject-btn:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}
```

### 5. Background Service Worker

**File: `background/background.js`**

```javascript
// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // Open welcome page
    chrome.tabs.create({
      url: 'http://localhost:8000/docs'
    });
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'generateResume') {
    // Open popup or show notification
    chrome.action.openPopup();
  }
});

// Handle download completion
chrome.downloads.onChanged.addListener((delta) => {
  if (delta.state && delta.state.current === 'complete') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Resume Downloaded',
      message: 'Your customized resume has been downloaded successfully!'
    });
  }
});
```

## Testing the Integration

### 1. Start Backend Server

```bash
cd /mnt/d/project/resume-modifier-agent
source .venv/bin/activate
python main.py
```

Verify backend is running at `http://localhost:8000`

### 2. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select your `chrome-extension/` folder
5. Extension should now appear in your browser

### 3. Test Workflow

1. **Click extension icon** → Should show login screen
2. **Register account** → Creates user in backend
3. **Upload master resume** → Uploads PDF to backend
4. **Navigate to LinkedIn/Indeed job posting**
5. **Click "Generate Resume"** → Creates customized resume
6. **Download PDF** → Resume saved to your computer

## Production Deployment

### Backend Changes

1. **Update CORS settings** in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://<your-extension-id>",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Deploy to cloud** (AWS, Google Cloud, Heroku, etc.)
3. **Update environment variables** for production

### Extension Changes

1. **Update API URL** in `api-client.js`:
```javascript
this.baseURL = 'https://your-api-domain.com/api';
```

2. **Add production host permissions** in `manifest.json`
3. **Package extension** for Chrome Web Store
4. **Submit for review**

## Features Included

✅ User authentication (login/register)
✅ Master resume upload
✅ One-click resume generation
✅ Job description auto-detection
✅ Recent resumes history
✅ Download generated resumes
✅ Rate limit tracking
✅ Multi-platform support (LinkedIn, Indeed, Glassdoor)
✅ Error handling
✅ Loading states

## Optional Enhancements

- [ ] Add resume preview before download
- [ ] Implement customization options in popup
- [ ] Add keyboard shortcuts
- [ ] Implement offline mode with caching
- [ ] Add analytics tracking
- [ ] Create onboarding tutorial
- [ ] Add dark mode
- [ ] Support more job sites
- [ ] Add browser notifications
- [ ] Implement resume versioning

## Troubleshooting

### CORS Errors
- Ensure backend CORS is properly configured
- Check that extension ID is whitelisted in production

### Authentication Issues
- Verify JWT token is being stored correctly
- Check token expiration (24 hours by default)
- Clear extension storage: `chrome.storage.local.clear()`

### File Upload Failures
- Verify file size limits
- Check file type restrictions (PDF, DOCX)
- Ensure proper FormData handling

### Rate Limiting
- Monitor quota usage
- Implement retry logic with exponential backoff
- Show clear error messages to users

## Support

For issues or questions:
- Backend API documentation: `http://localhost:8000/docs`
- Check browser console for errors
- Review network tab for API failures
