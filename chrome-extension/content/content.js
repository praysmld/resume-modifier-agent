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
    // Wait for DOM to load and then inject button
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => injectButton(targetSelector));
    } else {
      injectButton(targetSelector);
    }
  }

  function injectButton(selector) {
    // Use MutationObserver to handle dynamically loaded content
    const observer = new MutationObserver((mutations, obs) => {
      const container = document.querySelector(selector);
      if (container && !document.getElementById('resume-modifier-btn')) {
        createButton(container);
        obs.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Also try immediately in case content is already loaded
    const container = document.querySelector(selector);
    if (container && !document.getElementById('resume-modifier-btn')) {
      createButton(container);
      observer.disconnect();
    }
  }

  function createButton(container) {
    const button = document.createElement('button');
    button.id = 'resume-modifier-btn';
    button.className = 'resume-modifier-inject-btn';
    button.innerHTML = '📄 Generate Custom Resume';

    button.addEventListener('click', async () => {
      // Open extension popup programmatically or show notification
      chrome.runtime.sendMessage({ action: 'generateResume' }, (response) => {
        if (chrome.runtime.lastError) {
          console.log('Extension popup will open when you click the icon');
          // Show a notification since we can't programmatically open popup in Manifest V3
          button.textContent = '✓ Click extension icon to continue';
          button.style.background = '#16a34a';
          setTimeout(() => {
            button.innerHTML = '📄 Generate Custom Resume';
            button.style.background = '';
          }, 3000);
        }
      });
    });

    container.insertBefore(button, container.firstChild);
  }
})();
