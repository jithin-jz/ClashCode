import React from "react";
import { P, Panel } from "../SkeletonPrimitives";

export const BuyXpSkeleton = () => (
  <div className="relative flex min-h-screen w-full flex-col bg-black pb-20 text-white sm:pb-0">
    <main className="relative z-10 flex-1 w-full min-w-0 px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {[...Array(8)].map((_, i) => (
          <Panel
            key={i}
            className={`relative flex min-h-[274px] flex-col overflow-hidden rounded-xl p-5 ${
              i === 4
                ? "border-[#ffa116]/30 bg-[#ffa116]/[0.035]"
                : i === 6
                  ? "border-[#00af9b]/30 bg-[#00af9b]/[0.035]"
                  : "bg-[#141414]/70"
            }`}
          >
            {(i === 4 || i === 6) && (
              <P className="absolute right-3 top-3 h-5 w-16 rounded-md" />
            )}
            <P className="mb-4 h-10 w-10 rounded-lg" />
            <P className="h-5 w-20 rounded-sm" />
            <P className="mt-3 h-9 w-24 rounded-sm" />
            <div className="mt-auto space-y-4 pt-6">
              <div className="flex items-center gap-1.5">
                <CircleDot />
                <P className="h-3 w-20 rounded-sm" />
              </div>
              <P className="h-10 w-full rounded-lg" />
            </div>
          </Panel>
        ))}
      </div>
    </main>
  </div>
);

const CircleDot = () => <P className="h-3.5 w-3.5 rounded-full" />;
