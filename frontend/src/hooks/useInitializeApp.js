import { useEffect, useRef } from "react";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import useNotificationStore from "../stores/useNotificationStore";
import { useNotificationSocket } from "./useNotificationSocket";
import { useFCM } from "./useFCM";

/**
 * Custom hook to initialize authentication and notifications.
 */
export const useInitializeApp = () => {
  const { checkAuth, user, authLoading } = useAuthStore(
    useShallow((s) => ({
      checkAuth: s.checkAuth,
      user: s.user,
      authLoading: s.loading,
    })),
  );
  
  const { initFCM } = useFCM();
  const { connectWS } = useNotificationSocket();

  const authInitRef = useRef(false);
  const notifInitUserIdRef = useRef(null);

  useEffect(() => {
    if (authInitRef.current) return;
    authInitRef.current = true;
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    const userId = user?.id;
    if (!userId) {
      notifInitUserIdRef.current = null;
      return;
    }
    if (notifInitUserIdRef.current !== userId) {
      notifInitUserIdRef.current = userId;
      
      // Modular initialization
      useNotificationStore.setState({ wsShouldReconnect: true });
      initFCM();
      connectWS();
    }
  }, [user, initFCM, connectWS]);

  return { user, authLoading };
};
