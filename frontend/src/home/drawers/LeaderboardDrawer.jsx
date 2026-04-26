import React, { useEffect, useState, memo } from "react";
import { Link } from "react-router-dom";
import {
  Trophy,
  Crown,
  Medal,
  Users,
  X,
  Gem,
  ArrowRight,
  MessageSquare,
} from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import { Skeleton } from "boneyard-js/react";
import api from "../../services/api";
import useAuthStore from "../../stores/useAuthStore";

const LeaderboardDrawer = ({ isLeaderboardOpen, setLeaderboardOpen }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user: currentUser } = useAuthStore();

  useEffect(() => {
    if (isLeaderboardOpen) {
      const fetchLeaderboard = async () => {
        setLoading(true);
        try {
          const response = await api.get("/challenges/leaderboard/");
          setUsers(response.data.slice(0, 20));
        } catch (error) {
          console.error("Failed to fetch leaderboard:", error);
        } finally {
          setLoading(false);
        }
      };
      fetchLeaderboard();
    }
  }, [isLeaderboardOpen]);

  const getRankStyles = (index) => {
    switch (index) {
      case 0:
        return {
          icon: <Crown size={16} />,
          color: "text-[#ffa116]",
          bg: "bg-[#ffa116]/10",
          border: "border-[#ffa116]/20",
          label: "Grandmaster",
        };
      case 1:
        return {
          icon: <Medal size={16} />,
          color: "text-neutral-300",
          bg: "bg-neutral-300/10",
          border: "border-neutral-300/20",
          label: "Master",
        };
      case 2:
        return {
          icon: <Medal size={16} />,
          color: "text-[#cd7f32]",
          bg: "bg-[#cd7f32]/10",
          border: "border-[#cd7f32]/20",
          label: "Elite",
        };
      default:
        return {
          icon: null,
          color: "text-neutral-500",
          bg: "bg-white/[0.03]",
          border: "border-white/[0.05]",
          label: null,
        };
    }
  };

  return (
    <AnimatePresence>
      {isLeaderboardOpen && (
        <>
          <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLeaderboardOpen(false)}
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
              <div className="flex items-center gap-2">
                <div className="flex flex-col">
                  <span className="text-[10px] font-bold tracking-[0.2em] text-[#444] uppercase font-mono">
                    Leaderboard
                  </span>
                  <div className="flex items-center gap-1 leading-none">
                    <span className="w-1 h-1 rounded-full bg-amber-500" />
                    <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-tighter">
                      Global Standings
                    </span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setLeaderboardOpen(false)}
                className="h-6 w-6 rounded-md flex items-center justify-center text-neutral-600 hover:text-white hover:bg-[#1a1a1a] transition-all"
              >
                <X size={14} />
              </button>
            </header>

            {/* List Content */}
            <main className="flex-1 overflow-y-auto p-4 space-y-3 bg-transparent ds-scrollbar">
              <Skeleton name="leaderboard-list" loading={loading}>
                {users.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                    <Trophy size={48} className="text-neutral-800 mb-4" />
                    <p className="text-sm font-bold uppercase tracking-widest">
                      No legends yet
                    </p>
                  </div>
                ) : (
                  users.map((rankUser, index) => {
                    const isMe = currentUser?.username === rankUser.username;
                    const styles = getRankStyles(index);

                    return (
                      <Motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.03 }}
                        key={rankUser.username}
                      >
                        <Link
                          to={`/profile/${rankUser.username}`}
                          onClick={() => setLeaderboardOpen(false)}
                          className={`group relative flex items-center gap-3 p-2.5 rounded-lg transition-all border ${
                            isMe
                              ? "bg-emerald-500/10 border-emerald-500/20 shadow-sm"
                              : "bg-[#111] border-[#1a1a1a] hover:bg-[#161616] hover:border-[#222]"
                          }`}
                        >
                          {/* Rank Circle */}
                          <div
                            className={`shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-[9px] font-black border ${styles.bg} ${styles.border} ${styles.color}`}
                          >
                            {styles.icon
                              ? React.cloneElement(styles.icon, { size: 10 })
                              : `#${index + 1}`}
                          </div>

                          {/* Avatar */}
                          <div className="relative shrink-0 w-8 h-8 rounded-md overflow-hidden border border-white/5 transition-transform duration-500">
                            {rankUser.avatar ? (
                              <img
                                src={
                                  rankUser.avatar.startsWith("http")
                                    ? rankUser.avatar
                                    : `${import.meta.env.VITE_API_URL.replace("/api", "")}${rankUser.avatar}`
                                }
                                alt=""
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full bg-[#1c1c1c] flex items-center justify-center text-[10px] font-bold text-neutral-500">
                                {rankUser.username?.[0]?.toUpperCase()}
                              </div>
                            )}
                          </div>

                          {/* Details */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-[11px] font-bold truncate ${isMe ? "text-emerald-400" : "text-neutral-200"}`}
                              >
                                {isMe ? "YOU" : rankUser.username}
                              </span>
                              {styles.label && (
                                <span
                                  className={`text-[7px] font-bold uppercase tracking-widest px-1 py-0.5 rounded border ${styles.border} ${styles.bg} ${styles.color}`}
                                >
                                  {styles.label}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2.5 mt-0.5">
                              <div className="flex items-center gap-1">
                                <Gem size={8} className="text-neutral-600" />
                                <span className="text-[10px] font-bold text-neutral-500">
                                  {rankUser.xp?.toLocaleString()}
                                </span>
                              </div>
                              <span className="text-[9px] font-bold text-neutral-700 uppercase tracking-tighter">
                                {rankUser.completed_levels} Levels
                              </span>
                            </div>
                          </div>

                          {/* Action Icon */}
                          <ArrowRight
                            size={14}
                            className="text-neutral-600 group-hover:text-primary transition-colors duration-300"
                          />

                          {isMe && (
                            <div className="absolute inset-0 bg-primary/5 rounded-2xl pointer-events-none" />
                          )}
                        </Link>
                      </Motion.div>
                    );
                  })
                )}
              </Skeleton>
            </main>
          </Motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default memo(LeaderboardDrawer);
