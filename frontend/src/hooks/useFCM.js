import { useCallback } from "react";
import useNotificationStore from "../stores/useNotificationStore";
import { notify } from "../services/notification";
import { notificationsAPI } from "../services/api";

/**
 * Hook to manage Firebase Cloud Messaging (FCM) notifications.
 * Handles permission requests, token registration, and foreground message listening.
 */
export const useFCM = () => {
  const registerFCM = useCallback(async () => {
    try {
      const { requestForToken } = await import("../services/firebase");
      const token = await requestForToken();

      if (!token) {
        console.warn("[FCM] No token received from Firebase. Registration aborted.");
        return;
      }

      const store = useNotificationStore.getState();
      
      // Sync with backend
      await notificationsAPI.registerFCMToken({
        token: token,
        device_id: navigator.userAgent,
      });

      const oldToken = store.fcmToken;
      useNotificationStore.setState({ fcmToken: token });

      if (token !== oldToken) {
        notify.success("Push notifications active! 🔔");
      }
    } catch (error) {
      console.error("[FCM] Registration error:", error);
      notify.error("Registration Failed", {
        description: error.message || "Could not sync with backend",
      });
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (typeof Notification === "undefined") return "default";
    try {
      const permission = await Notification.requestPermission();
      useNotificationStore.setState({ permission });
      
      if (permission === "granted") {
        notify.success("Permission Granted!", {
          description: "Setting up real-time secure channel...",
        });
        await registerFCM();
      } else if (permission === "denied") {
        notify.error("Permission Denied", {
          description: "You've blocked notifications. Please enable them in site settings.",
        });
      }
      return permission;
    } catch (error) {
      console.error("Error requesting notification permission:", error);
      return "default";
    }
  }, [registerFCM]);

  const initFCM = useCallback(async () => {
    if (typeof Notification === "undefined") return;

    const store = useNotificationStore.getState();

    if (Notification.permission === "default") {
      if (!store._promptShown) {
        notify.info("Enable Notifications", {
          description: "Stay updated with real-time alerts.",
          action: {
            label: "Allow",
            onClick: () => requestPermission(),
          },
        });
        useNotificationStore.setState({ _promptShown: true });
      }
    } else if (Notification.permission === "granted") {
      await registerFCM();
    }

    // Listener for foreground messages
    if (store._listenerSetup) return;
    useNotificationStore.setState({ _listenerSetup: true });

    try {
      const { onMessageListener } = await import("../services/firebase");
      onMessageListener((payload) => {
        const title = payload.notification?.title || payload.data?.title || "New Notification";
        const body = payload.notification?.body || payload.data?.body || "New alert received.";
        
        const currentStore = useNotificationStore.getState();
        currentStore._showToast(title, body);
        currentStore.scheduleRealtimeSync();
      });
    } catch (error) {
      console.error("Error setting up foreground message listener:", error);
    }
  }, [registerFCM, requestPermission]);

  return { initFCM, requestPermission, registerFCM };
};
