import React from "react";
import { Sparkles, Gem } from "lucide-react";
import { motion as Motion } from "framer-motion";
import VictoryAnimation from "../VictoryAnimation";

const CompletionModal = ({ data, onNext, onDashboard, activeVictory }) => {
  if (!data) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4">
      <VictoryAnimation type={activeVictory} />
      <Motion.div
        initial={{ scale: 0.98, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-[#111]/95 backdrop-blur-md border border-[#222] rounded-2xl p-6 sm:p-10 max-w-sm w-full flex flex-col items-center text-center shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        <div className="relative z-10 flex flex-col items-center gap-6">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-2 bg-green-500/10 border border-green-500/20">
            <Sparkles size={32} className="text-green-500" />
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white uppercase tracking-wider">Challenge Complete</h2>
            <p className="text-gray-500 text-xs text-balance">Validation successful. You've beaten the challenge.</p>
          </div>

          <div className="flex gap-2 my-1">
            {[1, 2, 3].map((star) => (
              <div
                key={star}
                className={`w-6 h-6 flex items-center justify-center ${star <= data.stars ? "text-[#ffa116]" : "text-gray-800"}`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-5.82 3.25L7.38 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
              </div>
            ))}
          </div>

          {data.xp_earned > 0 && (
            <div className="text-white text-sm font-mono tracking-tighter flex items-center gap-1.5">
              <Gem size={14} className="text-red-500 fill-red-500/10" />+{data.xp_earned} EARNED
            </div>
          )}

          <div className="flex flex-col w-full gap-2 mt-4">
            {data.next_level_slug && (
              <button
                onClick={onNext}
                className="w-full h-10 rounded-xl bg-[#ffa116] text-black hover:bg-[#ff8f00] font-bold uppercase text-xs transition-colors"
              >
                Next Challenge
              </button>
            )}
            <button
              onClick={onDashboard}
              className="w-full h-10 rounded-xl border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:bg-white/10 font-bold uppercase text-xs transition-colors"
            >
              Dashboard
            </button>
          </div>
        </div>
      </Motion.div>
    </div>
  );
};

export default CompletionModal;
