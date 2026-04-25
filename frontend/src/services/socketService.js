 * Manages WebSocket connections for real-time task updates.
 * Replaces polling logic to reduce server load and latency.
 */
import { SLog } from "./logger";

const getSocketUrl = () => {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
  const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
  const base = apiUrl.replace(/^https?:\/\//, "").replace(/\/api\/v1\/?$/, "");
  return `${wsProtocol}://${base}/ws/tasks/`;
};

class SocketService {
  constructor() {
    this.url = getSocketUrl();
    this.socket = null;
    this.listeners = new Map(); // taskId -> { resolve, reject, timeout }
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.isConnected = false;
  }

  connect() {
    if (this.socket || this.isConnected) return;

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log("[WS] Connected to", this.url);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        // Resubscribe to any pending tasks if necessary (or the server might handle it)
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("[WS] Message:", data);

          // The backend publishes { type, task_id, task_type, result: { ok, payload, error, status_code } }
          if (data.task_id && this.listeners.has(data.task_id)) {
            const { resolve, reject, timeout } = this.listeners.get(data.task_id);
            const result = data.result || {};

            if (result.ok) {
              clearTimeout(timeout);
              this.listeners.delete(data.task_id);
              resolve(result.payload || {});
            } else {
              clearTimeout(timeout);
              this.listeners.delete(data.task_id);
              const err = new Error(result.error || "AI task failed");
              err.response = { status: result.status_code || 500, data: result };
              reject(err);
            }
          }
        } catch (err) {
          console.error("[WS] Failed to parse message:", err);
          SLog.error("WS parse error", err, { raw: event.data });
        }
      };

      this.socket.onclose = (e) => {
        this.isConnected = false;
        this.socket = null;
        console.warn(`[WS] Closed: ${e.code}. Reconnecting...`);
        this.handleReconnect();
      };

      this.socket.onerror = (err) => {
        console.error("[WS] Error:", err);
        SLog.error("WS connection error", err, { url: this.url });
        this.socket.close();
      };
    } catch (err) {
      console.error("[WS] Connection failed:", err);
      this.handleReconnect();
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => this.connect(), delay);
    }
  }

  waitForTask(taskId, timeoutMs = 90000) {
    // Ensure connected
    this.connect();

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (this.listeners.has(taskId)) {
          this.listeners.delete(taskId);
          const err = new Error("AI task timed out (WS)");
          err.response = { status: 504 };
          SLog.warn("WS task timeout", { taskId, timeoutMs });
          reject(err);
        }
      }, timeoutMs);

      this.listeners.set(taskId, { resolve, reject, timeout });

      // If already connected, we could send a subscription message if the backend requires it
      if (this.isConnected) {
        this.socket.send(JSON.stringify({ action: "subscribe", task_id: taskId }));
      }
    });
  }
}

export const socketService = new SocketService();
