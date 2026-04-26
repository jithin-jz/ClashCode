import React from "react";

/**
 * NavButton component
 * A reusable, styled icon button used in both Top and Bottom navigation.
 */
const NavButton = ({
  onClick,
  title,
  children,
  className = "",
  badge = null,
  active = false,
}) => (
  <button
    type="button"
    onClick={onClick}
    title={title}
    aria-label={title}
    className={`
      group relative inline-flex h-8 w-8 shrink-0 items-center justify-center
      rounded-md border transition-all duration-150
      ${
        active
          ? "border-white/30 bg-white/10 text-white"
          : "border-white/10 bg-white/5 text-white/70 hover:border-white/30 hover:bg-white/10 hover:text-white"
      }
      ${className}
    `}
  >
    <span className="inline-flex items-center justify-center">{children}</span>
    {badge}
  </button>
);

export default NavButton;
