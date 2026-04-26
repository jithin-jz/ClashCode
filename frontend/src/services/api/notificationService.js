import api from "./client";

export const notificationService = {
  getNotifications: (params = {}) => api.get("/notifications/", { params }),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => api.post("/notifications/mark_all_read/"),
  clearAll: () => api.delete("/notifications/clear_all/"),
  registerFCMToken: (data) => api.post("/notifications/fcm-tokens/", data),
};
