import axios from "axios";

let API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8002";
if (API_BASE_URL.includes(":8000")) {
  API_BASE_URL = API_BASE_URL.replace(":8000", ":8002");
}

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
