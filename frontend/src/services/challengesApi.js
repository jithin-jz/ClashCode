import api from "./api";
import { socketService } from "./socketService";

let aiAnalyzeUnavailable = false;
let aiAnalyzeUnavailableUntil = 0;
const AI_TASK_POLL_INTERVAL_MS = 2000; // Increased interval for fallback
const AI_TASK_POLL_TIMEOUT_MS = 90000;

/**
 * Waits for an AI task result using WebSockets with a polling fallback.
 */
const waitForAITaskResult = async (taskId) => {
  try {
    // Primary: Try WebSocket
    return await socketService.waitForTask(taskId, AI_TASK_POLL_TIMEOUT_MS);
  } catch (err) {
    // If WS times out or fails, fallback to polling
    console.warn("[API] WebSocket failed, falling back to polling for taskId:", taskId);
    
    const startedAt = Date.now();
    while (Date.now() - startedAt < AI_TASK_POLL_TIMEOUT_MS) {
      const response = await api.get(`/challenges/ai-tasks/${taskId}/status/`);
      const payload = response.data || {};

      if (payload.status === "success") {
        return payload.result || {};
      }

      if (payload.status === "failed") {
        const pollErr = new Error(payload.error || "AI task failed (Poll)");
        pollErr.response = { status: 503, data: payload };
        throw pollErr;
      }

      await new Promise((resolve) => setTimeout(resolve, AI_TASK_POLL_INTERVAL_MS));
    }

    const timeoutErr = new Error("AI task timed out (Poll Fallback)");
    timeoutErr.response = { status: 504 };
    throw timeoutErr;
  }
};

export const challengesApi = {
  getAll: async () => {
    const response = await api.get("/challenges/");
    return response.data;
  },
  getBySlug: async (slug) => {
    const response = await api.get(`/challenges/${slug}/`);
    return response.data;
  },
  submit: async (slug, code) => {
    const payload = { code };
    const response = await api.post(`/challenges/${slug}/submit/`, payload);
    return response.data;
  },
  execute: async (slug, code) => {
    const response = await api.post(`/challenges/${slug}/execute/`, { code });
    return response.data;
  },
  purchaseAIHint: async (slug) => {
    const response = await api.post(`/challenges/${slug}/purchase_ai_assist/`);
    return response.data;
  },
  getAIHint: async (slug, data) => {
    const response = await api.post(`/challenges/${slug}/ai-hint/`, data);
    if (response.status === 202 && response.data?.task_id) {
      return waitForAITaskResult(response.data.task_id);
    }
    return response.data;
  },
  aiAnalyze: async (slug, user_code) => {
    if (aiAnalyzeUnavailable && Date.now() < aiAnalyzeUnavailableUntil) {
      const err = new Error("AI analyze endpoint unavailable");
      err.isAnalyzeUnavailable = true;
      err.response = { status: 404 };
      throw err;
    }
    // Cooldown expired: allow retry.
    if (aiAnalyzeUnavailable && Date.now() >= aiAnalyzeUnavailableUntil) {
      aiAnalyzeUnavailable = false;
    }

    const payload = { user_code };
    const path = `/challenges/${slug}/ai-analyze/`;

    try {
      const response = await api.post(path, payload);
      if (response.status === 202 && response.data?.task_id) {
        return waitForAITaskResult(response.data.task_id);
      }
      return response.data;
    } catch (err) {
      const statusCode = err?.response?.status;
      if (statusCode === 404) {
        aiAnalyzeUnavailable = true;
        aiAnalyzeUnavailableUntil = Date.now() + 60000; // retry backend after 60s
      }
      throw err;
    }
  },
  create: async (data) => {
    const response = await api.post("/challenges/", data);
    return response.data;
  },
  update: async (slug, data) => {
    const response = await api.patch(`/challenges/${slug}/`, data);
    return response.data;
  },
  delete: async (slug) => {
    const response = await api.delete(`/challenges/${slug}/`);
    return response.data;
  },

  // Certificate APIs
  getMyCertificate: async () => {
    const response = await api.get("/certificates/my_certificate/");
    const data = response.data;
    return data?.certificate_id ? data : null;
  },
  verifyCertificate: async (certificateId) => {
    const response = await api.get(`/certificates/verify/${certificateId}/`);
    return response.data;
  },
  checkCertificateEligibility: async () => {
    const response = await api.get("/certificates/check_eligibility/");
    return response.data;
  },
};
