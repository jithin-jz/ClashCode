import React from "react";
import { P } from "../SkeletonPrimitives";

export const AdminSkeleton = () => (
  <div className="min-h-screen bg-[#000] p-6 space-y-8">
    <div className="flex justify-between items-center">
      <P className="h-8 w-56" />
      <div className="flex gap-3">
        <P className="h-10 w-32 rounded-xl" />
        <P className="h-10 w-10 rounded-xl" />
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="bg-white/[0.015] border border-white/[0.03] rounded-2xl p-5 space-y-3"
        >
          <P className="h-2.5 w-20 opacity-40" />
          <P className="h-8 w-16" />
          <div className="h-1.5 w-full bg-white/[0.02] rounded-full">
            <P
              className="h-full rounded-full"
              style={{ width: `${30 + i * 15}%` }}
            />
          </div>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <P className="lg:col-span-2 h-[400px] rounded-2xl" />
      <P className="h-[400px] rounded-2xl" />
    </div>
  </div>
);
