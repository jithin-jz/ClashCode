import api from "./api";

/**
 * Tasks API Service
 * Handles Celery task monitoring and status checks for the Admin Dashboard.
 */
export const tasksApi = {
  /**
   * List recent task results from the database.
   * @param {Object} params - Query parameters (limit, status, task_name)
   */
  getResults: async (params = {}) => {
    const response = await api.get("/tasks/results/", { params });
    return response.data;
  },

  /**
   * Check the status of a specific task.
   * @param {string} taskId - The unique ID of the task
   */
  getStatus: async (taskId) => {
    const response = await api.get(`/tasks/${taskId}/status/`);
    return response.data;
  },
};
