import { useEffect, useRef } from "react";
import useNotificationStore from "../stores/useNotificationStore";
import { buildWebSocketUrl } from "../utils/websocketUrl";

/**
 * Hook to manage the Notification WebSocket connection.
 * Handles auto-reconnect and message routing to the store.
 */
export const useNotificationSocket = () => {
  const { wsShouldReconnect, isWSConnected, set, get } = useNotificationStore((s) => ({
    wsShouldReconnect: s.wsShouldReconnect,
    isWSConnected: s.isWSConnected,
    set: s.set,
    get: s.get || (() => s), // Fallback if get is not in slice
  }));
  
  const socketRef = useRef(null);

  const connectWS = () => {
    if (!useNotificationStore.getState().wsShouldReconnect) return;
    
    if (socketRef.current) {
      if (
        socketRef.current.readyState === WebSocket.OPEN ||
        socketRef.current.readyState === WebSocket.CONNECTING
      ) {
        return;
      }
      socketRef.current.close();
    }

    const WS_URL = buildWebSocketUrl({
      explicitUrl:
        import.meta.env.VITE_NOTIFICATIONS_WS_URL ||
        import.meta.env.VITE_WS_NOTIFICATIONS_URL,
      apiUrl: import.meta.env.VITE_API_URL,
      defaultPath: "/ws/notifications",
      legacyPaths: ["/notifications", "/ws"],
      label: "Notifications",
      token: localStorage.getItem("clashcode_access_token"),
    });

    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      useNotificationStore.setState({ isWSConnected: true, socket: socket });
      console.info("[Notifications] WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const store = useNotificationStore.getState();
        if (data.type === "notification") {
          store._showToast(data.title, data.body);
        } else if (data.type === "mention") {
          store._showToast(
            "You were mentioned",
            `@${data.sender} mentioned you in ${data.room}`
          );
        }
      } catch (err) {
        console.error("[Notifications] Failed to parse socket message", err);
      }
    };

    socket.onclose = () => {
      useNotificationStore.setState({ isWSConnected: false, socket: null });
      if (useNotificationStore.getState().wsShouldReconnect) {
        console.warn("[Notifications] WebSocket closed. Retrying in 5s...");
        setTimeout(() => connectWS(), 5000);
      }
    };

    socket.onerror = (error) => {
      console.error("[Notifications] WebSocket error:", error);
      socket.close();
    };
  };

  useEffect(() => {
    if (useNotificationStore.getState().wsShouldReconnect && !isWSConnected) {
      connectWS();
    }
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [isWSConnected]);

  return { connectWS };
};
