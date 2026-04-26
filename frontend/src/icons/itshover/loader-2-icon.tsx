import { forwardRef, useImperativeHandle } from "react";
import type { AnimatedIconHandle, AnimatedIconProps } from "./types";
import { motion, useAnimate } from "motion/react";

const Loader2Icon = forwardRef<AnimatedIconHandle, AnimatedIconProps>(
  (
    { size = 24, color = "currentColor", strokeWidth = 2, className = "" },
    ref,
  ) => {
    const [scope, animate] = useAnimate();

    const start = async () => {
      await animate(
        scope.current,
        { rotate: 360 },
        {
          duration: 1,
          ease: "linear",
          repeat: Infinity,
        },
      );
    };

    const stop = async () => {
      scope.current.style.transform = "rotate(0deg)";
    };

    useImperativeHandle(ref, () => ({
      startAnimation: start,
      stopAnimation: stop,
    }));

    // For loaders, we might want it to start automatically if it has a certain class or prop,
    // but here we follow the pattern of other icons.

    return (
      <motion.svg
        ref={scope}
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        style={{ transformOrigin: "50% 50%" }}
      >
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </motion.svg>
    );
  },
);

Loader2Icon.displayName = "Loader2Icon";

export default Loader2Icon;
