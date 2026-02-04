/**
 * WorkSynapse API Client
 * ======================
 * Axios-based HTTP client with JWT auth, anti-replay headers,
 * request/response interceptors, and error handling.
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { v4 as uuidv4 } from 'uuid';
import CryptoJS from 'crypto-js';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';
const SECRET_KEY = import.meta.env.VITE_SECRET_KEY || '';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Auth token storage
let authToken: string | null = null;

// Set auth token
export const setAuthToken = (token: string) => {
    authToken = token;
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

// Clear auth token
export const clearAuthToken = () => {
    authToken = null;
    delete apiClient.defaults.headers.common['Authorization'];
};

// Get current auth token
export const getAuthToken = (): string | null => authToken;

/**
 * Generate HMAC-SHA256 signature for anti-replay protection
 */
function generateSignature(
    method: string,
    path: string,
    body: string,
    timestamp: string,
    nonce: string
): string {
    const message = `${method.toUpperCase()}${path}${body}${timestamp}${nonce}`;
    return CryptoJS.HmacSHA256(message, SECRET_KEY).toString(CryptoJS.enc.Hex);
}

// Request interceptor
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // Add timestamp header
        const timestamp = Math.floor(Date.now() / 1000).toString();
        config.headers['X-TIMESTAMP'] = timestamp;

        // Add unique nonce
        const nonce = uuidv4();
        config.headers['X-NONCE'] = nonce;

        // Add API key if configured
        if (API_KEY) {
            config.headers['X-API-KEY'] = API_KEY;

            // Generate signature for anti-replay (if secret key is configured)
            if (SECRET_KEY) {
                const body = config.data ? JSON.stringify(config.data) : '';
                const path = config.url || '';
                const method = config.method || 'GET';
                const signature = generateSignature(method, path, body, timestamp, nonce);
                config.headers['X-SIGNATURE'] = signature;
            }
        }

        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 Unauthorized - try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('worksynapse-refresh-token');
                if (refreshToken) {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token } = response.data;

                    localStorage.setItem('worksynapse-access-token', access_token);
                    localStorage.setItem('worksynapse-refresh-token', refresh_token);
                    setAuthToken(access_token);

                    // Retry original request
                    originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed, redirect to login
                localStorage.removeItem('worksynapse-access-token');
                localStorage.removeItem('worksynapse-refresh-token');
                localStorage.removeItem('worksynapse-user');
                clearAuthToken();

                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
            }
        }

        // Handle other errors
        const errorMessage = extractErrorMessage(error);
        console.error('API Error:', errorMessage);

        return Promise.reject(error);
    }
);

/**
 * Extract user-friendly error message from axios error
 */
function extractErrorMessage(error: AxiosError): string {
    if (error.response?.data) {
        const data = error.response.data as any;
        if (data.detail) {
            return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        }
        if (data.message) {
            return data.message;
        }
        if (data.error) {
            return data.error;
        }
    }

    if (error.message) {
        return error.message;
    }

    return 'An unexpected error occurred';
}

// Export utility functions
export const api = {
    get: <T = any>(url: string, config?: any) =>
        apiClient.get<T>(url, config).then(res => res.data),

    post: <T = any>(url: string, data?: any, config?: any) =>
        apiClient.post<T>(url, data, config).then(res => res.data),

    put: <T = any>(url: string, data?: any, config?: any) =>
        apiClient.put<T>(url, data, config).then(res => res.data),

    patch: <T = any>(url: string, data?: any, config?: any) =>
        apiClient.patch<T>(url, data, config).then(res => res.data),

    delete: <T = any>(url: string, config?: any) =>
        apiClient.delete<T>(url, config).then(res => res.data),
};

export default apiClient;
