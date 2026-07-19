import { forwardRef, useImperativeHandle, useCallback } from "react";
import type { AnimatedIconHandle, AnimatedIconProps } from "./types";
import { motion, useAnimate } from "framer-motion";

const TravelBag = forwardRef<AnimatedIconHandle, AnimatedIconProps>(
  (
    { size = 24, color = "currentColor", strokeWidth = 2, className = "" },
    ref,
  ) => {
    const [scope, animate] = useAnimate();

    const start = useCallback(async () => {
      animate(
        ".front-flap",
        { skewX: 20 },
        { duration: 0.4, ease: [0.4, 0, 0.2, 1] },
      );
      animate(
        ".elements",
        { x: -1, scale: 0.9, skewX: 20 },
        { duration: 0.3, ease: "easeInOut" },
      );
      animate(".back-flap", { x: 4 }, { duration: 0.3, ease: "easeInOut" });
    }, [animate]);

    const stop = useCallback(() => {
      animate(".front-flap", { skewX: 0 }, { duration: 0.3, ease: "easeIn" });
      animate(
        ".elements",
        { x: 0, scale: 1, skewX: 0 },
        { duration: 0.3, ease: "easeOut" },
      );
      animate(".back-flap", { x: 0 }, { duration: 0.3, ease: "easeOut" });
    }, [animate]);

    useImperativeHandle(
      ref,
      () => ({
        startAnimation: start,
        stopAnimation: stop,
      }),
      [start, stop],
    );

    return (
      <motion.svg
        ref={scope}
        onHoverStart={start}
        onHoverEnd={stop}
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`cursor-pointer ${className}`}
      >
        <motion.path
          className="front-flap"
          d="M12.75 4.25h-6m6 0c2.828 0 4.243 0 5.121.879.879.878.879 2.293.879 5.121v2.5c0 2.828 0 4.243-.879 5.121-.878.879-2.293.879-5.121.879h-6c-2.828 0-4.243 0-5.121-.879C.75 16.993.75 15.578.75 12.75v-2.5c0-2.828 0-4.243.879-5.121.878-.879 2.293-.879 5.121-.879"
        ></motion.path>
        <motion.path
          className="elements"
          d="M18.75 8.25a4 4 0 0 1-4-4"
        ></motion.path>
        <motion.path
          className="elements"
          d="m7 9.75-.75.75.75.75.75-.75z"
        ></motion.path>
        <motion.path
          className="elements"
          d="M.75 14.75a4 4 0 0 1 4 4m-4-10.5a4 4 0 0 0 4-4m14 10.5a4 4 0 0 0-4 4"
        ></motion.path>
        <motion.path
          className="elements"
          d="m11.75 14.55-1.5-.3 1.2-1.2z"
        ></motion.path>
        <motion.path className="elements" d="M12.25 8.75v.01"></motion.path>
        <motion.path
          className="back-flap"
          d="M12.75 4.25h-6v-.5c0-1.414 0-2.121.44-2.56C7.628.75 8.335.75 9.75.75s2.121 0 2.56.44c.44.438.44 1.145.44 2.56zm0 0c2.828 0 4.243 0 5.121.879.879.878.879 2.293.879 5.121v2.5c0 2.828 0 4.243-.879 5.121-.878.879-2.293.879-5.121.879"
        ></motion.path>
      </motion.svg>
    );
  },
);

TravelBag.displayName = "TravelBag";
export default TravelBag;

