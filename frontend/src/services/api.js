import api from "./api/client";
import { authService } from "./api/authService";
import { userService } from "./api/userService";
import { postService } from "./api/postService";
import { storeService } from "./api/storeService";
import { adminService } from "./api/adminService";
import { notificationService } from "./api/notificationService";
import { paymentService } from "./api/paymentService";

// Export the client for direct access if needed
export default api;

// Legacy names for backward compatibility during migration
export const authAPI = {
  ...authService,
  ...userService,
  ...adminService,
};

export const paymentAPI = paymentService;
export const storeAPI = storeService;
export const postsAPI = postService;
export const notificationsAPI = notificationService;
