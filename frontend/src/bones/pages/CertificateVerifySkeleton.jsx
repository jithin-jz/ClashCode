import React from "react";
import { P, Panel, Circle } from "../SkeletonPrimitives";

export const CertificateVerifySkeleton = () => (
  <div className="flex h-screen w-screen flex-col overflow-hidden bg-zinc-950 p-2 text-zinc-200 md:p-4 lg:p-6">
    <div className="relative z-10 mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col gap-3 overflow-hidden px-2">
      <Panel className="flex shrink-0 items-center justify-between gap-3 rounded-xl bg-zinc-900/40 p-3">
        <div className="flex items-center gap-3">
          <P className="h-10 w-10 rounded-lg" />
          <div className="space-y-1.5">
            <P className="h-5 w-40 rounded-sm" />
            <P className="h-3 w-32 rounded-sm opacity-60" />
          </div>
        </div>
        <P className="hidden h-6 w-28 rounded-full sm:block" />
      </Panel>

      <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-hidden lg:grid-cols-12">
        <Panel className="relative flex min-h-0 items-center justify-center overflow-hidden rounded-xl bg-zinc-900/20 p-2 lg:col-span-8">
          <div className="aspect-[1.414/1] w-full max-w-[760px] rounded-lg border border-white/10 bg-black/40 p-5">
            <div className="h-full rounded-md border border-white/10 p-6">
              <P className="mx-auto h-8 w-48 rounded-sm" />
              <P className="mx-auto mt-8 h-12 w-80 max-w-full rounded-sm" />
              <div className="mt-10 grid grid-cols-2 gap-6">
                <P className="h-4 rounded-sm" />
                <P className="h-4 rounded-sm" />
              </div>
              <P className="mx-auto mt-12 h-24 w-24 rounded-full" />
            </div>
          </div>
        </Panel>

        <aside className="flex min-h-0 flex-col gap-3 overflow-hidden lg:col-span-4">
          <Panel className="space-y-4 rounded-xl bg-zinc-900/40 p-4">
            <P className="h-3 w-28 rounded-sm opacity-60" />
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {[...Array(3)].map((_, index) => (
                <div key={index} className="space-y-1.5">
                  <P className="h-2.5 w-20 rounded-sm opacity-50" />
                  <P className="h-4 w-36 rounded-sm" />
                </div>
              ))}
            </div>
            <div className="h-px bg-white/5" />
            <div className="space-y-2">
              <P className="h-2.5 w-16 rounded-sm opacity-50" />
              <P className="h-9 w-full rounded-lg" />
            </div>
            <div className="grid grid-cols-2 gap-2 border-t border-white/5 pt-3">
              <P className="h-10 rounded-lg" />
              <P className="h-10 rounded-lg" />
            </div>
          </Panel>

          <Panel className="hidden flex-1 items-center justify-center gap-3 rounded-xl border-emerald-500/10 bg-emerald-500/[0.03] p-4 text-center sm:flex">
            <Circle className="h-10 w-10 shrink-0" />
            <P className="h-5 w-48 rounded-sm" />
          </Panel>
        </aside>
      </main>

      <div className="shrink-0 border-t border-white/5 py-2 text-center">
        <P className="mx-auto h-2 w-56 rounded-sm opacity-50" />
      </div>
    </div>
  </div>
);
