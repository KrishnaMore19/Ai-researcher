// services/api.ts
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { config } from '@/lib/config';

// Create Axios instance with config
const api: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: config.apiTimeout,
});

// Request interceptor - Add auth token to every request
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Define error response type
interface ErrorResponse {
  detail?: string;
  message?: string;
}

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (typeof window !== 'undefined') {
        try {
          // Try to refresh token
          const refreshToken = localStorage.getItem('refresh_token');
          
          if (refreshToken) {
            const response = await axios.post(`${config.apiBaseUrl}/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token } = response.data;
            localStorage.setItem('auth_token', access_token);

            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            return api(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed - logout user
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user_data');
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
          return Promise.reject(refreshError);
        }
      }
    }

    // Handle other errors
    if (error.response) {
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      
      if (config.showApiErrors) {
        console.error('API Error:', errorMessage);
      }
      
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      if (config.showApiErrors) {
        console.error('Network Error:', error.message);
      }
      return Promise.reject(new Error('Network error. Please check your connection.'));
    } else {
      if (config.showApiErrors) {
        console.error('Error:', error.message);
      }
      return Promise.reject(error);
    }
  }
);

// Export API instance
export default api;

// Helper function for file uploads
export const uploadFile = async (url: string, formData: FormData) => {
  return api.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Helper function for downloads
export const downloadFile = async (url: string, filename: string) => {
  const response = await api.get(url, {
    responseType: 'blob',
  });
  
  const blob = new Blob([response.data]);
  const link = document.createElement('a');
  link.href = window.URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};