/**
 * Axios base client - single source of truth for all API calls.
 * Interceptors handle auth headers, error normalization, and logging.
 */
import axios from 'axios';
import toast from 'react-hot-toast';

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT if present ────────────────────────────────
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('medai_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor: normalize errors ───────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (status === 401) {
      localStorage.removeItem('medai_token');
      toast.error('Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.');
    } else if (status === 403) {
      toast.error('Bạn không có quyền thực hiện thao tác này.');
    } else if (status >= 500) {
      toast.error('Lỗi máy chủ. Vui lòng thử lại sau.');
    }

    // Attach a human-readable message for callers
    error.userMessage = detail || 'Đã xảy ra lỗi. Vui lòng thử lại.';
    return Promise.reject(error);
  },
);

export default client;
