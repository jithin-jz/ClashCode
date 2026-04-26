import React from "react";
import { P } from "../SkeletonPrimitives";

export const AchievementsSkeleton = () => (
  <div className="min-h-screen bg-black">
    <div className="max-w-[1200px] mx-auto px-6 pt-12 pb-24 space-y-12">
      {/* Header Skeleton */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
        <div className="space-y-4">
          <P className="h-4 w-20 opacity-20" />
          <P className="h-12 w-80" />
          <P className="h-4 w-64 opacity-20" />
        </div>
        <div className="flex gap-8">
          <div className="space-y-2">
            <P className="h-3 w-16 opacity-20" />
            <P className="h-8 w-24" />
          </div>
          <div className="space-y-2">
            <P className="h-3 w-16 opacity-20" />
            <P className="h-8 w-24" />
          </div>
        </div>
      </div>

      {/* Grid Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="bg-white/[0.02] border border-white/5 rounded-xl p-4 space-y-4"
          >
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
          </div>
        ))}
      </div>
    </div>
  </div>
);
