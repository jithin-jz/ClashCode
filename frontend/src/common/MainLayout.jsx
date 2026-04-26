import React, { useState, useEffect, useCallback, useMemo, memo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import useChallengesStore from "../stores/useChallengesStore";
import useChatStore from "../stores/useChatStore";
import {
  HomeTopNav,
  ChatDrawer,
  LeaderboardDrawer,
  NotificationDrawer,
  DailyCheckInModal,
  SiteFooter,
} from "../home";
import { useDailyReward } from "../hooks/useDailyReward";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";

/**
 * MainLayout — Single persistent layout wrapping all authenticated routes.
 */
const MainLayout = memo(({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  // ---- Zustand Selectors (shallow) ----
  const { user, userId, logout } = useAuthStore(
    useShallow((s) => ({ user: s.user, userId: s.user?.id, logout: s.logout })),
  );
  const { apiLevels, fetchChallenges, ensureFreshChallenges } =
    useChallengesStore(
      useShallow((s) => ({
        apiLevels: s.challenges,
        fetchChallenges: s.fetchChallenges,
        ensureFreshChallenges: s.ensureFreshChallenges,
      })),
    );

  const { isChatOpen, setChatOpen } = useChatStore(
    useShallow((s) => ({
      isChatOpen: s.isChatOpen,
      setChatOpen: s.setChatOpen,
    })),
  );

  // ---- Local UI State & Hooks ----
  const [isLeaderboardOpen, setLeaderboardOpen] = useState(false);
  const [isNotificationOpen, setNotificationOpen] = useState(false);
  
  const { 
    checkInOpen, 
    setCheckInOpen, 
    hasUnclaimedReward, 
    handleClaimReward 
  } = useDailyReward(userId);

  useKeyboardShortcuts(user, navigate, setChatOpen, setLeaderboardOpen);

  // ---- Derived state (memoised) ----
  const hideNav = useMemo(
    () =>
      location.pathname.startsWith("/level/") ||
      location.pathname.startsWith("/admin/"),
    [location.pathname],
  );
  const showFooter = useMemo(() => {
    const footerPaths = [
      "/", "/home", "/profile", "/marketplace", "/store", "/buy-xp", "/shop", "/game"
    ];
    return footerPaths.includes(location.pathname) || location.pathname.startsWith("/profile/");
  }, [location.pathname]);

  // ---- Data Fetching ----
  useEffect(() => {
    if (userId) fetchChallenges();
  }, [userId, fetchChallenges]);

  useEffect(() => {
    if (!userId) return undefined;
    const refreshIfNeeded = () => ensureFreshChallenges(20000);
    const onVisible = () => document.visibilityState === "visible" && refreshIfNeeded();

    window.addEventListener("focus", refreshIfNeeded);
    document.addEventListener("visibilitychange", onVisible);

    const intervalId = setInterval(() => {
      if (document.visibilityState === "visible") refreshIfNeeded();
    }, 30000);

    return () => {
      window.removeEventListener("focus", refreshIfNeeded);
      document.removeEventListener("visibilitychange", onVisible);
      clearInterval(intervalId);
    };
  }, [userId, ensureFreshChallenges]);

  // ---- Stable Callbacks ----
  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/");
  }, [logout, navigate]);

  const handleCloseNotification = useCallback(() => setNotificationOpen(false), []);
  const handleCloseCheckIn = useCallback(() => setCheckInOpen(false), []);

  // ---- Early exit for gameplay screens ----
  if (hideNav) return children;

  return (
    <div className="relative min-h-full bg-black text-foreground selection:bg-primary/20 ds-spotlight">
      <div className="fixed inset-0 z-0 pointer-events-none bg-black app-grid-overlay opacity-[0.03]" />
      <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.02),transparent_100%)]" />

      <div className="relative z-10 flex min-h-full flex-col">
        <HomeTopNav
          user={user}
          levels={apiLevels}
          handleLogout={handleLogout}
          setChatOpen={setChatOpen}
          isChatOpen={isChatOpen}
          setCheckInOpen={setCheckInOpen}
          setLeaderboardOpen={setLeaderboardOpen}
          setNotificationOpen={setNotificationOpen}
          hasUnclaimedReward={hasUnclaimedReward}
        />

        <ChatDrawer isOpen={isChatOpen} setOpen={setChatOpen} user={user} />
        <LeaderboardDrawer
          isLeaderboardOpen={isLeaderboardOpen}
          setLeaderboardOpen={setLeaderboardOpen}
        />
        <NotificationDrawer
          isOpen={isNotificationOpen}
          onClose={handleCloseNotification}
        />
        <DailyCheckInModal
          isOpen={checkInOpen}
          onClose={handleCloseCheckIn}
          onClaim={handleClaimReward}
        />

        <main className="flex-1 pt-14">{children}</main>

        {showFooter && (
          <div className={user ? "pb-16 sm:pb-0" : ""}>
            <SiteFooter />
          </div>
        )}
      </div>
    </div>
  );
});

MainLayout.displayName = "MainLayout";

export default MainLayout;
