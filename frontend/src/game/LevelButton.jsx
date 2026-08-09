import React from "react";
import { motion as Motion } from "framer-motion";
import { ArrowRight, CheckCircle2, Lock, Star, Gem } from "lucide-react";
import { getDifficultyMeta } from "../utils/challengeMeta";

const LevelButton = ({ level, isCurrentLevel, onClick }) => {
  const isCertificate =
    level.type === "CERTIFICATE" || level.slug === "certificate";
  const difficulty = getDifficultyMeta(level.order);

  const isCompleted = level.completed;
  const isUnlocked = level.unlocked;
  const isLocked = !isUnlocked;

  return (
    <Motion.button
      onClick={onClick}
      disabled={isLocked}
      animate={isCurrentLevel && isUnlocked ? { y: [-0.5, 0.5, -0.5] } : {}}
      transition={
        isCurrentLevel && isUnlocked
          ? { duration: 3, repeat: Infinity, ease: "easeInOut" }
          : {}
      }
      className={`
        w-full text-left rounded-lg border p-3 sm:p-3.5 min-h-[100px] sm:min-h-[110px]
        transition-all duration-200 group relative flex flex-col justify-between
        ${isCompleted
          ? "bg-neutral-950 border-neutral-700"
          : isUnlocked
            ? `bg-neutral-950 border-neutral-700 hover:border-neutral-500 hover:bg-neutral-900 ${isCurrentLevel ? "border-neutral-500 ring-1 ring-white/10" : ""}`
            : "bg-neutral-950/50 border-neutral-700/70"
        }
        ${isUnlocked ? "cursor-pointer active:scale-[0.98]" : "cursor-not-allowed opacity-70"}
      `}
    >
      {/* Top section */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-wider mb-1">
            {isCertificate ? "Certificate" : `Level ${level.order}`}
          </p>
          <p className="text-[13px] font-medium text-white leading-snug line-clamp-2">
            {isCertificate ? "Professional Badge" : level.title || level.name}
          </p>
        </div>

        {/* Status indicator */}
        <div className="shrink-0 mt-0.5">
          {isCompleted ? (
            <CheckCircle2 size={14} className="text-emerald-400" />
          ) : isUnlocked ? (
            <ArrowRight
              size={13}
              className="text-neutral-600 group-hover:text-white group-hover:translate-x-0.5 transition-all"
            />
          ) : (
            <Lock size={11} className="text-neutral-700" />
          )}
        </div>
      </div>

      {/* Bottom section */}
      {!isCertificate && (
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Difficulty */}
            <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${
              difficulty.label === "Easy"
                ? "bg-emerald-500/10 text-emerald-400"
                : difficulty.label === "Medium"
                  ? "bg-amber-500/10 text-amber-400"
                  : "bg-red-500/10 text-red-400"
            }`}>
              {difficulty.label}
            </span>

            {/* XP */}
            {isUnlocked && (
              <span className="flex items-center gap-1 text-[10px] text-neutral-600">
                <Gem size={9} className="text-neutral-600" />
                {level.xp_reward || 0}
              </span>
            )}
          </div>

          {/* Stars */}
          <div className="flex gap-px">
            {[1, 2, 3].map((star) => (
              <Star
                key={star}
                size={9}
                className={
                  star <= (level.stars || 0)
                    ? "text-amber-400 fill-amber-400"
                    : "text-neutral-800 fill-neutral-800"
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Current level indicator */}
      {isCurrentLevel && isUnlocked && !isCompleted && (
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      )}

      {/* Locked hint */}
      {!isCertificate && isLocked && (
        <p className="mt-2 text-[10px] text-neutral-500">
          Complete prior level
        </p>
      )}
    </Motion.button>
  );
};

export default LevelButton;
