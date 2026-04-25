import { Play, Sparkles, Star, X, Gem } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { cn } from "../lib/utils";
import { getDifficultyMeta } from "../utils/challengeMeta";

import { useNavigate } from "react-router-dom";

const LevelModal = ({ selectedLevel, onClose }) => {
  const navigate = useNavigate();

  if (!selectedLevel) return null;

  const levelNumber = selectedLevel.order || selectedLevel.id;
  const levelTitle = selectedLevel.title || selectedLevel.name;
  const stars = Math.max(0, Math.min(3, selectedLevel.stars || 0));
  const xpReward = selectedLevel.xp_reward || 0;
  const difficulty = getDifficultyMeta(levelNumber);

  return (
    <Dialog open={!!selectedLevel} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="sm:max-w-[340px] p-0 overflow-hidden rounded-lg border border-white/20 bg-[#050505] text-white shadow-2xl"
        showClose={false}
        aria-describedby={undefined}
      >
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex flex-col">
              <span className="text-[10px] font-bold tracking-[0.2em] text-[#444] uppercase font-mono">
                Mission Brief
              </span>
              <div className="flex items-center gap-1.5 mt-[-1px]">
                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-white text-[9px] font-bold uppercase tracking-tighter">
                  Sector {levelNumber} Analysis
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="h-6 w-6 rounded flex items-center justify-center text-neutral-700 hover:text-white hover:bg-[#1a1a1a] transition-all"
            >
              <X size={14} />
            </button>
          </div>

          <div className="space-y-4">
            {/* Title Area */}
            <DialogHeader className="px-1">
              <DialogTitle className="text-xl font-bold tracking-tight text-white mb-1 uppercase font-mono">
                {levelTitle}
              </DialogTitle>
              <p className="text-[11px] text-white/50 font-medium leading-relaxed">
                Analyze patterns, clear test cases, and earn rewards to advance
                through the core.
              </p>
            </DialogHeader>

            {/* Stats Row */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-md bg-black border border-white/10">
                <span className="text-[8px] font-bold tracking-[0.1em] text-white/30 uppercase font-mono block mb-1.5">
                  Rewards
                </span>
                <div className="flex items-center gap-1.5 leading-none">
                  <Gem size={14} className="text-red-500 fill-red-500/20" />
                  <span className="text-sm font-bold text-white font-mono tracking-tight">
                    {xpReward.toLocaleString()}
                  </span>
                </div>
              </div>
              <div className="p-3 rounded-md bg-black border border-white/10">
                <span className="text-[8px] font-bold tracking-[0.1em] text-white/30 uppercase font-mono block mb-1.5">
                  Complexity
                </span>
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-tighter">
                  {difficulty.label}
                </span>
              </div>
            </div>

            {/* Star Progress */}
            <div className="p-3 rounded-md bg-black border border-white/10">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[8px] font-bold tracking-[0.1em] text-white/30 uppercase font-mono">
                  Status
                </span>
                <span className="text-[9px] font-bold text-white/50 tabular-nums uppercase">
                  {stars}/3 Units
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {[1, 2, 3].map((star) => (
                  <Star
                    key={star}
                    size={14}
                    className={cn(
                      "transition-all duration-300",
                      star <= stars
                        ? "text-emerald-500 fill-emerald-500/20"
                        : "text-neutral-800 fill-transparent",
                    )}
                  />
                ))}
              </div>
            </div>

            <Button
              onClick={() =>
                navigate(`/level/${selectedLevel.slug || selectedLevel.id}`)
              }
              className="h-10 w-full rounded-md border border-[#222] bg-white text-[#0a0a0a] text-xs font-bold tracking-widest uppercase hover:bg-neutral-200 transition-all shadow-md group"
            >
              <Play
                size={14}
                fill="currentColor"
                className="group-hover:scale-110 transition-transform"
              />
              <span>Initiate Sync</span>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default LevelModal;
