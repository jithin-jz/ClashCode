import React from "react";
import { P, Circle } from "../SkeletonPrimitives";

export const LandingSkeleton = () => (
  <div className="w-full min-h-screen bg-black">
    {/* Hero Section */}
    <section className="flex flex-col items-center justify-center px-5 py-24 space-y-8">
      <div className="max-w-4xl w-full text-center space-y-6">
        <P className="h-16 sm:h-20 w-3/4 mx-auto" />
        <P className="h-4 w-1/2 mx-auto opacity-40" />
        <P className="h-12 w-48 mx-auto rounded-xl" />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl mt-12">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="bg-white/[0.02] border border-white/5 rounded-xl p-5 text-center space-y-2"
          >
            <P className="h-2 w-16 mx-auto opacity-40" />
            <P className="h-6 w-24 mx-auto" />
          </div>
        ))}
      </div>
    </section>

    {/* Features Section */}
    <section className="max-w-5xl mx-auto px-5 pb-24 grid grid-cols-1 lg:grid-cols-2 gap-12">
      <div className="space-y-4">
        <P className="h-3 w-32 mb-6" />
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="bg-white/[0.02] border border-white/5 rounded-xl p-6 flex gap-4"
          >
            <Circle className="w-9 h-9 rounded-lg shrink-0" />
            <div className="space-y-2 flex-1">
              <P className="h-3.5 w-32" />
              <P className="h-3 w-full opacity-40" />
            </div>
          </div>
        ))}
      </div>
      <div className="space-y-4">
        <div className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden">
          <div className="h-10 border-b border-white/10 px-4 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
              <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
              <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
            </div>
          </div>
          <div className="p-6 space-y-3">
            <P className="h-3 w-full opacity-60" />
            <P className="h-3 w-4/5 opacity-50" />
            <P className="h-3 w-5/6 opacity-40" />
            <P className="h-3 w-3/4 opacity-30" />
            <div className="pt-4">
              <P className="h-32 w-full rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
);
