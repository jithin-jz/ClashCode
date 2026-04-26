import React from "react";
import { P, Circle } from "../SkeletonPrimitives";

export const ProfileSkeleton = () => (
  <div className="w-full min-h-screen bg-black pb-20">
    <div className="max-w-5xl mx-auto px-4 py-4 grid grid-cols-1 lg:grid-cols-4 gap-6">
      <div className="lg:col-span-1 space-y-4">
        <div className="rounded-xl bg-[#141414] border border-white/5 overflow-hidden">
          <P className="h-32 rounded-none" />
          <div className="px-6 pb-6 pt-2 flex flex-col items-center gap-3 -mt-10">
            <Circle className="w-20 h-20 border-4 border-black" />
            <P className="h-4 w-32" />
            <P className="h-3 w-48 opacity-40" />
            <div className="flex gap-8 pt-3 border-t border-white/5 w-full justify-center">
              <div className="text-center space-y-1">
                <P className="h-5 w-8 mx-auto" />
                <P className="h-2 w-14 opacity-30" />
              </div>
              <div className="text-center space-y-1">
                <P className="h-5 w-8 mx-auto" />
                <P className="h-2 w-14 opacity-30" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <P className="h-9 w-24 rounded-lg" />
          <P className="h-9 w-32 rounded-lg" />
        </div>
        <P className="h-24 w-full rounded-xl" />
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="bg-[#141414] border border-white/5 rounded-xl p-4 space-y-3"
          >
            <div className="flex items-center gap-3">
              <Circle className="w-9 h-9 shrink-0" />
              <div className="space-y-1.5 flex-1">
                <P className="h-3 w-24" />
                <P className="h-2 w-16 opacity-40" />
              </div>
            </div>
            <P className="h-3 w-full" />
            <P className="h-3 w-4/5 opacity-60" />
            <P className="h-40 w-full rounded-lg" />
          </div>
        ))}
      </div>
      <div className="lg:col-span-1">
        <div className="bg-[#141414] border border-white/5 rounded-xl p-4 space-y-4">
          <P className="h-3 w-32" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Circle className="w-8 h-8 shrink-0" />
              <div className="space-y-1.5 flex-1">
                <P className="h-3 w-24" />
                <P className="h-2 w-16 opacity-40" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);
