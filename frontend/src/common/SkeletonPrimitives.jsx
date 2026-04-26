import React from "react";
import { Skeleton } from "boneyard-js/react";
import { cn } from "../lib/utils";

/**
 * Shimmer Effect component
 * Industrial Standard: Smooth, translucent CSS animation
 */
export const Shimmer = () => (
  <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
    <div className="absolute inset-0 -translate-x-full animate-[shimmer_2.5s_infinite] bg-linear-to-r from-transparent via-white/[0.03] to-transparent" />
    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.02] mix-blend-overlay" />
  </div>
);

/**
 * AutoSkeleton Wrapper
 * Uses boneyard-js for pixel-perfect skeleton generation
 */
export const AutoSkeleton = ({ name, loading, children, className }) => {
  return (
    <Skeleton name={name} loading={loading} className={className}>
      {children}
    </Skeleton>
  );
};

/**
 * Base Skeleton component with layout and shimmer
 */
export const SkeletonBase = ({ className, children, ...props }) => {
  return (
    <div
      className={cn(
        "relative overflow-hidden bg-white/[0.015] border border-white/[0.03] rounded-2xl backdrop-blur-sm",
        className,
      )}
      {...props}
    >
      <Shimmer />
      <div className="relative z-10 w-full h-full">{children}</div>
    </div>
  );
};

/* --- Specialized Primitives (Maintained for Legacy/Explicit cases) --- */

export const SkeletonCircle = ({ className, ...props }) => (
  <SkeletonBase
    className={cn("rounded-full aspect-square", className)}
    {...props}
  />
);

export const SkeletonText = ({
  className,
  width = "100%",
  height = "1rem",
  ...props
}) => (
  <SkeletonBase
    className={cn("rounded-lg", className)}
    style={{ width, height, ...props.style }}
    {...props}
  />
);

export const SkeletonButton = ({ className, ...props }) => (
  <SkeletonBase
    className={cn("h-12 w-full rounded-2xl", className)}
    {...props}
  />
);

export const SkeletonAvatar = ({ size = "md", className, ...props }) => {
  const sizes = {
    sm: "w-8 h-8",
    md: "w-12 h-12",
    lg: "w-16 h-16",
    xl: "w-24 h-24",
  };
  return <SkeletonCircle className={cn(sizes[size], className)} {...props} />;
};

export const SkeletonCard = ({
  className,
  children,
  variant = "solid",
  ...props
}) => {
  const variants = {
    glass:
      "bg-white/[0.02] backdrop-blur-xl border border-white/[0.05] shadow-[0_20px_50px_rgba(0,0,0,0.5)]",
    solid: "bg-black/60 border border-white/[0.05] backdrop-blur-md shadow-xl",
    plain: "bg-transparent border border-white/[0.02]",
  };

  return (
    <div
      className={cn(
        "p-5 rounded-[2rem] relative overflow-hidden",
        variants[variant],
        className,
      )}
      {...props}
    >
      <Shimmer />
      <div className="relative z-10 w-full h-full">{children}</div>
    </div>
  );
};

/* --- Complex Primitives --- */

export const SkeletonCode = ({ lines = 12, className, ...props }) => {
  const lineWidths = [85, 60, 45, 70, 90, 55, 75, 40, 80, 65, 50, 95];

  return (
    <div
      className={cn(
        "bg-black/40 backdrop-blur-xl rounded-[1.5rem] border border-white/[0.05] overflow-hidden font-mono",
        className,
      )}
      {...props}
    >
      <div className="flex">
        <div className="w-12 bg-white/[0.01] border-r border-white/5 py-5 px-3 flex flex-col gap-3">
          {[...Array(lines)].map((_, i) => (
            <div key={i} className="h-3 w-6 bg-white/[0.03] rounded-sm" />
          ))}
        </div>
        <div className="flex-1 p-5 space-y-3 relative overflow-hidden">
          <Shimmer />
          {[...Array(lines)].map((_, i) => (
            <div
              key={i}
              className="h-3 bg-white/[0.04] rounded-sm"
              style={{ width: `${lineWidths[i % lineWidths.length]}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export const SkeletonStats = ({ className, ...props }) => (
  <SkeletonCard
    className={cn("flex flex-col gap-4 bg-white/[0.01]", className)}
    {...props}
  >
    <SkeletonText width="60%" height="0.65rem" className="opacity-40" />
    <SkeletonText width="40%" height="2rem" className="opacity-80" />
    <div className="h-2 w-full bg-white/[0.02] rounded-full overflow-hidden mt-1 relative">
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 via-emerald-500/20 to-transparent w-2/3" />
    </div>
  </SkeletonCard>
);

/* --- Layout Wrapper --- */

export const SkeletonPage = ({ children, className }) => (
  <div className={cn("w-full text-zinc-400 relative bg-black", className)}>
    {/* Background Decoration to match Home/Achievements */}
    <div className="fixed inset-0 z-0 pointer-events-none">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-purple-600/5 blur-[120px] rounded-full opacity-30" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-emerald-500/5 blur-[100px] rounded-full opacity-20" />
    </div>

    <div className="relative z-10 w-full">{children}</div>

    <style>{`
      @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
      }
    `}</style>
  </div>
);

/* --- High-Level Page Skeletons --- */

export const SkeletonAdminDashboard = () => (
  <SkeletonPage className="p-6 bg-[#000000] space-y-8">
    <div className="flex justify-between items-center">
      <SkeletonText width="250px" height="2rem" />
      <div className="flex gap-4">
        <SkeletonBase className="h-10 w-32 rounded-xl" />
        <SkeletonBase className="h-10 w-10 rounded-xl" />
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <SkeletonStats key={i} />
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <SkeletonCard className="lg:col-span-2 h-[400px]" />
      <SkeletonCard className="h-[400px]" />
    </div>
  </SkeletonPage>
);

export const SkeletonGenericPage = () => (
  <SkeletonPage className="p-8 space-y-8 bg-[#000000]">
    <div className="space-y-4">
      <SkeletonText width="300px" height="2.5rem" />
      <SkeletonText width="500px" height="1.1rem" className="opacity-40" />
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      {[...Array(3)].map((_, i) => (
        <SkeletonCard key={i} className="h-64" />
      ))}
    </div>
    <SkeletonCard className="h-96" />
  </SkeletonPage>
);

export { Skeleton };
