import React, { useMemo } from "react";
import { motion as Motion } from "framer-motion";
import { ArrowRight, Crown, Lock, CheckCircle2 } from "lucide-react";
import LevelButton from "../../game/LevelButton";
import { getTrackMeta } from "../../utils/challengeMeta";

const TRACK_ORDER = [
  "Python Basics",
  "Data Structures",
  "Control Flow",
  "Functions & Patterns",
  "Standard Library",
  "OOP Mastery",
];

const TRACK_DESCRIPTION = {
  "Python Basics": "Core syntax, variables, and fundamental concepts",
  "Data Structures": "Lists, dicts, sets, and complex data types",
  "Control Flow": "Conditionals, loops, and program logic",
  "Functions & Patterns": "Functions, closures, decorators, and design",
  "Standard Library": "Built-in modules, itertools, collections, and more",
  "OOP Mastery": "Classes, inheritance, polymorphism, and design",
};

const ChallengeMap = ({ levels, handleLevelClick }) => {
  const {
    certificateLevel,
    completedChallenges,
    totalChallenges,
    certificateProgressPercent,
    grouped,
    trackProgress,
  } = useMemo(() => {
    const sorted = [...levels].sort((a, b) => (a.order || 0) - (b.order || 0));
    const cert =
      sorted.find(
        (l) => l.slug === "certificate" || l.type === "CERTIFICATE",
      ) || null;
    const normal = sorted.filter(
      (l) => l.slug !== "certificate" && l.type !== "CERTIFICATE",
    );

    const groupsMap = {};
    normal.forEach((level) => {
      const track = getTrackMeta(level.order).label;
      if (!groupsMap[track]) groupsMap[track] = [];
      groupsMap[track].push(level);
    });

    const progress = {};
    Object.entries(groupsMap).forEach(([name, tLevels]) => {
      const solved = tLevels.filter((l) => l.completed).length;
      progress[name] = {
        solved,
        total: tLevels.length,
        percent: tLevels.length
          ? Math.round((solved / tLevels.length) * 100)
          : 0,
      };
    });

    const completed = normal.filter((l) => l.completed).length;

    return {
      certificateLevel: cert,
      completedChallenges: completed,
      totalChallenges: normal.length,
      certificateProgressPercent: normal.length
        ? Math.round((completed / normal.length) * 100)
        : 0,
      grouped: groupsMap,
      trackProgress: progress,
    };
  }, [levels]);

  return (
    <div className="w-full max-w-[1200px] mx-auto">
      {/* ─── Hero Stats ────────────────────────────────────────────── */}
      <div className="px-4 sm:px-8 pt-6 sm:pt-8 pb-2">
        <Motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          <div className="flex items-end justify-between gap-4 mb-6">
            <div>
              <h1 className="text-[22px] sm:text-[28px] font-semibold text-white tracking-tight leading-tight">
                Challenges
              </h1>
              <p className="text-[13px] sm:text-sm text-neutral-500 mt-1">
                {completedChallenges} of {totalChallenges} completed
              </p>
            </div>
            <div className="text-right hidden sm:block">
              <span className="text-2xl font-semibold text-white tabular-nums">
                {certificateProgressPercent}%
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="h-1 w-full bg-neutral-900 rounded-full overflow-hidden">
            <Motion.div
              className="h-full bg-white rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${certificateProgressPercent}%` }}
              transition={{ duration: 1, delay: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            />
          </div>
        </Motion.div>
      </div>

      <div className="mx-4 sm:mx-8 border-t border-neutral-900 my-4 sm:my-6" />

      {/* ─── Track Sections ───────────────────────────────────────── */}
      <div className="px-4 sm:px-8 space-y-8 sm:space-y-12 pb-8">
        {TRACK_ORDER.map((track, trackIdx) => {
          const trackLevels = grouped[track] || [];
          if (!trackLevels.length) return null;
          const prog = trackProgress[track] || {};
          const isComplete = prog.solved === prog.total && prog.total > 0;

          return (
            <Motion.section
              key={track}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{
                duration: 0.5,
                delay: trackIdx * 0.05,
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
            >
              {/* Track Header */}
              <div className="flex items-baseline justify-between gap-4 mb-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-[15px] font-medium text-white">
                      {track}
                    </h2>
                    {isComplete && (
                      <CheckCircle2 size={14} className="text-emerald-400" />
                    )}
                  </div>
                  <p className="text-[12.5px] text-neutral-500 mt-0.5">
                    {TRACK_DESCRIPTION[track]}
                  </p>
                </div>

                <span className="text-xs text-neutral-600 tabular-nums shrink-0 font-medium">
                  {prog.solved}/{prog.total}
                </span>
              </div>

              {/* Track Progress Bar */}
              <div className="h-px w-full bg-neutral-900 mb-5 relative overflow-hidden">
                <div
                  className="h-full bg-neutral-700 transition-all duration-700"
                  style={{ width: `${prog.percent}%` }}
                />
              </div>

              {/* Level Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2.5">
                {trackLevels.map((level, index) => {
                  const next = trackLevels[index + 1];
                  const isCurrentLevel = level.unlocked && !next?.unlocked;
                  return (
                    <LevelButton
                      key={level.id}
                      level={level}
                      isCurrentLevel={isCurrentLevel}
                      motionIndex={index}
                      onClick={() => handleLevelClick(level)}
                    />
                  );
                })}
              </div>
            </Motion.section>
          );
        })}
      </div>

      {/* ─── Certificate Section ──────────────────────────────────── */}
      {certificateLevel && (
        <div className="px-4 sm:px-8 pb-16">
          <div className="border-t border-neutral-800 pt-10">
            <Motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              <button
                onClick={() => handleLevelClick(certificateLevel)}
                disabled={!certificateLevel.unlocked}
                className={`
                  w-full text-left rounded-xl border p-6 sm:p-8
                  transition-all duration-200 group relative overflow-hidden
                  ${certificateLevel.unlocked
                    ? "bg-neutral-950 border-amber-500/30 hover:border-amber-500/50 hover:bg-neutral-900/80 cursor-pointer shadow-[0_0_30px_rgba(245,158,11,0.04)]"
                    : "bg-neutral-950 border-neutral-700 cursor-not-allowed"
                  }
                `}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 min-w-0">
                    <div
                      className={`w-12 h-12 rounded-xl border flex items-center justify-center shrink-0 ${
                        certificateLevel.unlocked
                          ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                          : "bg-neutral-900 border-neutral-700 text-neutral-400"
                      }`}
                    >
                      {certificateLevel.unlocked ? (
                        <Crown size={22} strokeWidth={1.5} />
                      ) : (
                        <Lock size={18} strokeWidth={2} />
                      )}
                    </div>
                    <div className="min-w-0 pt-0.5">
                      <p className="text-[11px] font-medium text-amber-400/70 uppercase tracking-wider mb-1">
                        Final Achievement
                      </p>
                      <h3 className="text-base sm:text-lg font-semibold text-white leading-snug">
                        Python Mastery Certificate
                      </h3>
                      <p className="mt-1.5 text-[13px] text-neutral-400 leading-relaxed">
                        {certificateLevel.unlocked
                          ? "Your journey is complete. View and share your verified achievement."
                          : "Complete all challenges to unlock your certificate."}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0 mt-1">
                    {certificateLevel.unlocked ? (
                      <ArrowRight
                        size={18}
                        className="text-amber-400 group-hover:text-amber-300 group-hover:translate-x-1 transition-all"
                      />
                    ) : (
                      <Lock size={14} className="text-neutral-600" />
                    )}
                  </div>
                </div>

                {/* Progress */}
                <div className="mt-6 pt-5 border-t border-neutral-800">
                  <div className="flex items-center justify-between mb-2.5">
                    <span className="text-[12px] text-neutral-400">
                      {completedChallenges} / {totalChallenges} challenges completed
                    </span>
                    <span className="text-[12px] font-medium text-white tabular-nums">
                      {certificateProgressPercent}%
                    </span>
                  </div>
                  <div className="h-1 w-full bg-neutral-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full transition-all duration-700"
                      style={{ width: `${certificateProgressPercent}%` }}
                    />
                  </div>
                </div>
              </button>
            </Motion.div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChallengeMap;
