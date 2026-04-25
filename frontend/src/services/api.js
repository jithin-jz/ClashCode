import axios from "axios";
import { notify } from "./notification";
import { SLog } from "./logger";

const API_BASE_URL = import.meta.env.VITE_API_URL;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Queue for storing requests that failed while token was refreshing
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

// Handle token refresh on 401 and rate limiting on 429
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle rate limiting (429 Too Many Requests)
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

    // Check for blocked user
    if (
      error.response?.data?.error === "User account is disabled." ||
      error.response?.data?.detail === "User account is disabled."
    ) {
      // If in a popup (OAuth), let the caller handle it (to close popup and notify parent)
      if (window.opener) {
        return Promise.reject(error);
      }

      notify.error("Your account has been blocked by an administrator.", {
        duration: 5000,
      });
      window.location.href = "/login";
      return Promise.reject(error);
    }

    const isRefreshRequest = originalRequest?.url?.includes("/auth/refresh/");
    const isCurrentUserProbe =
      originalRequest?.url?.includes("/profiles/user/");
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isRefreshRequest
    ) {
      // /profiles/user/ is often used as a session probe; avoid forcing refresh loops.
      if (isCurrentUserProbe) {
        return Promise.reject(error);
      }

      // Avoid repeated refresh storms when no valid session exists.
      if (Date.now() < refreshBlockedUntil) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
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

    // Log critical errors to centralized SLog
    if (!error.response || error.response.status >= 500) {
      SLog.error("API critical failure", error, {
        url: originalRequest?.url,
        status: error.response?.status,
        method: originalRequest?.method,
      });
    }

    return Promise.reject(error);
  },
);

// Auth API functions
export const authAPI = {
  // Get OAuth URLs
  getGithubAuthUrl: (state) => api.get("/auth/github/", { params: { state } }),
  getGoogleAuthUrl: (state) => api.get("/auth/google/", { params: { state } }),

  // Handle OAuth callbacks
  githubCallback: (code) => api.post("/auth/github/callback/", { code }),
  googleCallback: (code) => api.post("/auth/google/callback/", { code }),

  // Email OTP endpoints
  requestOtp: (email) => api.post("/auth/otp/request/", { email }),
  verifyOtp: (email, otp) => api.post("/auth/otp/verify/", { email, otp }),

  // User endpoints
  getCurrentUser: () => api.get("/profiles/user/"),
  getUserProfile: (username) => api.get(`/profiles/users/${username}/`),
  logout: () => api.post("/auth/logout/"),
  refreshToken: () => api.post("/auth/refresh/", {}),
  updateProfile: (data) => {
    const config = {};
    if (data instanceof FormData) {
      // Setting Content-Type to undefined allows the browser to set the boundary automatically
      config.headers = { "Content-Type": undefined };
    }
    return api.patch("/profiles/user/update/", data, config);
  },
  followUser: (username) => api.post(`/profiles/users/${username}/follow/`),
  getFollowers: (username) => api.get(`/profiles/users/${username}/followers/`),
  getFollowing: (username) => api.get(`/profiles/users/${username}/following/`),
  redeemReferral: (code) =>
    api.post("/profiles/user/redeem-referral/", { code }),
  deleteAccount: () => api.delete("/auth/user/delete/"),
  getSuggestedUsers: () => api.get("/profiles/users/suggestions/"),
  getContributionHistory: (username) =>
    api.get(`/profiles/users/${username}/stats/contributions/`),

  // Admin endpoints
  getUsers: (params = {}) => api.get("/admin/users/", { params }),
  getUserDetails: (username) => api.get(`/admin/users/${username}/details/`),
  updateUserRole: (username, role) =>
    api.patch(`/admin/users/${username}/role/`, { role }),
  getUserNotes: (username) => api.get(`/admin/users/${username}/notes/`),
  createUserNote: (username, payload) =>
    api.post(`/admin/users/${username}/notes/`, payload),
  toggleBlockUser: (username) =>
    api.post(`/admin/users/${username}/toggle-block/`),
  deleteUser: (username) => api.delete(`/admin/users/${username}/delete/`),
  bulkUserAction: (payload) => api.post("/admin/users/bulk/", payload),
  exportUsers: (params = {}) =>
    api.get("/admin/users/export/", { params, responseType: "blob" }),
  getAdminStats: () => api.get("/admin/stats/"),
  getChallengeAnalytics: () => api.get("/admin/analytics/challenges/"),
  getStoreAnalytics: () => api.get("/admin/analytics/store/"),
  getSystemIntegrity: () => api.get("/admin/system/integrity/"),
  getSystemHealth: () => api.get("/admin/system/health/"),
  sendBroadcast: (message, options = {}) =>
    api.post("/admin/notifications/broadcast/", { message, ...options }),
  getBroadcastHistory: () => api.get("/admin/notifications/history/"),
  resendBroadcast: (requestId) =>
    api.post(`/admin/notifications/history/${requestId}/resend/`),
  getAuditLogs: (params = {}) => api.get("/admin/audit-logs/", { params }),
  exportAuditLogs: (params = {}) =>
    api.get("/admin/audit-logs/", {
      params: { ...params, format: "csv" },
      responseType: "blob",
    }),
  getUserEngagementAnalytics: () => api.get("/admin/analytics/engagement/"),
  getUltimateAnalytics: () => api.get("/admin/analytics/ultimate/"),
  getReports: (params = {}) => api.get("/admin/reports/", { params }),
  createReport: (payload) => api.post("/admin/reports/", payload),
  updateReport: (reportId, payload) =>
    api.patch(`/admin/reports/${reportId}/`, payload),
  duplicateStoreItem: (itemId) =>
    api.post(`/admin/store/items/${itemId}/duplicate/`),
};

// Payment endpoints
export const paymentAPI = {
  createOrder: (amount) => api.post("/payments/create-order/", { amount }),
  verifyPayment: (data) => api.post("/payments/verify-payment/", data),
};

export const storeAPI = {
  getItems: () => api.get("/store/items/"),
  getPurchasedItems: () => api.get("/store/purchased/"),
  purchaseItem: (id) => api.post(`/store/buy/${id}/`),
  buyItem: (id) => api.post(`/store/buy/${id}/`), // Alias
  equipItem: (id) => api.post("/store/equip/", { item_id: id }),
  unequipItem: (category) => api.post("/store/unequip/", { category }),
};

export const postsAPI = {
  getFeed: () => api.get("/posts/"),
  getUserPosts: (username) => api.get(`/posts/?username=${username}`),
  createPost: (data) => {
    const config = {};
    if (data instanceof FormData) {
      config.headers = { "Content-Type": undefined };
    }
    return api.post("/posts/", data, config);
  },
  updatePost: (id, data) => api.patch(`/posts/${id}/`, data),
  deletePost: (id) => api.delete(`/posts/${id}/`),
  toggleLike: (id) => api.post(`/posts/${id}/like/`),
};

export const notificationsAPI = {
  getNotifications: (params = {}) => api.get("/notifications/", { params }),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => api.post("/notifications/mark_all_read/"),
  clearAll: () => api.delete("/notifications/clear_all/"),
  registerFCMToken: (data) => api.post("/notifications/fcm-tokens/", data),
};

export default api;
