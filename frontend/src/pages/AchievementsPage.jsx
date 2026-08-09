import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import useAuthStore from "../stores/useAuthStore";

import AchievementCard from "../components/AchievementCard";
import { AchievementsSkeleton } from "../bones/PageSkeletons";
import { useAchievements } from "../hooks/useAchievements";

const AchievementsPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { achievements, userAchievements, loading, isUnlocked } =
    useAchievements(user);

  const trophyScore = (userAchievements?.length || 0) * 10;

  if (loading) return <AchievementsSkeleton />;

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-8">
        {/* Header */}
        <div className="pt-8 pb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-neutral-500 hover:text-white transition-colors mb-6 group"
          >
            <ArrowLeft
              size={15}
              className="group-hover:-translate-x-0.5 transition-transform"
            />
            <span className="text-[12px] font-medium">Back</span>
          </button>

          <div className="flex items-end justify-between gap-6">
            <div>
              <h1 className="text-[22px] sm:text-[28px] font-semibold text-white tracking-tight">
                Achievements
              </h1>
              <p className="text-[13px] sm:text-sm text-neutral-500 mt-1">
                {userAchievements?.length || 0} of {achievements?.length || 0} unlocked
              </p>
            </div>

            <div className="flex items-center gap-6 text-right">
              <div>
                <p className="text-2xl font-semibold text-white tabular-nums">
                  {userAchievements?.length || 0}
                  <span className="text-sm text-neutral-600 font-normal ml-1">
                    /{achievements?.length || 0}
                  </span>
                </p>
                <p className="text-[11px] text-neutral-600 mt-0.5">Unlocked</p>
              </div>
              <div className="w-px h-8 bg-neutral-800 hidden sm:block" />
              <div className="hidden sm:block">
                <p className="text-2xl font-semibold text-white tabular-nums">
                  {trophyScore}
                </p>
                <p className="text-[11px] text-neutral-600 mt-0.5">Score</p>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6 h-1 w-full bg-neutral-900 rounded-full overflow-hidden">
            <Motion.div
              className="h-full bg-white rounded-full"
              initial={{ width: 0 }}
              animate={{
                width: `${achievements?.length ? ((userAchievements?.length || 0) / achievements.length) * 100 : 0}%`,
              }}
              transition={{ duration: 1, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
            />
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-neutral-900 mb-8" />

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          <AnimatePresence mode="popLayout">
            {achievements.map((achievement, idx) => (
              <AchievementCard
                key={achievement.id}
                achievement={achievement}
                unlocked={isUnlocked(achievement.id)}
                idx={idx}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default AchievementsPage;
