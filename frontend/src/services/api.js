import axios from 'axios';

const baseURL = 'http://192.168.175.242:8000';

console.log('API Base URL:', baseURL); // Debug log

const api = axios.create({
  baseURL: baseURL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
