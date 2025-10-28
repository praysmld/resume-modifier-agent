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
