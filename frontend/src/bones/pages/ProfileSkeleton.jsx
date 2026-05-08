import React from "react";
import { P, Circle, Panel } from "../SkeletonPrimitives";

export const ProfileSkeleton = () => (
  <div className="relative flex min-h-screen w-full flex-col bg-black pb-20 text-white sm:pb-0">
    <main className="relative z-10 flex-1 px-4 py-4 sm:px-10 lg:px-14">
      <div className="grid w-full grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="min-w-0 space-y-6 lg:col-span-4">
          <Panel className="overflow-visible bg-[#0a0a0a]/80">
            <div className="relative">
              <P className="h-40 rounded-b-none rounded-t-xl" />
              <div className="absolute left-3 top-3 flex w-[calc(100%-1.5rem)] items-center justify-between">
                <P className="h-8 w-8 rounded-lg" />
                <div className="flex gap-2">
                  <P className="h-8 w-8 rounded-lg" />
                  <P className="h-8 w-8 rounded-lg" />
                </div>
              </div>
              <div className="absolute bottom-0 left-1/2 translate-y-1/2 -translate-x-1/2">
                <Circle className="h-28 w-28 border-[6px] border-[#050505]" />
              </div>
            </div>
            <div className="flex flex-col items-center px-6 pb-6 pt-20 text-center">
              <P className="mb-2 h-8 w-48 max-w-full rounded-md" />
              <P className="mb-5 h-3 w-28 rounded-sm opacity-70" />
              <div className="mb-4 flex items-center justify-center gap-2">
                {[...Array(4)].map((_, index) => (
                  <Circle key={index} className="h-4 w-4" />
                ))}
              </div>
              <div className="mb-4 flex w-full justify-center gap-8 border-t border-white/5 pt-3">
                {[...Array(2)].map((_, index) => (
                  <div key={index} className="space-y-1.5 text-center">
                    <P className="mx-auto h-5 w-9 rounded-sm" />
                    <P className="h-3 w-16 rounded-sm opacity-70" />
                  </div>
                ))}
              </div>
              <P className="h-10 w-full rounded-xl" />
            </div>
          </Panel>
        </div>

        <div className="min-w-0 space-y-6 lg:col-span-6">
          <Panel className="overflow-hidden bg-zinc-900/50">
            <div className="flex items-center justify-between border-b border-white/5 p-4">
              <div className="flex items-center gap-2">
                <P className="h-4 w-4 rounded-sm" />
                <P className="h-4 w-32 rounded-sm" />
              </div>
              <P className="h-3 w-24 rounded-sm" />
            </div>
            <div className="p-4">
              <div className="flex gap-1 overflow-hidden">
                {[...Array(34)].map((_, week) => (
                  <div key={week} className="flex shrink-0 flex-col gap-1">
                    {[...Array(7)].map((_, day) => (
                      <P key={day} className="h-2.5 w-2.5 rounded-[1px]" />
                    ))}
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-4">
                <P className="h-3 w-40 rounded-sm" />
                <P className="h-3 w-24 rounded-sm" />
              </div>
            </div>
          </Panel>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <P className="h-6 w-1.5 rounded-full" />
              <P className="h-6 w-32 rounded-sm" />
              <P className="h-5 w-20 rounded-lg" />
            </div>
            <P className="h-9 w-28 rounded-xl" />
          </div>

          <div className="grid grid-cols-3 gap-1 md:gap-4">
            {[...Array(9)].map((_, index) => (
              <P key={index} className="aspect-square rounded-md" />
            ))}
          </div>

          {[...Array(2)].map((_, i) => (
            <Panel key={i} className="space-y-3 bg-[#0a0a0a]/60 p-4 md:hidden">
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
            </Panel>
          ))}
        </div>

        <div className="hidden space-y-6 lg:col-span-2 lg:block">
          <Panel className="bg-[#0a0a0a]/60">
            <div className="border-b border-white/5 p-3">
              <P className="h-3 w-32 rounded-sm" />
            </div>
            <div className="space-y-3 p-3">
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
          </Panel>
        </div>
      </div>
    </main>
  </div>
);
