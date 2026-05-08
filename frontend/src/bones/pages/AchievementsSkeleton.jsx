import React from "react";
import { P, Panel } from "../SkeletonPrimitives";

export const AchievementsSkeleton = () => (
  <div className="min-h-screen bg-black text-white relative overflow-hidden">
    {/* Subtle Background FX */}
    <div className="fixed inset-0 z-0 pointer-events-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(16,185,129,0.05),transparent_70%)]" />
      <div className="absolute inset-0 ds-dot-grid opacity-20" />
    </div>

    <div className="max-w-[1200px] mx-auto px-6 relative z-10 space-y-12">
      {/* Header Skeleton */}
      <div className="pt-12 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <P className="h-4 w-4 rounded-sm opacity-20" />
            <P className="h-3 w-16 opacity-20" />
          </div>
          <div className="flex gap-3">
            <P className="h-12 w-48" />
            <P className="h-12 w-32 opacity-50" />
          </div>
        </div>

        <div className="flex items-center gap-8 pt-6 md:pt-0">
          <div className="space-y-1">
            <P className="h-3 w-16 opacity-20" />
            <P className="h-8 w-20" />
          </div>
          <div className="w-px h-10 bg-white/5 hidden md:block" />
          <div className="space-y-1">
            <P className="h-3 w-20 opacity-20" />
            <P className="h-8 w-16 opacity-50" />
          </div>
        </div>
      </div>

      {/* Grid Skeleton */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {[...Array(10)].map((_, i) => (
          <Panel key={i} className="space-y-4 bg-white/[0.02] p-4">
            <P className="w-10 h-10 rounded-lg" />
            <div className="space-y-2">
              <P className="h-3 w-24" />
              <P className="h-2 w-full opacity-20" />
              <P className="h-2 w-3/4 opacity-20" />
            </div>
            <div className="flex justify-between items-center pt-2">
              <P className="h-5 w-12 rounded-full opacity-20" />
              <P className="h-3 w-3 rounded-full opacity-20" />
            </div>
          </Panel>
        ))}
      </div>
    </div>
  </div>
);
