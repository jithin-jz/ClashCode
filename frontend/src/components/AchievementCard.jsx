import React from "react";
import { Trophy, CheckCircle2, Lock, Zap } from "lucide-react";
import { motion as Motion } from "framer-motion";

const CATEGORY_COLORS = {
  CODING: {
    text: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    glow: "shadow-[0_0_20px_rgba(59,130,246,0.15)]",
    accent: "text-blue-500",
    gradient: "from-blue-500/10",
  },
  COMMUNITY: {
    text: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    glow: "shadow-[0_0_20px_rgba(168,85,247,0.15)]",
    accent: "text-purple-500",
    gradient: "from-purple-500/10",
  },
  CONSISTENCY: {
    text: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
    glow: "shadow-[0_0_20px_rgba(249,115,22,0.15)]",
    accent: "text-orange-500",
    gradient: "from-orange-500/10",
  },
  SPECIAL: {
    text: "text-yellow-400",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/20",
    glow: "shadow-[0_0_20px_rgba(234,179,8,0.15)]",
    accent: "text-yellow-500",
    gradient: "from-yellow-500/10",
  },
  default: {
    text: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    glow: "shadow-[0_0_20px_rgba(16,185,129,0.15)]",
    accent: "text-emerald-500",
    gradient: "from-emerald-500/10",
  },
};

const AchievementCard = ({ achievement, unlocked, idx }) => {
  const colors =
    CATEGORY_COLORS[achievement.category] || CATEGORY_COLORS.default;

  return (
    <Motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2, delay: idx * 0.01 }}
      className="h-full"
    >
      <div
        className={`
        relative h-full flex flex-col p-4 rounded-xl border transition-all duration-500 group overflow-hidden
        ${
          unlocked
            ? `bg-white/[0.03] backdrop-blur-sm border-white/10 hover:border-white/20 ${colors.glow}`
            : "bg-white/[0.01] border-white/[0.03] opacity-100"
        }
      `}
      >
        {/* Animated Glow Background for Unlocked */}
        {unlocked && (
          <div
            className={`absolute -inset-24 bg-gradient-to-tr ${colors.gradient} via-transparent to-transparent opacity-20 group-hover:opacity-40 transition-opacity duration-700 blur-2xl pointer-events-none`}
          />
        )}

        {/* Progress Background for Unlocked */}
        {unlocked && (
          <div className="absolute top-0 right-0 p-3 z-10">
            <div
              className={`w-1.5 h-1.5 rounded-full ${colors.accent} shadow-[0_0_8px_currentColor]`}
            />
          </div>
        )}

        {/* Icon Wrapper */}
        <div className="mb-4 relative z-10">
          <div
            className={`
            w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-500 relative overflow-hidden
            ${
              unlocked
                ? `${colors.bg} ${colors.text} ${colors.border} group-hover:scale-110 group-hover:rotate-3`
                : "bg-white/[0.03] text-white/5 border border-white/5"
            }
          `}
          >
            {unlocked && (
              <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
            <Trophy
              size={18}
              strokeWidth={2.5}
              className={unlocked ? "drop-shadow-sm" : ""}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-2 relative z-10">
          <div className="space-y-0.5">
            <p
              className={`text-[9px] font-black uppercase tracking-[0.2em] font-mono transition-colors ${unlocked ? colors.text : "text-neutral-700"}`}
            >
              {achievement.category}
            </p>
            <h3
              className={`text-[13px] font-bold tracking-tight uppercase font-mono ${unlocked ? "text-white" : "text-neutral-500"}`}
            >
              {achievement.title}
            </h3>
          </div>
          <p
            className={`text-[11px] leading-relaxed font-medium transition-colors ${unlocked ? "text-neutral-400 group-hover:text-neutral-300" : "text-neutral-700"}`}
          >
            {achievement.description}
          </p>
        </div>

        {/* Footer */}
        <div className="mt-5 flex items-center justify-between relative z-10">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-all duration-300 ${unlocked ? `${colors.bg} ${colors.border}` : "bg-white/[0.02] border-white/5"}`}
          >
            <Zap
              size={9}
              className={unlocked ? colors.text : "text-neutral-700"}
            />
            <span
              className={`text-[9px] font-bold font-mono ${unlocked ? "text-white" : "text-neutral-700"}`}
            >
              {achievement.xp_reward} <span className="opacity-40">XP</span>
            </span>
          </div>

          {!unlocked ? (
            <Lock size={10} className="text-neutral-700" />
          ) : (
            <div
              className={`w-1.5 h-1.5 rounded-full ${colors.accent} animate-pulse shadow-[0_0_8px_currentColor]`}
            />
          )}
        </div>
      </div>
    </Motion.div>
  );
};

export default AchievementCard;
