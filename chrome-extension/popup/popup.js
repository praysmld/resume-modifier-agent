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
    const filename = `resume_${jobData.company || 'job'}_${Date.now()}.pdf`;

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
