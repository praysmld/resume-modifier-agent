// API Client for Background Script (simplified version)
class BackgroundAPIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000/api';
    this.extensionVersion = '1.0.0';
  }

  async getAuthToken() {
    const result = await chrome.storage.local.get(['authToken']);
    return result.authToken;
  }

  async quickModifyResume(selectedText, pageUrl) {
    const token = await this.getAuthToken();

    if (!token) {
      throw new Error('Please login first. Click the extension icon to login.');
    }

    const response = await fetch(`${this.baseURL}/extension/quick-modify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Extension-Version': this.extensionVersion
      },
      body: JSON.stringify({
        selected_text: selectedText,
        page_url: pageUrl,
        quick_settings: {
          format: 'pdf',
          template: 'default'
        }
      })
    });

    if (response.status === 401) {
      throw new Error('Session expired. Please login again via extension popup.');
    }

    if (response.status === 429) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Failed to generate resume');
    }

    return response.blob();
  }
}

const apiClient = new BackgroundAPIClient();

// Create context menu on installation
chrome.runtime.onInstalled.addListener((details) => {
  // Create context menu item for selected text
  chrome.contextMenus.create({
    id: 'generate-resume',
    title: 'Generate Resume from Job Description',
    contexts: ['selection']
  });

  // Open welcome page on first install
  if (details.reason === 'install') {
    chrome.tabs.create({
      url: 'http://localhost:8000/docs'
    });
  }
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'generate-resume') {
    const selectedText = info.selectionText;
    const pageUrl = tab.url;

    try {
      // Show notification that generation started
      chrome.notifications.create({
        type: 'basic',
        iconUrl: '../icons/icon48.png',
        title: 'Resume Generation Started',
        message: 'Generating your customized resume...',
        priority: 1
      });

      // Call API to generate resume
      const pdfBlob = await apiClient.quickModifyResume(selectedText, pageUrl);

      // Create download URL
      const url = URL.createObjectURL(pdfBlob);
      const timestamp = Date.now();
      const filename = `resume_contextmenu_${timestamp}.pdf`;

      // Download the PDF
      await chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: true
      });

    } catch (error) {
      console.error('Resume generation failed:', error);

      // Show error notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: '../icons/icon48.png',
        title: 'Resume Generation Failed',
        message: error.message || 'Failed to generate resume. Please try again.',
        priority: 2
      });
    }
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'generateResume') {
    // Note: In Manifest V3, we can't programmatically open popups
    // Users need to click the extension icon
    sendResponse({ status: 'Please click the extension icon to continue' });
  }
  return true; // Keep message channel open for async response
});

// Handle download completion
chrome.downloads.onChanged.addListener((delta) => {
  if (delta.state && delta.state.current === 'complete') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon48.png',
      title: 'Resume Downloaded',
      message: 'Your customized resume has been downloaded successfully!',
      priority: 2
    });
  }
});
