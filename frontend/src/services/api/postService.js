import api from "./client";

export const postService = {
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
