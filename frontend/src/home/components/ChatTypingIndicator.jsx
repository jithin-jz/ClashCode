import React from "react";
import { AnimatePresence, motion as Motion } from "framer-motion";

/**
 * ChatTypingIndicator component
 * Shows a message when other users are typing.
 */
const ChatTypingIndicator = ({ otherTyping }) => {
  return (
    <AnimatePresence>
      {otherTyping.length > 0 && (
        <Motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="shrink-0 px-4 py-1 bg-[#050505]"
        >
          <span className="text-[10px] text-neutral-500 italic">
            {otherTyping.length === 1
              ? `${otherTyping[0].username} is typing...`
              : otherTyping.length === 2
                ? `${otherTyping[0].username} and ${otherTyping[1].username} are typing...`
                : `${otherTyping[0].username} and ${otherTyping.length - 1} others are typing...`}
          </span>
        </Motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatTypingIndicator;
