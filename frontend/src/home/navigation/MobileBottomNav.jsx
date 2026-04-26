import React from "react";
import { useNavigate } from "react-router-dom";
import { Home, Trophy, Play, ShoppingBag, Shield, User } from "lucide-react";

/**
 * MobileBottomNav component
 * Fixed bottom navigation bar for mobile users.
 */
const MobileBottomNav = ({
  user,
  navLevels,
  setLeaderboardOpen,
}) => {
  const navigate = useNavigate();

  if (!user) return null;

  const navItems = [
    { Icon: Home, label: "Home", action: () => navigate("/home") },
    {
      Icon: Trophy,
      label: "Ranks",
      action: () => setLeaderboardOpen((p) => !p),
    },
    {
      Icon: Play,
      label: "Play",
      action: () => {
        const allChallenges = navLevels || [];
        const nonCert = allChallenges.filter((l) => l.slug !== "certificate");
        const current = [...nonCert]
          .reverse()
          .find((l) => l.status !== "LOCKED");
        if (current) {
          const targetId = current.slug || current.id || current.order;
          navigate(`/level/${targetId}`);
        } else if (nonCert.length > 0) {
          navigate(
            `/level/${nonCert[0].slug || nonCert[0].id || nonCert[0].order}`
          );
        }
      },
    },
    {
      Icon: ShoppingBag,
      label: "Store",
      action: () => navigate("/store"),
    },
  ];

  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-50 pointer-events-auto">
      <div className="absolute left-0 right-0 top-0 h-px bg-white/5" />
      <div className="bg-black px-5 pb-safe">
        <div className="flex items-center justify-around h-16">
          {navItems.map((item) => {
            const Icon = item.Icon;
            return (
              <button
                key={item.label}
                type="button"
                onClick={item.action}
                title={item.label}
                className="flex flex-col items-center gap-0.5 h-10 w-12 justify-center rounded-lg
                           text-white/80 hover:text-white transition-colors"
              >
                <Icon size={20} strokeWidth={1.8} />
                <span className="text-[9px] font-mono tracking-wide uppercase">
                  {item.label}
                </span>
              </button>
            );
          })}

          {(user?.is_staff || user?.is_superuser) && (
            <button
              type="button"
              onClick={() => navigate("/admin/dashboard")}
              title="Admin"
              className="flex flex-col items-center gap-0.5 h-10 w-12 justify-center rounded-lg
                         text-white/80 hover:text-white transition-colors"
            >
              <Shield size={20} strokeWidth={1.8} />
              <span className="text-[9px] font-mono tracking-wide uppercase">
                Admin
              </span>
            </button>
          )}

          <button
            type="button"
            onClick={() => navigate("/profile")}
            title="Profile"
            className="flex flex-col items-center gap-0.5 h-10 w-12 justify-center rounded-lg
                       text-white/80 hover:text-white transition-colors"
          >
            {user?.profile?.avatar_url ? (
              <img
                src={user.profile.avatar_url}
                alt="profile"
                className="h-6 w-6 rounded-full object-cover ring-1 ring-[#333]"
              />
            ) : (
              <User size={18} strokeWidth={1.6} />
            )}
            <span className="text-[9px] font-mono tracking-wide uppercase">
              You
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default MobileBottomNav;
