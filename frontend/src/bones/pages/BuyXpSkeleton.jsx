import React from "react";
import { P } from "../SkeletonPrimitives";

export const BuyXpSkeleton = () => (
  <div className="min-h-screen bg-black p-6 space-y-8">
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-2">
        <P className="h-8 w-48" />
        <P className="h-3 w-72 opacity-40" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="bg-[#0d0d0d] border border-white/5 rounded-2xl p-6 space-y-4"
          >
            <P className="h-12 w-12 rounded-xl" />
            <P className="h-5 w-20" />
            <P className="h-8 w-24" />
            <P className="h-3 w-full opacity-40" />
            <P className="h-12 w-full rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  </div>
);
