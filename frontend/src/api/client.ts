import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — add access token from memory + CSRF
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const csrf = useAuthStore.getState().getCsrfToken();
  if (csrf) {
    config.headers['X-CSRF-Token'] = csrf;
  }

  return config;
});

// Response interceptor — handle 401 + refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const response = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const { access_token, csrf_token } = response.data;
        useAuthStore.getState().setTokens(access_token, csrf_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        if (csrf_token) {
          originalRequest.headers['X-CSRF-Token'] = csrf_token;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
