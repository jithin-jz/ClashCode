import React from "react";
import { P, Panel } from "../SkeletonPrimitives";

export const OAuthCallbackSkeleton = () => (
  <div className="flex min-h-screen items-center justify-center bg-black px-4 py-12">
    <div className="pointer-events-none absolute inset-0 ds-dot-grid opacity-50" />
    <Panel className="relative z-10 w-full max-w-[400px] space-y-6 p-6 pb-7">
      <div className="space-y-3 text-center">
        <P className="mx-auto h-3 w-24 rounded-sm opacity-60" />
        <P className="mx-auto h-8 w-64 max-w-full rounded-md" />
        <P className="mx-auto h-3 w-52 max-w-full rounded-sm opacity-60" />
      </div>
      <div className="space-y-4">
        <P className="h-11 w-full rounded-xl" />
        <P className="h-11 w-full rounded-xl" />
      </div>
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-white/5" />
        <P className="h-2 w-20 rounded-sm opacity-50" />
        <div className="h-px flex-1 bg-white/5" />
      </div>
      <div className="grid grid-cols-2 gap-2.5">
        <P className="h-11 rounded-xl" />
        <P className="h-11 rounded-xl" />
      </div>
    </Panel>
  </div>
);
