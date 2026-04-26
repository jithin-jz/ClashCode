import React from "react";
import { P } from "../SkeletonPrimitives";

export const MarketplaceSkeleton = () => (
  <div className="w-full min-h-screen bg-black pb-20">
    <div className="sticky top-14 z-20 border-b border-[#1e1e1e] bg-[#0a0a0a] px-4 sm:px-6">
      <div className="flex items-center gap-3 py-2.5">
        <P className="h-8 w-8 rounded-md shrink-0" />
        <div className="h-4 w-px bg-white/5 shrink-0" />
        {[...Array(4)].map((_, i) => (
          <P key={i} className="h-8 w-20 rounded-md shrink-0" />
        ))}
        <P className="h-8 w-8 rounded-md ml-auto shrink-0" />
      </div>
    </div>
    <div className="px-4 sm:px-6 lg:px-8 py-6">
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="bg-[#0d0d0d] border border-[#1a1a1a] rounded-lg overflow-hidden"
          >
            <P className="h-28 rounded-none" />
            <div className="p-3 space-y-2">
              <P className="h-3 w-3/4" />
              <P className="h-2 w-full opacity-40" />
              <P className="h-2 w-2/3 opacity-30" />
            </div>
            <div className="px-3.5 pb-3.5">
              <P className="h-8 w-full rounded-md" />
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);
