import api from "./client";

export const adminService = {
  // User Management
  getUsers: (params = {}) => api.get("/admin/users/", { params }),
  getUserDetails: (username) => api.get(`/admin/users/${username}/details/`),
  updateUserRole: (username, role) => api.patch(`/admin/users/${username}/role/`, { role }),
  getUserNotes: (username) => api.get(`/admin/users/${username}/notes/`),
  createUserNote: (username, payload) => api.post(`/admin/users/${username}/notes/`, payload),
  toggleBlockUser: (username) => api.post(`/admin/users/${username}/toggle-block/`),
  deleteUser: (username) => api.delete(`/admin/users/${username}/delete/`),
  bulkUserAction: (payload) => api.post("/admin/users/bulk/", payload),
  exportUsers: (params = {}) => api.get("/admin/users/export/", { params, responseType: "blob" }),

  // System & Stats
  getAdminStats: () => api.get("/admin/stats/"),
  getChallengeAnalytics: () => api.get("/admin/analytics/challenges/"),
  getStoreAnalytics: () => api.get("/admin/analytics/store/"),
  getSystemIntegrity: () => api.get("/admin/system/integrity/"),
  getSystemHealth: () => api.get("/admin/system/health/"),
  getUserEngagementAnalytics: () => api.get("/admin/analytics/engagement/"),
  getUltimateAnalytics: () => api.get("/admin/analytics/ultimate/"),

  // Notifications
  sendBroadcast: (message, options = {}) => api.post("/admin/notifications/broadcast/", { message, ...options }),
  getBroadcastHistory: () => api.get("/admin/notifications/history/"),
  resendBroadcast: (requestId) => api.post(`/admin/notifications/history/${requestId}/resend/`),

  // Audit & Reports
  getAuditLogs: (params = {}) => api.get("/admin/audit-logs/", { params }),
  exportAuditLogs: (params = {}) => api.get("/admin/audit-logs/export/", { params, responseType: "blob" }),
  getReports: (params = {}) => api.get("/admin/reports/", { params }),
  createReport: (payload) => api.post("/admin/reports/", payload),
  updateReport: (reportId, payload) => api.patch(`/admin/reports/${reportId}/`, payload),
  
  // Store Admin
  duplicateStoreItem: (itemId) => api.post(`/admin/store/items/${itemId}/duplicate/`),
};
