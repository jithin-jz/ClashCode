import React from "react";
import { P, Circle, Panel } from "../SkeletonPrimitives";

const TRACKS = [
  { cards: 10, width: "w-28" },
  { cards: 10, width: "w-32" },
  { cards: 10, width: "w-28" },
  { cards: 10, width: "w-36" },
  { cards: 10, width: "w-32" },
  { cards: 10, width: "w-28" },
];

export const HomeSkeleton = () => (
  <div className="w-full min-h-screen bg-black pb-20 sm:pb-0">
    <div className="w-full px-3 sm:px-5">
      <div className="space-y-0.5 pb-4">
        <div className="px-4 pb-4 pt-4">
          <Panel className="flex flex-col gap-5 border-white/60 bg-black p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <P className="h-8 w-8 shrink-0 rounded-lg" />
              <div className="min-w-0 space-y-1.5 pt-0.5">
                <P className="h-2.5 w-24 rounded-sm" />
                <P className="h-3.5 w-32 rounded-sm" />
              </div>
            </div>
            <div className="flex flex-1 flex-col gap-2 sm:max-w-[300px]">
              <div className="flex items-end justify-between">
                <P className="h-4 w-32 rounded-sm" />
                <P className="h-3 w-8 rounded-sm" />
              </div>
              <P className="h-1.5 w-full rounded-full" />
            </div>
          </Panel>
        </div>

        {TRACKS.map((track, trackIdx) => (
          <section key={trackIdx} className="px-4 py-4 sm:px-4">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="mb-1 flex items-center gap-2">
                  <P className={`h-4 ${track.width} rounded-sm`} />
                  {trackIdx % 3 === 0 && (
                    <P className="h-5 w-12 rounded-full" />
                  )}
                </div>
                <P className="h-3 w-64 max-w-[58vw] rounded-sm opacity-80" />
              </div>
              <div className="shrink-0 space-y-1.5 text-right">
                <P className="ml-auto h-3 w-10 rounded-sm" />
                <P className="h-1.5 w-20 rounded-full" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {[...Array(track.cards)].map((_, i) => (
                <Panel
                  key={i}
                  className="min-h-[120px] border-white/20 bg-white/[0.01] p-3.5"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-start gap-2.5">
                      <P className="h-8 w-8 shrink-0 rounded-lg" />
                      <div className="space-y-1.5">
                        <P className="h-2.5 w-14 rounded-sm opacity-80" />
                        <P className="h-3.5 w-20 rounded-sm" />
                      </div>
                    </div>
                    <Circle className="h-4 w-4" />
                  </div>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <P className="h-4 w-14 rounded-full" />
                      <P className="h-3 w-10 rounded-sm opacity-60" />
                    </div>
                    <div className="flex gap-0.5">
                      <Circle className="h-2.5 w-2.5 opacity-70" />
                      <Circle className="h-2.5 w-2.5 opacity-70" />
                      <Circle className="h-2.5 w-2.5 opacity-70" />
                    </div>
                  </div>
                </Panel>
              ))}
            </div>
          </section>
        ))}

        <section className="px-4 pb-12 pt-4 sm:px-4">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="min-w-0 space-y-2">
              <P className="h-4 w-36 rounded-sm" />
              <P className="h-3 w-52 rounded-sm opacity-80" />
            </div>
            <P className="h-6 w-24 rounded-full" />
          </div>
          <Panel className="p-4">
            <div className="flex items-start gap-4">
              <P className="h-10 w-10 shrink-0 rounded-lg" />
              <div className="min-w-0 space-y-2 pt-0.5">
                <P className="h-3 w-24 rounded-sm" />
                <P className="h-4 w-56 max-w-[60vw] rounded-sm" />
                <P className="h-3 w-72 max-w-[70vw] rounded-sm opacity-70" />
              </div>
            </div>
            <div className="mt-6 space-y-2.5">
              <div className="flex justify-between">
                <P className="h-3 w-32 rounded-sm opacity-70" />
                <P className="h-6 w-9 rounded-md" />
              </div>
              <P className="h-1.5 w-full rounded-full" />
            </div>
          </Panel>
        </section>
      </div>
    </div>
  </div>
);
