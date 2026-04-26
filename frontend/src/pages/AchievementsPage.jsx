import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Trophy,
  Target,
  Users,
  Medal,
  TrendingUp,
  Zap,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";
import { AnimatePresence } from "framer-motion";
import { Skeleton } from "boneyard-js/react";
import useAuthStore from "../stores/useAuthStore";

// Components
import AchievementCard from "../components/AchievementCard";

// Hooks
import { useAchievements } from "../hooks/useAchievements";

const AchievementsPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { achievements, userAchievements, loading, isUnlocked } =
    useAchievements(user);

  const trophyScore = (userAchievements?.length || 0) * 10;

  return (
    <Skeleton name="achievements-page" loading={loading}>
      <div className="min-h-screen bg-black text-white selection:bg-emerald-500/30 pb-24 relative overflow-hidden">
        {/* Subtle Background FX */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(16,185,129,0.05),transparent_70%)]" />
          <div className="absolute inset-0 ds-dot-grid opacity-20" />
        </div>

        <div className="max-w-[1200px] mx-auto px-6 relative z-10">
          {/* Simple Header */}
          <div className="pt-12 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <button
                onClick={() => navigate(-1)}
                className="flex items-center gap-2 text-neutral-500 hover:text-white transition-colors mb-4 group"
              >
                <ArrowLeft
                  size={16}
                  className="group-hover:-translate-x-1 transition-transform"
                />
                <span className="text-xs font-bold tracking-widest uppercase font-mono">
                  Back
                </span>
              </button>
              <h1 className="text-4xl font-black tracking-tight text-white uppercase sm:text-5xl">
                Hall of <span className="text-emerald-500">Fame</span>
              </h1>
              <p className="text-neutral-500 mt-2 font-medium max-w-md">
                Your journey through the arena. Collect trophies by completing
                challenges and mastering the arts.
              </p>
            </div>

            <div className="flex items-center gap-8 border-t md:border-t-0 border-white/5 pt-6 md:pt-0">
              <div className="space-y-1">
                <p className="ds-eyebrow opacity-40">Unlocked</p>
                <p className="text-3xl font-black font-mono tracking-tighter">
                  {userAchievements?.length || 0}
                  <span className="text-sm text-neutral-600 ml-1">
                    /{achievements?.length || 0}
                  </span>
                </p>
              </div>
              <div className="w-px h-10 bg-white/5 hidden md:block" />
              <div className="space-y-1">
                <p className="ds-eyebrow opacity-40">Trophy Score</p>
                <p className="text-3xl font-black font-mono tracking-tighter text-emerald-500">
                  {trophyScore}
                </p>
              </div>
            </div>
          </div>

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
    </Skeleton>
  );
};

export default AchievementsPage;
