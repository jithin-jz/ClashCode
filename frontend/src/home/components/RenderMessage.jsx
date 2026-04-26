import React from "react";
import { Link } from "react-router-dom";

/**
 * RenderMessage component
 * Processes text for @mentions and renders them as clickable profile links.
 */
const RenderMessage = ({ text }) => {
  if (!text) return null;
  const parts = text.split(/(@\w+)/g);
  return (
    <p className="break-words font-medium">
      {parts.map((part, i) =>
        part.startsWith("@") ? (
          <Link
            key={i}
            to={`/profile/${part.slice(1)}`}
            className="text-amber-400 hover:text-amber-300 font-bold transition-colors"
          >
            {part}
          </Link>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </p>
  );
};

export default RenderMessage;
