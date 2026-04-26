import React from "react";
import { Search, X } from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";

/**
 * ChatSearch component
 * Handles the search input bar with debounced searching state.
 */
const ChatSearch = ({
  showSearch,
  searchQuery,
  setSearchQuery,
  searchMessages,
  clearSearch,
  isSearching,
  searchTimeoutRef,
}) => {
  return (
    <AnimatePresence>
      {showSearch && (
        <Motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="shrink-0 border-b border-[#1a1a1a] bg-[#0d0d0d] overflow-hidden"
        >
          <div className="px-4 py-3">
            <div className="relative group">
              <Search
                size={12}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500"
              />
              <input
                type="text"
                autoFocus
                placeholder="Search transmissions..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (searchTimeoutRef.current) {
                    clearTimeout(searchTimeoutRef.current);
                  }
                  searchTimeoutRef.current = setTimeout(() => {
                    searchMessages(e.target.value);
                  }, 300);
                }}
                className="w-full bg-white/[0.03] border-white/5 focus:border-emerald-500/30 rounded-xl pl-9 pr-10 py-2 text-[11px] text-white transition-all placeholder:text-neutral-600 outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery("");
                    clearSearch();
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white transition-colors"
                >
                  <X size={12} />
                </button>
              )}
            </div>
            
            {isSearching && (
              <div className="mt-2 flex items-center gap-2">
                {[0, 150, 300].map((delay) => (
                  <div
                    key={delay}
                    className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
                <span className="text-[9px] text-neutral-500 ml-1">
                  Searching...
                </span>
              </div>
            )}
          </div>
        </Motion.div>
      )}
    </AnimatePresence>
  );
};

export default ChatSearch;
