import React from "react";
import { ArrowLeft, Play } from "lucide-react";

const HeaderBar = ({ title, navigate, isRunning, isSubmitting, stopCode }) => {
  return (
    <div className="h-12 bg-[#0a0a0a] border-b border-[#1e1e1e] flex items-center justify-between px-3 sm:px-4 shrink-0 z-20 relative font-sans">
      {/* Left: Navigation & Title */}
      <div className="flex items-center gap-2 sm:gap-3 relative z-10 min-w-0">
        <button
          type="button"
          onClick={() => navigate("/home")}
          className="h-7 w-7 rounded-md border border-[#242424] bg-[#161616] text-neutral-600 hover:text-neutral-200 hover:bg-[#1c1c1c] transition-colors flex items-center justify-center shrink-0"
        >
          <ArrowLeft size={13} />
        </button>
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex flex-col min-w-0">
            <h1 className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.2em] flex items-center gap-2 min-w-0">
              <span className="w-1 h-1 rounded-full bg-neutral-700 shrink-0" />
              <span className="truncate">{title}</span>
            </h1>
          </div>
        </div>
      </div>

      {/* Right: Actions & Status */}
      <div className="flex items-center gap-3 relative z-10 shrink-0">
        <div className="flex items-center gap-2">
          {(isRunning || isSubmitting) && (
            <button
              type="button"
              onClick={stopCode}
              className="h-8 px-3 bg-red-500/10 hover:bg-red-500/15 text-red-400 border border-red-500/20 text-[10px] font-bold uppercase tracking-wider rounded-md transition-all flex items-center gap-1.5"
            >
              <span className="w-1 h-1 rounded-full bg-red-400 animate-pulse" />
              <span>Terminate</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(HeaderBar);
