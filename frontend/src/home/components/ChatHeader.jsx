import React from "react";
import { Search, X } from "lucide-react";

/**
 * ChatHeader component
 * Displays the room title, online count, and action buttons (search, close).
 */
const ChatHeader = ({
  onlineCount,
  showSearch,
  setShowSearch,
  setSearchQuery,
  clearSearch,
  searchTimeoutRef,
  setOpen,
}) => {
  return (
    <header className="shrink-0 h-16 grid grid-cols-[1fr_auto_1fr] items-center px-5 border-b border-white/5 bg-black/40 backdrop-blur-xl relative z-10">
      {/* Left: Status */}
      <div className="flex items-center gap-1.5 leading-none">
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
        </span>
        <span className="text-[9px] font-black text-neutral-500 uppercase tracking-wider">
          {onlineCount || 0} online
        </span>
      </div>

      {/* Center: Title */}
      <div className="flex flex-col items-center justify-center">
        <span className="text-[11px] font-black tracking-[0.25em] text-neutral-100 uppercase font-mono drop-shadow-sm">
          Global Chat
        </span>
      </div>

      {/* Right Actions */}
      <div className="flex items-center justify-end gap-1">
        <button
          type="button"
          onClick={() => {
            setShowSearch(!showSearch);
            if (showSearch) {
              setSearchQuery("");
              clearSearch();
              if (searchTimeoutRef.current) {
                clearTimeout(searchTimeoutRef.current);
              }
            }
          }}
          className={`h-8 w-8 rounded-xl flex items-center justify-center transition-all duration-300 ${
            showSearch
              ? "bg-emerald-500/20 text-emerald-400"
              : "text-neutral-500 hover:text-white hover:bg-white/5"
          }`}
        >
          <Search size={16} />
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="h-8 w-8 rounded-xl flex items-center justify-center text-neutral-500 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-300"
        >
          <X size={16} />
        </button>
      </div>
    </header>
  );
};

export default ChatHeader;
