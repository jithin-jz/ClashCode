import React from "react";
import { P, Panel } from "../SkeletonPrimitives";

export const MarketplaceSkeleton = () => (
  <div className="relative flex min-h-screen w-full flex-col bg-black pb-20 text-white sm:pb-0">
    <div className="sticky top-14 z-20 border-b border-[#1e1e1e] bg-[#0a0a0a]/95 backdrop-blur-xl">
      <div className="w-full px-4 sm:px-8 lg:px-10">
        <div className="flex items-center gap-2 py-2 sm:gap-4 sm:py-3">
          <P className="h-8 w-8 rounded-md shrink-0" />
          <div className="hidden h-4 w-px shrink-0 bg-[#222] sm:block" />
          <div className="flex flex-1 items-center gap-1 overflow-hidden sm:gap-1.5">
            {[...Array(4)].map((_, i) => (
              <P
                key={i}
                className="h-8 flex-1 rounded-md sm:w-20 sm:flex-none"
              />
            ))}
          </div>
          <P className="ml-1 h-8 w-10 shrink-0 rounded-md" />
        </div>
      </div>
    </div>
    <main className="relative z-10 w-full px-4 py-0 sm:px-8 lg:px-10">
      <div className="grid min-h-[calc(100vh-8rem)] grid-cols-1 items-stretch gap-6 lg:grid-cols-12">
        <div className="order-2 py-4 lg:order-1 lg:col-span-9">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[...Array(8)].map((_, i) => (
              <Panel
                key={i}
                className="flex h-full flex-col overflow-hidden rounded-lg border-[#1a1a1a] bg-[#0d0d0d]"
              >
                <div className="relative h-28 shrink-0 border-b border-[#1a1a1a] bg-black">
                  <P className="absolute left-2 top-2 h-5 w-16 rounded-sm opacity-70" />
                  <P className="mx-auto mt-8 h-10 w-10 rounded-lg" />
                  <P className="absolute right-2 top-2 h-5 w-12 rounded-sm opacity-70" />
                </div>
                <div className="flex flex-1 flex-col p-3">
                  <P className="h-3 w-3/4 rounded-sm" />
                  <P className="mt-2 h-2 w-full rounded-sm opacity-70" />
                  <P className="mt-1.5 h-2 w-2/3 rounded-sm opacity-60" />
                </div>
                <div className="px-3.5 pb-3.5 pt-1">
                  <P className="h-8 w-full rounded-md" />
                </div>
              </Panel>
            ))}
          </div>
        </div>

        <aside className="order-1 py-4 lg:order-2 lg:col-span-3">
          <Panel className="flex h-[12.5cm] flex-col overflow-hidden border-[#1a1a1a] bg-[#0d0d0d]">
            <div className="relative flex h-40 shrink-0 items-center justify-center border-b border-[#1a1a1a] bg-black">
              <P className="h-14 w-14 rounded-xl" />
              <P className="absolute left-3 top-3 h-5 w-16 rounded-sm opacity-60" />
            </div>
            <div className="border-b border-white/5 p-4">
              <div className="mb-2 flex items-center justify-between">
                <P className="h-3 w-28 rounded-sm" />
                <P className="h-7 w-24 rounded-md" />
              </div>
              <P className="h-2.5 w-44 rounded-sm opacity-60" />
            </div>
            <div className="flex-1 space-y-6 p-4">
              <div className="flex items-center justify-between">
                {[...Array(3)].map((_, index) => (
                  <React.Fragment key={index}>
                    <P className="h-3 w-16 rounded-sm" />
                    {index < 2 && <div className="mx-1 h-px w-4 bg-white/5" />}
                  </React.Fragment>
                ))}
              </div>
              <div className="space-y-2">
                <P className="h-3 w-20 rounded-sm" />
                <P className="h-11 w-full rounded-lg" />
              </div>
              <div className="space-y-2">
                <P className="h-3 w-24 rounded-sm" />
                <div className="flex gap-2">
                  <P className="h-9 flex-1 rounded-lg" />
                  <P className="h-9 w-14 rounded-md" />
                </div>
              </div>
            </div>
          </Panel>
        </aside>
      </div>
    </main>
  </div>
);
