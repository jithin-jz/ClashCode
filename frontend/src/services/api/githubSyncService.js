import api from "./client";

/**
 * GitHub Sync API Service
 *
 * Handles all communication with the /api/github-sync/ endpoints.
 */

const githubSyncService = {
  /**
   * Get the OAuth URL to redirect the user to GitHub for authorization.
   */
  getConnectUrl: () => api.get("/github-sync/connect/url/"),

  /**
   * Exchange the OAuth code from GitHub callback for a connection.
   * @param {string} code - Authorization code from GitHub redirect
   */
  connect: (code) => api.post("/github-sync/connect/", { code }),

  /**
   * Get the current GitHub connection status.
   */
  getConnection: () => api.get("/github-sync/connection/"),

  /**
   * Update connection settings (enable/disable, repo name).
   * @param {Object} data - { is_enabled?: boolean, repo_name?: string }
   */
  updateConnection: (data) => api.patch("/github-sync/connection/", data),

  /**
   * Disconnect GitHub (removes the connection entirely).
   */
  disconnect: () => api.delete("/github-sync/connection/"),

  /**
   * Get push history (last 50 pushes).
   */
  getHistory: () => api.get("/github-sync/history/"),

  /**
   * Retry a failed push.
   * @param {number} logId - The push log ID to retry
   */
  retryPush: (logId) => api.post(`/github-sync/retry/${logId}/`),

  /**
   * Verify the stored token is still valid.
   */
  verify: () => api.post("/github-sync/verify/"),
};

export default githubSyncService;
