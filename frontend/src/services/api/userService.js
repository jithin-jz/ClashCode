import api from "./client";

export const userService = {
  getCurrentUser: () => api.get("/profiles/user/"),
  getUserProfile: (username) => api.get(`/profiles/users/${username}/`),
  updateProfile: (data) => {
    const config = {};
    if (data instanceof FormData) {
      config.headers = { "Content-Type": undefined };
    }
    return api.patch("/profiles/user/update/", data, config);
  },
  followUser: (username) => api.post(`/profiles/users/${username}/follow/`),
  getFollowers: (username) => api.get(`/profiles/users/${username}/followers/`),
  getFollowing: (username) => api.get(`/profiles/users/${username}/following/`),
  redeemReferral: (code) => api.post("/profiles/user/redeem-referral/", { code }),
  getSuggestedUsers: () => api.get("/profiles/users/suggestions/"),
  getContributionHistory: (username) => api.get(`/profiles/users/${username}/stats/contributions/`),
  uploadMedia: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/profiles/media/upload/", formData, {
      headers: { "Content-Type": undefined },
    });
  },
};
