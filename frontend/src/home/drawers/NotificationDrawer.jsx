import React, { useEffect, memo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  Check,
  Trash2,
  X,
  MessageSquare,
  Gift,
  Heart,
  UserPlus,
  ArrowRight,
  Shield,
  Zap,
  Loader2,
} from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import useNotificationStore from "../../stores/useNotificationStore";
import useAuthStore from "../../stores/useAuthStore";

const NotificationDrawer = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const {
    notifications,
    unreadCount,
    totalCount,
    hasMore,
    isLoading,
    isLoadingMore,
    fetchNotifications,
    loadMoreNotifications,
    markAsRead,
    markAllAsRead,
    clearAll,
  } = useNotificationStore();

  useEffect(() => {
    if (!isOpen || !user) return;
    fetchNotifications(true);
  }, [isOpen, user, fetchNotifications]);

  const handleMarkRead = async (id, e) => {
    if (e) e.stopPropagation();
    await markAsRead(id);
  };

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      handleMarkRead(notification.id);
    }
    onClose();
    if (notification.actor?.username) {
      navigate(`/profile/${notification.actor.username}`);
    }
  };

  const getVerbConfig = (verb) => {
    const v = verb.toLowerCase();
    if (v.includes("follow"))
      return {
        icon: <UserPlus size={14} />,
        color: "text-primary",
        bg: "bg-primary/10",
        border: "border-primary/20",
      };
    if (v.includes("like"))
      return {
        icon: <Heart size={14} />,
        color: "text-rose-400",
        bg: "bg-rose-400/10",
        border: "border-rose-400/20",
      };
    if (v.includes("comment"))
      return {
        icon: <MessageSquare size={14} />,
        color: "text-blue-400",
        bg: "bg-blue-400/10",
        border: "border-blue-400/20",
      };
    if (v.includes("gift"))
      return {
        icon: <Gift size={14} />,
        color: "text-accent",
        bg: "bg-accent/10",
        border: "border-accent/20",
      };
    if (v.includes("verified"))
      return {
        icon: <Shield size={14} />,
        color: "text-green-400",
        bg: "bg-green-400/10",
        border: "border-green-400/20",
      };
    return {
      icon: <Bell size={14} />,
      color: "text-neutral-400",
      bg: "bg-white/10",
      border: "border-white/20",
    };
  };

  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    const baseUrl = import.meta.env.VITE_API_URL?.replace("/api", "") || "";
    return `${baseUrl}${url}`;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/20 sm:hidden"
          />
          <Motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full z-[60] w-full md:max-w-[360px] bg-[#050505] shadow-2xl flex flex-col md:border-l border-[#1a1a1a]"
          >
            {/* Header */}
            <header className="relative shrink-0 h-12 bg-[#0a0a0a] flex items-center justify-between px-4 border-b border-[#1a1a1a]">
              <div className="flex items-center gap-3">
                <div className="flex flex-col">
                  <h2 className="text-[10px] font-bold tracking-[0.2em] text-[#444] uppercase font-mono">
                    Notifications
                  </h2>
                  <div className="flex items-center gap-1.5 mt-[-1px]">
                    <span
                      className={`w-1 h-1 rounded-full ${unreadCount > 0 ? "bg-amber-500 animate-pulse shadow-[0_0_4px_rgba(245,158,11,0.5)]" : "bg-neutral-600"}`}
                    />
                    <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-tighter">
                      {unreadCount} Unread / {totalCount} Total
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {notifications.length > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="h-6 w-6 rounded flex items-center justify-center text-neutral-600 hover:text-white hover:bg-[#1a1a1a] transition-all"
                    title="Acknowledge All"
                  >
                    <Check size={14} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={onClose}
                  className="h-6 w-6 rounded flex items-center justify-center text-neutral-600 hover:text-white hover:bg-[#1a1a1a] transition-all"
                >
                  <X size={14} />
                </button>
              </div>
            </header>

            {/* Content */}
            <main className="flex-1 overflow-y-auto p-4 space-y-3 bg-transparent no-scrollbar">
              {isLoading && notifications.length === 0 ? (
                <div className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className="h-20 rounded-2xl bg-white/[0.02] border border-white/[0.05] animate-pulse"
                    />
                  ))}
                </div>
              ) : notifications.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-30 mt-20">
                  <Bell size={24} className="text-neutral-700 mb-2" />
                  <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-neutral-600">
                    Signal Clear
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {notifications.map((notification, index) => {
                    const config = getVerbConfig(notification.verb);
                    return (
                      <Motion.div
                        key={notification.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.03 }}
                        onClick={() => handleNotificationClick(notification)}
                        className={`group relative flex items-start gap-3 p-3 rounded-lg transition-all border cursor-pointer ${
                          !notification.is_read
                            ? "bg-amber-500/5 border-amber-500/10"
                            : "bg-[#111] border-[#1a1a1a] hover:bg-[#161616] hover:border-[#222]"
                        }`}
                      >
                        {/* Status Marker */}
                        {!notification.is_read && (
                          <div className="absolute top-3 right-3 w-1 h-1 rounded-full bg-amber-500" />
                        )}

                        {/* Avatar & Icon Badge */}
                        <div className="relative shrink-0">
                          <div className="w-9 h-9 rounded-md overflow-hidden border border-white/5 bg-[#1c1c1c]">
                            {getImageUrl(notification.actor?.avatar_url) ? (
                              <img
                                src={getImageUrl(notification.actor.avatar_url)}
                                alt=""
                                className="w-full h-full object-cover transition-transform duration-500"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-[10px] font-bold text-neutral-500 uppercase">
                                {notification.actor?.username?.[0] || "?"}
                              </div>
                            )}
                          </div>
                          <div
                            className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-md flex items-center justify-center border shadow-lg ${config.bg} ${config.border} ${config.color}`}
                          >
                            {config.icon}
                          </div>
                        </div>

                        {/* Text Content */}
                        <div className="flex-1 min-w-0 pt-0.5">
                          <p className="text-[12px] leading-snug text-neutral-400">
                            <span
                              className={`font-bold uppercase tracking-tight ${!notification.is_read ? "text-neutral-200" : "text-neutral-500"}`}
                            >
                              {notification.actor?.username || "SYSTEM"}
                            </span>{" "}
                            <span className="text-neutral-600">
                              {notification.verb}
                            </span>
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[9px] font-bold font-mono text-neutral-700 uppercase tracking-tighter">
                              {formatDistanceToNow(
                                new Date(notification.created_at),
                                { addSuffix: true },
                              )}
                            </span>
                          </div>
                        </div>
                      </Motion.div>
                    );
                  })}

                  {hasMore && (
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={loadMoreNotifications}
                        disabled={isLoadingMore}
                        className="w-full h-10 rounded-lg border border-[#222] bg-[#0d0d0d] text-[10px] font-bold uppercase tracking-[0.16em] text-neutral-500 hover:text-white hover:border-[#333] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {isLoadingMore ? (
                          <>
                            <Loader2 size={12} className="animate-spin" />
                            Loading More
                          </>
                        ) : (
                          <>
                            <ArrowRight size={12} />
                            Load More
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </main>

            {/* Footer Actions */}
            {notifications.length > 0 && (
              <footer className="p-3 bg-[#0a0a0a] border-t border-[#1a1a1a] flex items-center justify-between">
                <button
                  onClick={clearAll}
                  className="px-3 py-1.5 rounded-md text-[9px] font-bold uppercase tracking-widest text-neutral-600 hover:text-red-500 hover:bg-red-500/5 transition-all flex items-center gap-2"
                >
                  <Trash2 size={10} />
                  Purge Data
                </button>
              </footer>
            )}
          </Motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default memo(NotificationDrawer);
