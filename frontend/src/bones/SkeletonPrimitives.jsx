import React from "react";

/**
 * Shared primitive components for high-fidelity skeleton screens.
 * These are the building blocks for layout-accurate loaders.
 */

export const P = ({ className = "", style }) => (
  <div
    aria-hidden="true"
    className={`ds-skeleton-bone rounded-lg ${className}`}
    style={style}
  />
);

export const Circle = ({ className = "", style }) => (
  <div
    aria-hidden="true"
    className={`ds-skeleton-bone rounded-full ${className}`}
    style={style}
  />
);

export const Panel = ({ children, className = "" }) => (
  <div className={`ds-skeleton-panel rounded-xl ${className}`}>{children}</div>
);

export const TopNavSkeleton = () => (
  <div className="h-14 border-b border-white/8 bg-black px-4 sm:px-8 lg:px-10">
    <div className="mx-auto flex h-full w-full items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <P className="h-8 w-8 rounded-lg" />
        <P className="hidden h-4 w-28 sm:block" />
      </div>
      <div className="hidden items-center gap-2 sm:flex">
        {[...Array(4)].map((_, index) => (
          <P key={index} className="h-8 w-20 rounded-lg" />
        ))}
      </div>
      <div className="flex items-center gap-2">
        <P className="h-8 w-8 rounded-lg" />
        <Circle className="h-8 w-8" />
      </div>
    </div>
  </div>
);

export const BottomNavSkeleton = () => (
  <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/8 bg-black px-5 sm:hidden">
    <div className="flex h-16 items-center justify-around">
      {[...Array(5)].map((_, index) => (
        <div key={index} className="flex h-10 w-12 flex-col items-center gap-1">
          <P className="h-5 w-5 rounded-md" />
          <P className="h-2 w-8 rounded-sm" />
        </div>
      ))}
    </div>
  </div>
);

export const FooterSkeleton = () => (
  <div className="w-full border-t border-white/10 bg-black px-7 py-3 sm:px-10 lg:px-14">
    <div className="flex items-center justify-between gap-4 overflow-hidden">
      <div className="flex items-center gap-3">
        <P className="h-3 w-24 rounded-sm" />
        <div className="h-3 w-px bg-white/10" />
        <div className="flex items-center gap-3">
          {[...Array(4)].map((_, index) => (
            <Circle key={index} className="h-3.5 w-3.5" />
          ))}
        </div>
      </div>
      <div className="hidden items-center gap-4 sm:flex">
        <P className="h-3 w-10 rounded-sm" />
        <P className="h-3 w-12 rounded-sm" />
        <P className="h-3 w-14 rounded-sm" />
      </div>
    </div>
  </div>
);
