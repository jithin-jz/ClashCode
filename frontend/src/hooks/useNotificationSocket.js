import { useEffect, useRef, useCallback, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import useNotificationStore from "../stores/useNotificationStore";
import { buildWebSocketUrl } from "../utils/websocketUrl";
import { isBoneyard } from "../utils/isBoneyard";

/**
 * Hook to manage the Notification WebSocket connection.
 * Handles auto-reconnect and message routing to the store.
 */
export const useNotificationSocket = (userId) => {
  const { isWSConnected } = useNotificationStore(
    useShallow((s) => ({
      isWSConnected: s.isWSConnected,
    })),
  );
  
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const activeUserIdRef = useRef(null);

  const connectWS = useCallback((id) => {
    if (!id) return;
    if (isBoneyard()) return;
    
    // Prevent double connection for same user
    if (socketRef.current) {
      if (
        socketRef.current.readyState === WebSocket.OPEN ||
        socketRef.current.readyState === WebSocket.CONNECTING
      ) {
        if (activeUserIdRef.current === id) return;
        // If ID changed, close old one
        socketRef.current.close();
      }
    }

    activeUserIdRef.current = id;

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

    console.info(`[Notifications] Connecting for user ${id}...`);
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

    socket.onclose = (event) => {
      // Only reconnect if this is still the active socket ref
      if (socketRef.current === socket) {
        useNotificationStore.setState({ isWSConnected: false, socket: null });
        socketRef.current = null;
        
        if (activeUserIdRef.current) {
          console.warn("[Notifications] WebSocket closed. Reconnecting in 5s...", event.code);
          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWS(activeUserIdRef.current);
          }, 5000);
        }
      }
    };

    socket.onerror = (error) => {
      console.error("[Notifications] WebSocket error:", error);
      socket.close();
    };
  }, []);

  useEffect(() => {
    if (userId) {
      connectWS(userId);
    } else {
      // User logged out
      activeUserIdRef.current = null;
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    }

    return () => {
      // We do NOT close the socket here anymore unless the component unmounts
      // and we want to be sure. But if we use a global store, maybe we want it to persist?
      // Actually, unmount of AppContent happens on full reload, so it's fine.
    };
  }, [userId, connectWS]);

  // Handle unmount specifically
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, []);

  return useMemo(() => ({ connectWS }), [connectWS]);
};
