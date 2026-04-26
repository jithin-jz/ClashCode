import React, { useState, useEffect, useRef } from "react";
import { Smile } from "lucide-react";
import { motion as Motion, AnimatePresence } from "framer-motion";

const REACTION_EMOJIS = ["👍", "🔥", "😂", "❤️", "🎉", "💯"];

/**
 * ReactionBar component
 * Manages emoji picker and displays current reactions horizontally.
 */
const ReactionBar = ({ reactions, onReact, username, isOwn }) => {
  const [showPicker, setShowPicker] = useState(false);
  const pickerRef = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setShowPicker(false);
      }
    };
    if (showPicker) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showPicker]);

  const hasReactions = reactions && Object.keys(reactions).length > 0;

  return (
    <div className="flex items-center gap-1 min-w-max relative">
      {hasReactions &&
        Object.entries(reactions).map(([emoji, users]) => (
          <button
            key={emoji}
            onClick={() => onReact(emoji)}
            className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] border transition-all shadow-sm backdrop-blur-md ${
              users.includes(username)
                ? "bg-emerald-500/30 border-emerald-500/50 text-emerald-200 hover:bg-emerald-500/40"
                : "bg-black/60 border-white/10 text-neutral-400 hover:bg-white/10 hover:border-white/20"
            }`}
            title={users.join(", ")}
          >
            <span className="text-xs">{emoji}</span>
            <span className="font-mono font-bold">{users.length}</span>
          </button>
        ))}
      <div className="relative" ref={pickerRef}>
        <button
          onClick={() => setShowPicker(!showPicker)}
          className="w-5 h-5 rounded-full flex items-center justify-center text-neutral-500 hover:text-emerald-400 hover:bg-emerald-500/10 border border-transparent hover:border-emerald-500/30 transition-all"
          title="Add reaction"
        >
          <Smile size={12} />
        </button>
        <AnimatePresence>
          {showPicker && (
            <Motion.div
              initial={{ opacity: 0, scale: 0.8, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 10 }}
              className={`absolute bottom-7 ${isOwn ? "right-0" : "left-0"} z-50 flex gap-1 p-1.5 bg-[#0a0a0a]/95 border border-white/10 rounded-lg shadow-2xl backdrop-blur-xl min-w-max`}
            >
              {REACTION_EMOJIS.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => {
                    onReact(emoji);
                    setShowPicker(false);
                  }}
                  className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-white/10 hover:scale-110 transition-all text-sm"
                >
                  {emoji}
                </button>
              ))}
            </Motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ReactionBar;
