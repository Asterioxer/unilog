import axios from "axios";

const defaultProdUrl = "https://unilog-w9oe.onrender.com";
const isLocalhost = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
const rawApiUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || (isLocalhost ? "http://127.0.0.1:8002" : defaultProdUrl);

export const API_BASE_URL = rawApiUrl.includes("127.0.0.1") || rawApiUrl.includes("localhost") 
  ? rawApiUrl.replace(":8000", ":8002")
  : rawApiUrl.replace(/\/$/, "");




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
