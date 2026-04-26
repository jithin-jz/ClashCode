import React, { useEffect, useState } from "react";
import useNotificationStore from "../../stores/useNotificationStore";
import DesktopTopNav from "./DesktopTopNav";
import MobileBottomNav from "./MobileBottomNav";

/**
 * HomeTopNav (Main Navigation Orchestrator)
 * 
 * Handles scroll detection and renders both the Desktop Top Nav 
 * and the Mobile Bottom Nav. Logic for these is split into sub-components.
 */
const HomeTopNav = ({
  user,
  handleLogout,
  setChatOpen,
  isChatOpen,
  setCheckInOpen,
  setLeaderboardOpen,
  setNotificationOpen,
  hasUnclaimedReward,
  levels: navLevels,
}) => {
  const userId = user?.id;
  const { unreadCount, fetchNotifications } = useNotificationStore();
  const [isScrolled, setIsScrolled] = useState(false);

  // Scroll detection for header height/style changes
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Fetch notifications on user load
  useEffect(() => {
    if (userId) fetchNotifications();
  }, [userId, fetchNotifications]);

  return (
    <>
      {/* ── TOP NAV (Fixed at top) ── */}
      <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none">
        <DesktopTopNav
          user={user}
          isScrolled={isScrolled}
          unreadCount={unreadCount}
          hasUnclaimedReward={hasUnclaimedReward}
          isChatOpen={isChatOpen}
          setChatOpen={setChatOpen}
          setNotificationOpen={setNotificationOpen}
          setCheckInOpen={setCheckInOpen}
          setLeaderboardOpen={setLeaderboardOpen}
          handleLogout={handleLogout}
          navLevels={navLevels}
        />
      </div>

      {/* ── MOBILE BOTTOM NAV (Fixed at bottom) ── */}
      <MobileBottomNav
        user={user}
        navLevels={navLevels}
        setLeaderboardOpen={setLeaderboardOpen}
      />
    </>
  );
};

export default HomeTopNav;
