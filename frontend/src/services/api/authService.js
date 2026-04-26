import api from "./client";

export const authService = {
  // OAuth Endpoints
  getGithubAuthUrl: (state) => api.get("/auth/github/", { params: { state } }),
  getGoogleAuthUrl: (state) => api.get("/auth/google/", { params: { state } }),
  githubCallback: (code) => api.post("/auth/github/callback/", { code }),
  googleCallback: (code) => api.post("/auth/google/callback/", { code }),

  // OTP Endpoints
  requestOtp: (email) => api.post("/auth/otp/request/", { email }),
  verifyOtp: (email, otp) => api.post("/auth/otp/verify/", { email, otp }),

  // Session Endpoints
  logout: () => api.post("/auth/logout/"),
  refreshToken: () => api.post("/auth/refresh/", {}),
  deleteAccount: () => api.delete("/auth/user/delete/"),
};
