import React from "react";
import { Pin } from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";

/**
 * ChatPinnedBanner component
 * Displays the pinned message if one exists.
 */
const ChatPinnedBanner = ({
  pinnedMessage,
  isGlobal,
  user,
  unpinMessage,
}) => {
  return (
    <AnimatePresence>
      {isGlobal && pinnedMessage && (
        <Motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="shrink-0 border-b border-[#1a1a1a] bg-[#0d0d0d] overflow-hidden"
        >
          <div className="flex items-center gap-2 px-3 py-2">
            <Pin size={12} className="text-amber-400 shrink-0" />
            <p className="text-[11px] text-neutral-400 truncate flex-1">
              {pinnedMessage.message}
            </p>
            {user?.is_admin && (
              <button
                onClick={() => unpinMessage(pinnedMessage.timestamp)}
                className="text-[9px] text-neutral-600 hover:text-red-400 transition-colors shrink-0"
              >
                Unpin
              </button>
            )}
          </div>
        </Motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatPinnedBanner;
