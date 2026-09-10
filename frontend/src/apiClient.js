const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

class ApiClient {
  constructor() {
    this.isRefreshing = false;
    this.refreshSubscribers = [];
  }

  subscribeTokenRefresh(cb) {
    this.refreshSubscribers.push(cb);
  }

  onRefreshed(token) {
    this.refreshSubscribers.map(cb => cb(token));
    this.refreshSubscribers = [];
  }

  async fetchWithAuth(url, options = {}) {
    let token = localStorage.getItem('access_token');
    let headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Check if body is FormData, if so let browser set Content-Type
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const finalUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
    let response = await fetch(finalUrl, {
      ...options,
      headers,
    });

    if (response.status === 401 && !options._retry) {
      options._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        window.location.href = '/login';
        return response;
      }

      if (this.isRefreshing) {
        return new Promise((resolve) => {
          this.subscribeTokenRefresh((newToken) => {
            headers['Authorization'] = `Bearer ${newToken}`;
            resolve(fetch(finalUrl, { ...options, headers }));
          });
        });
      }

      this.isRefreshing = true;
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!res.ok) {
          throw new Error('Refresh failed');
        }

        const data = await res.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        this.isRefreshing = false;
        this.onRefreshed(data.access_token);

        headers['Authorization'] = `Bearer ${data.access_token}`;
        return fetch(finalUrl, { ...options, headers });
      } catch (error) {
        this.isRefreshing = false;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return response;
      }
    }

    return response;
  }

  async request(url, options = {}) {
    const response = await this.fetchWithAuth(url, options);
    if (!response.ok) {
      let errorData;
      try {
         errorData = await response.json();
      } catch (e) {
         errorData = await response.text();
      }
      throw { status: response.status, data: errorData };
    }
    
    // For 204 No Content
    if (response.status === 204) return null;
    return await response.json();
  }

  get(url, options = {}) {
    return this.request(url, { ...options, method: 'GET' });
  }

  post(url, body, options = {}) {
    return this.request(url, { ...options, method: 'POST', body: JSON.stringify(body) });
  }

  put(url, body, options = {}) {
    return this.request(url, { ...options, method: 'PUT', body: JSON.stringify(body) });
  }

  delete(url, options = {}) {
    return this.request(url, { ...options, method: 'DELETE' });
  }
}

export default new ApiClient();
