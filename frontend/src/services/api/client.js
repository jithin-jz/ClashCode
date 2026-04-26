import axios from "axios";
import { notify } from "../notification";
import { SLog } from "../logger";

const API_BASE_URL = import.meta.env.VITE_API_URL;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor state
let isRefreshing = false;
let failedQueue = [];
let refreshBlockedUntil = 0;
let lastRateLimitNoticeAt = 0;

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor for Token Refresh and Error Handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 1. Handle Rate Limiting (429)
    if (error.response?.status === 429) {
      const now = Date.now();
      if (now - lastRateLimitNoticeAt > 3000) {
        const retryAfter = error.response.headers["retry-after"];
        const message = retryAfter
          ? `Too many requests. Please wait ${retryAfter} seconds.`
          : "Too many requests. Please slow down.";
        notify.error(message, { duration: 4000 });
        lastRateLimitNoticeAt = now;
      }
      return Promise.reject(error);
    }

    // 2. Handle Disabled/Blocked User
    const errorData = error.response?.data;
    const errorMessage = errorData?.error || errorData?.detail;

    if (errorMessage === "User account is disabled.") {
      if (window.opener) return Promise.reject(error);
      notify.error("Your account has been blocked by an administrator.", { duration: 5000 });
      window.location.href = "/login";
      return Promise.reject(error);
    }

    // 3. Handle Token Refresh (401)
    const isRefreshRequest = originalRequest?.url?.includes("/auth/refresh/");
    const isCurrentUserProbe = originalRequest?.url?.includes("/profiles/user/");
    
    if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
      if (isCurrentUserProbe) return Promise.reject(error);
      if (Date.now() < refreshBlockedUntil) return Promise.reject(error);

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => api(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await api.post(`/auth/refresh/`, {});
        refreshBlockedUntil = 0;
        processQueue(null, true);
        return api(originalRequest);
      } catch (err) {
        refreshBlockedUntil = Date.now() + 30000;
        processQueue(err, null);
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    // 4. Log Server Errors (500+)
    if (!error.response || error.response.status >= 500) {
      const errorDetail = errorData?.error || errorData?.detail || error.message;
      const requestId = errorData?.request_id;

      SLog.error(`API failure: ${errorDetail}`, error, {
        url: originalRequest?.url,
        status: error.response?.status,
        method: originalRequest?.method,
        requestId: requestId,
      });

      if (requestId) {
        notify.error(`A server error occurred. Support ID: ${requestId}`);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
