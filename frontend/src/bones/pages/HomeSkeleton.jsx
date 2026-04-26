import React from "react";
import { P, Circle } from "../SkeletonPrimitives";

export const HomeSkeleton = () => (
  <div className="w-full min-h-screen bg-black">
    <div className="w-full px-3 sm:px-5 py-4 max-w-5xl mx-auto space-y-8">
      {/* Platform Status Card */}
      <div className="px-4">
        <div className="bg-[#111] border border-white/10 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
          <div className="flex items-start gap-3">
            <Circle className="w-8 h-8 rounded-lg" />
            <div className="space-y-1.5">
              <P className="h-2 w-20" />
              <P className="h-3 w-32" />
            </div>
          </div>
          <div className="flex-1 max-w-[300px] space-y-2">
            <div className="flex justify-between">
              <P className="h-3 w-24" />
              <P className="h-3 w-8" />
            </div>
            <P className="h-1.5 w-full rounded-full" />
          </div>
        </div>
      </div>

      {/* Track Sections */}
      {[...Array(2)].map((_, trackIdx) => (
        <section key={trackIdx} className="px-4 space-y-4">
          {/* Track Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <P className="h-4 w-32" />
                <P className="h-4 w-12 rounded-full" />
              </div>
              <P className="h-3 w-64 opacity-50" />
            </div>
            <div className="text-right space-y-1.5">
              <P className="h-2 w-12 ml-auto" />
              <P className="h-1.5 w-20 rounded-full" />
            </div>
          </div>

          {/* Card Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {[...Array(4 + trackIdx * 2)].map((_, i) => (
              <div
                key={i}
                className="bg-white/[0.02] border border-white/5 rounded-xl p-3.5 min-h-[120px] space-y-4"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-2.5">
                    <Circle className="w-8 h-8 rounded-lg" />
                    <div className="space-y-1.5">
                      <P className="h-2 w-12 opacity-40" />
                      <P className="h-3 w-20" />
                    </div>
                  </div>
                  <Circle className="w-4 h-4" />
                </div>
                <div className="flex items-center gap-1.5 pt-1">
                  <P className="h-4 w-14 rounded-full" />
                  <P className="h-3 w-10 opacity-30" />
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}

      {/* Certificate Section */}
      <div className="px-4 pb-20">
        <div className="bg-[#111] border border-white/5 rounded-xl p-6 space-y-6">
          <div className="flex items-start gap-4">
            <Circle className="w-10 h-10 rounded-lg" />
            <div className="space-y-1.5">
              <P className="h-2 w-24 opacity-40" />
              <P className="h-4 w-48" />
              <P className="h-3 w-64 opacity-30" />
            </div>
          </div>
          <div className="space-y-2.5">
            <div className="flex justify-between">
              <P className="h-3 w-32 opacity-40" />
              <P className="h-3 w-10" />
            </div>
            <P className="h-1.5 w-full rounded-full" />
          </div>
        </div>
      </div>
    </div>
  </div>
);
