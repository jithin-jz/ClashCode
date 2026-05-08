import React from "react";
import { P, Circle, Panel } from "../SkeletonPrimitives";

export const AdminSkeleton = () => (
  <div className="relative h-screen overflow-hidden bg-black font-sans text-foreground">
    <div className="relative z-10 flex h-full flex-col md:flex-row">
      <aside className="w-full shrink-0 border-b border-white/8 bg-black/95 md:h-full md:w-64 md:border-b-0 md:border-r">
        <div className="flex h-14 items-center justify-between border-b border-white/8 px-4 md:px-6">
          <div className="flex items-center gap-2">
            <P className="h-5 w-5 rounded-md" />
            <P className="h-4 w-24 rounded-sm" />
          </div>
          <div className="flex gap-2 md:hidden">
            <P className="h-8 w-20 rounded-md" />
            <P className="h-8 w-16 rounded-md" />
          </div>
        </div>
        <nav className="overflow-x-auto p-2 md:overflow-y-auto md:p-3">
          <div className="mb-2 hidden px-3 md:block">
            <P className="h-3 w-20 rounded-sm" />
          </div>
          <div className="flex min-w-max gap-1 md:block md:min-w-0 md:space-y-1">
            {[...Array(8)].map((_, index) => (
              <div
                key={index}
                className={`flex shrink-0 items-center gap-2.5 rounded-lg border px-3 py-2 md:w-full ${
                  index === 0
                    ? "border-white/12 bg-white/[0.045]"
                    : "border-transparent"
                }`}
              >
                <P className="h-4 w-4 rounded-md" />
                <P className="h-4 w-20 rounded-sm" />
              </div>
            ))}
          </div>
        </nav>
        <div className="hidden border-t border-white/8 p-4 md:block">
          <div className="mb-4 flex items-center gap-3 px-2">
            <Circle className="h-8 w-8" />
            <div className="min-w-0 space-y-1.5">
              <P className="h-3 w-24 rounded-sm" />
              <P className="h-2.5 w-20 rounded-sm opacity-60" />
            </div>
          </div>
          <div className="space-y-2">
            <P className="h-9 w-full rounded-md" />
            <P className="h-9 w-full rounded-md" />
          </div>
        </div>
      </aside>

      <main className="h-full min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl space-y-6 p-3 sm:p-6 lg:p-8">
          <Panel className="p-4 sm:p-6">
            <div className="mb-6 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
              <P className="h-5 w-36 rounded-sm" />
              <P className="h-6 w-28 rounded-md" />
            </div>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
              {[...Array(6)].map((_, index) => (
                <Panel
                  key={index}
                  className="space-y-2 rounded-lg p-3 text-center"
                >
                  <P className="mx-auto h-2.5 w-16 rounded-sm opacity-70" />
                  <P className="mx-auto h-7 w-12 rounded-sm" />
                </Panel>
              ))}
            </div>
            <div className="mt-6 flex flex-col justify-between gap-3 border-t border-white/8 pt-4 sm:flex-row sm:items-center">
              <P className="h-3 w-56 rounded-sm" />
              <P className="h-8 w-24 rounded-md" />
            </div>
          </Panel>

          <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <P className="h-10 w-full rounded-lg sm:w-72" />
              <div className="flex gap-2">
                <P className="h-10 w-28 rounded-lg" />
                <P className="h-10 w-24 rounded-lg" />
              </div>
            </div>
            <Panel className="hidden overflow-hidden md:block">
              <div className="grid grid-cols-6 gap-4 border-b border-white/8 p-4">
                {[...Array(6)].map((_, index) => (
                  <P key={index} className="h-3 w-full rounded-sm" />
                ))}
              </div>
              {[...Array(7)].map((_, row) => (
                <div
                  key={row}
                  className="grid grid-cols-6 gap-4 border-b border-white/[0.04] p-4 last:border-b-0"
                >
                  {[...Array(6)].map((_, col) => (
                    <P key={col} className="h-4 w-full rounded-sm opacity-80" />
                  ))}
                </div>
              ))}
            </Panel>
            <div className="space-y-3 md:hidden">
              {[...Array(4)].map((_, index) => (
                <Panel key={index} className="space-y-4 p-4">
                  <div className="flex items-center gap-3">
                    <Circle className="h-10 w-10" />
                    <div className="flex-1 space-y-2">
                      <P className="h-4 w-32 rounded-sm" />
                      <P className="h-3 w-20 rounded-sm opacity-60" />
                    </div>
                    <P className="h-8 w-8 rounded-md" />
                  </div>
                  <P className="h-3 w-full rounded-sm" />
                  <P className="h-3 w-3/4 rounded-sm opacity-70" />
                </Panel>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
);
