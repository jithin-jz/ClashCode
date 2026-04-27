import axios from "axios";
import { notify } from "../notification";
import { SLog } from "../logger";
import { isBoneyard } from "../../utils/isBoneyard";

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

// 1. Request Interceptor: Auth injection and Crawler short-circuiting
api.interceptors.request.use(async (config) => {
  if (isBoneyard()) {
    // List of endpoints crawlers are allowed to hit (mostly public or mockable)
    const publicEndpoints = ["/challenges/", "/profiles/user/", "/health/"];
    const isPublic = publicEndpoints.some(ep => config.url?.includes(ep));
    
    if (!isPublic) {
      // Cancel the request to prevent backend 401/403/429 spam
      const controller = new AbortController();
      config.signal = controller.signal;
      controller.abort("CRAWLER_SKIP");
      return config;
    }
  }
  return config;
}, (error) => Promise.reject(error));

// Cross-tab synchronization using BroadcastChannel
const refreshChannel = typeof window !== "undefined" ? new BroadcastChannel("auth_refresh_channel") : null;

if (refreshChannel) {
  refreshChannel.onmessage = (event) => {
    const { type, error, blockedUntil } = event.data;
    if (type === "REFRESH_STARTED") {
      isRefreshing = true;
    } else if (type === "REFRESH_COMPLETED") {
      isRefreshing = false;
      refreshBlockedUntil = 0;
      processQueue(null, true);
    } else if (type === "REFRESH_FAILED") {
      isRefreshing = false;
      refreshBlockedUntil = blockedUntil || Date.now() + 30000;
      processQueue(error || new Error("Refresh failed in another tab"), null);
    }
  };
}

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
      const isRefreshRequest = originalRequest?.url?.includes("/auth/refresh/");
      if (isRefreshRequest) {
        // If refresh itself is rate limited, block all refresh attempts for a while
        refreshBlockedUntil = Date.now() + 60000;
        isRefreshing = false;
        if (refreshChannel) {
          refreshChannel.postMessage({ type: "REFRESH_FAILED", blockedUntil: refreshBlockedUntil });
        }
        processQueue(error, null);
        
        if (window.location.pathname !== "/login") {
           window.location.href = "/login";
        }
        return Promise.reject(error);
      }

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
    
    const isCrawler = isBoneyard();

    if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
      if (isCurrentUserProbe || isCrawler) {
        // Crawlers/Boneyard should not trigger refresh flows
        return Promise.reject(error);
      }
      
      // Check if we are globally blocked or currently refreshing
      const now = Date.now();
      if (now < refreshBlockedUntil) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => api(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;
      
      if (refreshChannel) {
        refreshChannel.postMessage({ type: "REFRESH_STARTED" });
      }

      try {
        // Use a clean axios instance for refresh to avoid interceptor complications
        await axios.post(`${API_BASE_URL}/auth/refresh/`, {}, { withCredentials: true });
        
        refreshBlockedUntil = 0;
        isRefreshing = false;
        
        if (refreshChannel) {
          refreshChannel.postMessage({ type: "REFRESH_COMPLETED" });
        }
        
        processQueue(null, true);
        return api(originalRequest);
      } catch (err) {
        // More aggressive blocking if refresh fails to prevent rapid loops
        refreshBlockedUntil = Date.now() + 15000;
        isRefreshing = false;
        
        if (refreshChannel) {
          refreshChannel.postMessage({ type: "REFRESH_FAILED", blockedUntil: refreshBlockedUntil });
        }
        
        processQueue(err, null);
        
        // Only redirect if not already on login and not a crawler
        if (window.location.pathname !== "/login" && !isCrawler) {
          window.location.href = "/login";
        }
        return Promise.reject(err);
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

