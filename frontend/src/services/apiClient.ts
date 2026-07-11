import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds
});

// Response interceptor to format errors standardizing on the backend error model
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorData = error.response?.data;
    // Map backend standardized error model to client
    if (errorData && errorData.success === false && errorData.error) {
      return Promise.reject(errorData.error);
    }
    return Promise.reject({
      code: error.code || "UNKNOWN_ERROR",
      message: error.message || "An unexpected error occurred",
      details: error.response?.data || {},
    });
  }
);
