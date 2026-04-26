import React from "react";

const Pulse = ({ className = "" }) => (
  <div className={`bg-white/[0.04] animate-pulse rounded-2xl ${className}`} />
);
const PulseLine = ({ width = "100%", height = "1rem", className = "" }) => (
  <div
    className={`bg-white/[0.04] animate-pulse rounded ${className}`}
    style={{ width, height }}
  />
);
const PulseCode = ({ lines = 12 }) => (
  <div className="bg-black/40 rounded-2xl border border-white/[0.05] overflow-hidden font-mono">
    <div className="flex">
      <div className="w-12 bg-white/[0.01] border-r border-white/5 py-5 px-3 flex flex-col gap-3">
        {[...Array(lines)].map((_, i) => (
          <div key={i} className="h-3 w-6 bg-white/[0.03] rounded-sm" />
        ))}
      </div>
      <div className="flex-1 p-5 space-y-3">
        {[85, 60, 45, 70, 90, 55, 75, 40, 80, 65, 50, 95]
          .slice(0, lines)
          .map((w, i) => (
            <div
              key={i}
              className="h-3 bg-white/[0.04] animate-pulse rounded-sm"
              style={{ width: `${w}%` }}
            />
          ))}
      </div>
    </div>
  </div>
);

const ChallengeWorkspaceSkeleton = () => {
  return (
    <div className="flex flex-col h-dvh bg-black overflow-hidden relative">
      {/* Background gradients */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-emerald-500/[0.03] blur-[150px] rounded-full" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-600/[0.02] blur-[130px] rounded-full" />

      {/* Top Navbar Skeleton */}
      <div className="relative z-20 h-16 bg-black/40 backdrop-blur-3xl border-b border-white/[0.05] flex items-center justify-between px-6">
        <div className="flex items-center gap-6">
          <Pulse className="w-10 h-10 rounded-xl border border-white/10" />
          <div className="space-y-2 pt-1 hidden sm:block">
            <PulseLine width="180px" height="1rem" className="opacity-90" />
            <PulseLine width="120px" height="0.65rem" className="opacity-30" />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Pulse className="w-10 h-10 rounded-xl sm:hidden" />
          <div className="hidden sm:flex items-center gap-3">
            <Pulse className="w-24 h-5 rounded-full opacity-20" />
            <Pulse className="w-32 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 shadow-lg" />
          </div>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="relative z-10 flex-1 p-0 sm:p-3 sm:gap-4 flex flex-col lg:flex-row overflow-hidden min-h-0">
        {/* Left Sidebar - Problem Desc */}
        <div className="w-full lg:w-[26rem] sm:rounded-2xl sm:border border-white/[0.05] bg-white/[0.015] backdrop-blur-2xl p-6 flex flex-col gap-6 shadow-2xl overflow-y-auto hidden lg:flex">
          <div className="space-y-2">
            <PulseLine width="140px" height="0.75rem" className="opacity-40" />
            <PulseLine width="100%" height="2rem" />
          </div>
          <div className="space-y-4 pt-4 border-t border-white/5 flex-1">
            {[...Array(4)].map((_, i) => (
              <Pulse key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
          <Pulse className="h-14 w-full rounded-2xl opacity-40 shrink-0" />
        </div>

        {/* Center - Code Editor */}
        <div className="flex-1 min-w-0 sm:rounded-2xl sm:border border-white/[0.05] bg-black/40 backdrop-blur-xl overflow-hidden flex flex-col shadow-2xl">
          <div className="h-11 bg-white/[0.02] border-b border-white/5 flex items-center px-4 gap-2">
            <Pulse className="h-6 w-32 rounded-lg" />
            <Pulse className="h-6 w-24 rounded-lg opacity-20" />
          </div>
          <div className="flex-1 p-2 bg-[#050505]">
            <PulseCode lines={24} />
          </div>
          {/* Output / Terminal Area */}
          <div className="h-[28rem] sm:h-[32%] min-h-[220px] border-t border-white/5 bg-black/60 p-6 space-y-4">
            <div className="flex justify-between items-center px-1">
              <PulseLine
                width="120px"
                height="0.75rem"
                className="opacity-40"
              />
              <div className="flex gap-2">
                <Pulse className="h-5 w-5 rounded-md opacity-20" />
                <Pulse className="h-5 w-5 rounded-md opacity-20" />
              </div>
            </div>
            <div className="space-y-3 font-mono">
              <PulseLine width="100%" height="0.65rem" className="opacity-10" />
              <PulseLine width="95%" height="0.65rem" className="opacity-10" />
              <PulseLine width="80%" height="0.65rem" className="opacity-10" />
            </div>
          </div>
        </div>

        {/* Right Sidebar - AI Assistant / Stats */}
        <div className="w-full lg:w-[24rem] sm:rounded-2xl sm:border border-white/[0.05] bg-white/[0.02] p-6 flex flex-col shadow-2xl hidden lg:flex">
          <div className="flex items-center justify-between mb-8">
            <PulseLine width="140px" height="1.1rem" className="opacity-90" />
            <Pulse className="h-9 w-9 rounded-xl opacity-30" />
          </div>
          <div className="flex-1 space-y-6">
            <Pulse className="h-56 rounded-2xl" />
            <div className="space-y-4 pt-6 mt-6 border-t border-white/5">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-4 items-center">
                  <Pulse key={i} className="h-10 w-10 rounded-xl opacity-20" />
                  <PulseLine
                    width="70%"
                    height="0.85rem"
                    className="opacity-60"
                  />
                </div>
              ))}
            </div>
          </div>
          <div className="pt-6 mt-6 border-t border-white/5 flex gap-3">
            <Pulse className="h-12 flex-1 rounded-2xl bg-white/5" />
            <Pulse className="h-12 w-12 rounded-2xl bg-emerald-500/20" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChallengeWorkspaceSkeleton;
