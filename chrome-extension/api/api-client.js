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
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
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
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
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
