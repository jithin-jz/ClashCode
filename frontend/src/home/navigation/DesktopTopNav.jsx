import React from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Bell,
  Gem,
  Shield,
  Calendar,
  Award,
  ShoppingBag,
  Play,
  MessageSquare,
  Trophy,
  User,
  LogOut,
} from "lucide-react";
import NavButton from "./NavButton";
import useNotificationStore from "../../stores/useNotificationStore";

/**
 * DesktopTopNav component
 * The main header bar for desktop users.
 */
const DesktopTopNav = ({
  user,
  isScrolled,
  unreadCount,
  hasUnclaimedReward,
  isChatOpen,
  setChatOpen,
  setNotificationOpen,
  setCheckInOpen,
  setLeaderboardOpen,
  handleLogout,
  navLevels,
}) => {
  const navigate = useNavigate();
  const xp = user?.profile?.xp || 0;

  return (
    <nav
      className={`
        pointer-events-auto grid h-12 w-full grid-cols-[1fr_auto_1fr] items-center px-7 sm:px-9
        transition-all duration-300 ease-in-out
        app-top-nav ${isScrolled ? "h-14" : "h-12"}
      `}
    >
      {/* LEFT: User Stats & Desktop Actions */}
      <div className="flex items-center justify-start gap-3 min-w-0">
        {user ? (
          <>
            {/* Mobile Notification Shortcut (Hidden on desktop) */}
            <button
              type="button"
              onClick={() => setNotificationOpen((p) => !p)}
              className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/5 text-white sm:hidden"
            >
              <Bell size={14} className={unreadCount > 0 ? "text-amber-400" : ""} />
              {unreadCount > 0 && (
                <span className="absolute top-0.5 right-0.5 h-1.5 w-1.5 rounded-full bg-amber-400 ring-1 ring-black" />
              )}
            </button>

            {/* XP Chip */}
            <button
              type="button"
              onClick={() => navigate("/shop")}
              title="Buy Points"
              className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-white/20
                         bg-white/5 px-2.5 transition-colors hover:bg-white/10 hover:border-white/30"
            >
              <Gem size={13} className="text-red-500 fill-red-500/20" />
              <span className="text-white font-semibold text-[11px] tabular-nums font-['Geist_Mono',monospace]">
                {xp.toLocaleString()}
              </span>
            </button>

            {/* Desktop Extra Actions */}
            <div className="hidden sm:flex items-center gap-1.5 ml-1">
              {(user?.is_staff || user?.is_superuser) && (
                <NavButton onClick={() => navigate("/admin/dashboard")} title="Admin">
                  <Shield size={14} />
                </NavButton>
              )}
              <NavButton
                onClick={() => setCheckInOpen(true)}
                title="Daily Check-in"
                badge={
                  hasUnclaimedReward ? (
                    <span className="pointer-events-none absolute -right-0.5 -top-0.5 z-10 h-2 w-2 rounded-full bg-amber-400 ring-1 ring-black" />
                  ) : null
                }
              >
                <Calendar size={14} />
              </NavButton>
              <NavButton onClick={() => navigate("/achievements")} title="Achievements Hall">
                <Award size={14} />
              </NavButton>
              <NavButton onClick={() => navigate("/store")} title="Store">
                <ShoppingBag size={14} />
              </NavButton>
              <NavButton
                onClick={() => {
                  const allChallenges = navLevels || [];
                  const nonCert = allChallenges.filter((l) => l.slug !== "certificate");
                  const current = [...nonCert].reverse().find((l) => l.status !== "LOCKED");
                  if (current) {
                    navigate(`/level/${current.slug || current.id || current.order}`);
                  } else if (nonCert.length > 0) {
                    navigate(`/level/${nonCert[0].slug || nonCert[0].id || nonCert[0].order}`);
                  }
                }}
                title="Play"
                className="!text-emerald-400 !border-emerald-500/20 !bg-emerald-500/5 hover:!bg-emerald-500/10 hover:!border-emerald-500/30"
              >
                <Play size={14} fill="currentColor" />
              </NavButton>
            </div>
          </>
        ) : null}
      </div>

      {/* CENTER: Wordmark */}
      <div className="flex items-center justify-center px-2">
        <button
          type="button"
          onClick={() => navigate(user ? "/home" : "/")}
          className="group overflow-hidden"
          title="Home"
        >
          <span className="text-[11px] sm:text-[11px] font-bold tracking-[0.2em] text-white hover:text-neutral-300 transition-colors uppercase font-['Geist_Mono',monospace] truncate block max-w-[140px] sm:max-w-none">
            CLASHCODE
          </span>
        </button>
      </div>

      {/* RIGHT: System Toggles & Profile */}
      <div className="flex items-center justify-end gap-3">
        {user ? (
          <>
            {/* Mobile Hall/Check-in/Chat Shortcuts (Hidden on desktop) */}
            <div className="flex sm:hidden items-center gap-1">
              <button
                onClick={() => navigate("/achievements")}
                className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/5 text-white"
              >
                <Award size={14} />
              </button>
              <button
                onClick={() => setCheckInOpen(true)}
                className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-white/10 bg-white/5 text-white"
              >
                <Calendar size={14} />
                {hasUnclaimedReward && (
                  <span className="absolute top-0.5 right-0.5 h-1.5 w-1.5 rounded-full bg-amber-400 ring-1 ring-black" />
                )}
              </button>
              <button
                onClick={() => setChatOpen((p) => !p)}
                className={`relative flex h-8 w-8 shrink-0 items-center justify-center rounded-md border transition-colors ${
                  isChatOpen ? "border-white/30 bg-white/10 text-white" : "border-white/10 bg-white/5 text-white"
                }`}
              >
                <MessageSquare size={14} strokeWidth={isChatOpen ? 2.5 : 1.75} />
              </button>
            </div>

            {/* Desktop System Toggles */}
            <div className="hidden sm:flex items-center gap-1.5">
              <NavButton onClick={() => setChatOpen((p) => !p)} title="Chat" active={isChatOpen}>
                <MessageSquare size={14} />
              </NavButton>
              <NavButton onClick={() => setLeaderboardOpen((p) => !p)} title="Leaderboard">
                <Trophy size={14} />
              </NavButton>
              <NavButton
                onClick={() => {
                  if (Notification.permission === "default") {
                    useNotificationStore.getState().requestPermission();
                  }
                  setNotificationOpen((p) => !p);
                }}
                title="Notifications"
                className={unreadCount > 0 ? "!text-amber-400" : ""}
                badge={
                  unreadCount > 0 ? (
                    <span className="pointer-events-none absolute -right-0.5 -top-0.5 z-10 h-1.5 w-1.5 rounded-full bg-amber-400 ring-1 ring-black" />
                  ) : null
                }
              >
                <Bell size={14} />
              </NavButton>

              <div className="mx-1.5 h-4 w-px bg-white/10" />

              {/* Profile Avatar */}
              <button
                type="button"
                onClick={() => navigate("/profile")}
                title="Profile"
                className="h-8 w-8 rounded-md overflow-hidden border border-white/20 hover:border-white/30 transition-all shrink-0 bg-white/5"
              >
                {user?.profile?.avatar_url ? (
                  <img src={user.profile.avatar_url} alt="profile" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-[#1c1c1c]">
                    <User size={12} className="text-neutral-600" />
                  </div>
                )}
              </button>

              <NavButton
                onClick={handleLogout}
                title="Logout"
                className="!text-white/40 hover:!text-red-400 !border-white/5"
              >
                <LogOut size={13} />
              </NavButton>
            </div>
          </>
        ) : (
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="h-7 rounded-md bg-white px-3.5 text-[11px] font-semibold text-[#0a0a0a] transition-colors hover:bg-neutral-200"
          >
            Sign in
          </button>
        )}
      </div>
    </nav>
  );
};

export default DesktopTopNav;
