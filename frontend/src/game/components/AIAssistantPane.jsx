import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import { Sparkles, Gem, Lock } from "lucide-react";
const Spinner = ({ className = "" }) => (
  <div
    className={`rounded-full border border-white/20 animate-spin border-t-white/60 ${className}`}
  />
);
const PulseCard = ({ className = "", children }) => (
  <div className={`animate-pulse bg-white/[0.03] rounded-xl ${className}`}>
    {children}
  </div>
);

const formatReviewMarkdown = (raw = "") => {
  if (!raw) return "";

  const normalized = raw
    .replace(/\r\n/g, "\n")
    // Convert "1) Findings" / "1. Findings" into markdown headings.
    .replace(/^\s*\d+[).]?\s+([A-Za-z][^\n:]*)\s*$/gm, "### $1")
    // Convert "Findings:" style section labels into headings.
    .replace(/^([A-Za-z][A-Za-z\s]{2,40}):\s*$/gm, "### $1")
    // Keep spacing between sections readable.
    .replace(/\n(### )/g, "\n\n$1")
    .replace(/\n{3,}/g, "\n\n");

  return normalized.trim();
};

const AIAssistantPane = ({
  onGetHint,
  onPurchase,
  onAnalyze,
  hint,
  review,
  isHintLoading,
  isReviewLoading,
  hintLevel,
  ai_hints_purchased,
  userXp,
  isCodePassed = false,
  streamingHint = "", // New prop for real-time text
}) => {
  const [hintHistory, setHintHistory] = React.useState([]);
  const scrollRef = React.useRef(null);
  const [activeIndex, setActiveIndex] = React.useState(0);

  const handleScroll = (e) => {
    const scrollLeft = e.target.scrollLeft;
    const width = e.target.offsetWidth;
    const index = Math.round(scrollLeft / width);
    setActiveIndex(index);
  };

  React.useEffect(() => {
    if (hint) {
      setHintHistory((prev) => {
        if (prev.includes(hint)) return prev;
        return [...prev, hint];
      });
      // Auto-scroll to latest hint
      setTimeout(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTo({
            left: scrollRef.current.scrollWidth,
            behavior: "smooth",
          });
        }
      }, 100);
    }
  }, [hint]);

  // Reset history if challenge id changes
  React.useEffect(() => {
    if (hintLevel === 1) {
      setHintHistory([]);
      setActiveIndex(0);
    }
  }, [hintLevel]);

  // Cost Logic
  const nextCost = 10 * (ai_hints_purchased + 1);
  const isMaxReached = ai_hints_purchased >= 3;
  const isLocked = ai_hints_purchased < hintLevel && !isMaxReached;
  const formattedReview = React.useMemo(
    () => formatReviewMarkdown(review),
    [review],
  );

  return (
    <section className="flex-1 min-h-0 flex flex-col bg-black overflow-hidden m-0">
      <header className="border-b border-white/5 px-4 py-2.5 flex items-center justify-between bg-black">
        <div className="flex items-center gap-2">
          <Sparkles size={12} className="text-neutral-600" />
          <h2 className="text-[10px] font-semibold text-neutral-600 uppercase tracking-widest font-sans">
            Assistant
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {userXp !== undefined && (
            <div className="flex items-center gap-1">
              <Gem size={10} className="text-neutral-700" />
              <span className="text-neutral-500 text-[10px] font-mono tabular-nums">
                {userXp}
              </span>
            </div>
          )}
        </div>
      </header>

      <div className="flex-1 min-h-0 relative bg-black overflow-y-auto">
        <div className="min-h-full flex flex-col">
          {review ? (
            <div className="mx-4 mt-4 mb-3 rounded-lg border border-[#2a2a2a] bg-[#161616] p-4 flex flex-col">
              <div className="text-[10px] font-semibold uppercase tracking-widest text-neutral-700 mb-2">
                AI Review
              </div>
              <div className="max-h-[50vh] min-h-[180px] overflow-y-auto pr-2">
                <div className="prose prose-invert prose-sm max-w-none prose-headings:text-neutral-100 prose-h3:text-[13px] prose-h3:font-semibold prose-h3:mb-2 prose-h3:mt-4 first:prose-h3:mt-0 prose-p:text-neutral-400 prose-p:text-[12px] prose-p:leading-relaxed prose-ul:text-neutral-400 prose-ol:text-neutral-400 prose-li:text-[12px] prose-strong:text-white prose-code:text-neutral-300 prose-code:bg-[#1c1c1c] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
                  <ReactMarkdown>{formattedReview}</ReactMarkdown>
                </div>
              </div>
            </div>
          ) : null}

          {/* Hint Carousel Wrapper */}
          <div className="flex-1 min-h-[340px] relative overflow-hidden flex flex-col">
            <div
              ref={scrollRef}
              onScroll={handleScroll}
              className="flex-1 min-h-[300px] flex overflow-x-auto snap-x snap-mandatory select-none scroll-smooth"
            >
              {hintHistory.length > 0 ? (
                hintHistory.map((h, i) => (
                  <div
                    key={i}
                    className="flex-none w-full h-full min-h-0 snap-start p-4 flex flex-col"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-4 h-4 rounded-sm bg-black flex items-center justify-center border border-white/5">
                        <span className="text-[9px] font-bold text-neutral-600">
                          {i + 1}
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold text-neutral-600 uppercase tracking-widest">
                        Hint {i + 1}
                      </span>
                    </div>

                    <div className="flex-1 min-h-0 bg-black border border-white/5 rounded-lg p-4 overflow-y-auto">
                      <div
                        className="prose prose-invert prose-sm max-w-none 
                              prose-p:text-neutral-500 prose-p:leading-relaxed prose-p:text-[12px]
                              prose-strong:text-white prose-strong:font-semibold
                              prose-pre:bg-[#0f0f0f] prose-pre:border prose-pre:border-[#222] prose-pre:rounded-md prose-pre:p-0
                              prose-code:text-neutral-300 prose-code:bg-[#1c1c1c] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-[11px] prose-code:before:content-none prose-code:after:content-none
                          "
                      >
                        <ReactMarkdown
                          components={{
                            pre: ({ children }) => (
                              <pre className="relative p-3 overflow-x-auto">
                                {children}
                              </pre>
                            ),
                            code: ({
                              inline,
                              className,
                              children,
                              ...props
                            }) => {
                              return !inline ? (
                                <code
                                  className={`${className} block text-[11px] leading-normal font-mono text-gray-400`}
                                  {...props}
                                >
                                  {children}
                                </code>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {h}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                ))
              ) : !isHintLoading && !review ? (
                <div className="w-full h-full flex flex-col items-center justify-center opacity-20 grayscale">
                  <Sparkles size={24} className="text-gray-500 mb-2" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    Awaiting Query
                  </p>
                </div>
              ) : null}

              {isHintLoading && (
                <div className="flex-none w-full h-full min-h-0 snap-start p-4 flex flex-col">
                  <div className="flex items-center gap-2 mb-3">
                    <Spinner className="w-2.5 h-2.5" />
                    <span className="text-[10px] font-bold text-[#00af9b] uppercase tracking-widest">
                      {streamingHint ? "Thinking..." : "Consulting AI..."}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-h-0 bg-black border border-[#00af9b]/20 rounded-lg p-4 overflow-y-auto">
                    {streamingHint ? (
                       <div className="prose prose-invert prose-sm max-w-none prose-p:text-neutral-300 prose-p:text-[12px] animate-in fade-in duration-500">
                         <ReactMarkdown>{streamingHint}</ReactMarkdown>
                         <span className="inline-block w-1.5 h-3.5 bg-[#00af9b] ml-1 animate-pulse" />
                       </div>
                    ) : (
                      <PulseCard className="h-full bg-white/[0.02] border border-white/5 relative">
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Sparkles size={20} className="text-[#00af9b]/10" />
                        </div>
                      </PulseCard>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Carousel Pagination Dots */}
            {(hintHistory.length > 1 ||
              (hintHistory.length > 0 && isHintLoading)) && (
              <div className="flex justify-center gap-1.5 pb-3">
                {[...Array(hintHistory.length + (isHintLoading ? 1 : 0))].map(
                  (_, i) => (
                    <div
                      key={i}
                      className={`w-1 h-1 transition-all duration-300 ${
                        i === activeIndex
                          ? "bg-[#00af9b] scale-125 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                          : "bg-white/10"
                      }`}
                    />
                  ),
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Action Bar - Fixed at absolute bottom of Card */}
      <div className="p-3 border-t border-white/5 bg-black space-y-2 shrink-0">
        {isMaxReached ? (
          <div className="w-full bg-purple-900/30 text-purple-400/60 border border-purple-500/20 text-[10px] font-semibold h-10 rounded-lg cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-wider">
            <Gem size={12} className="opacity-50" />
            Max Hints Reached
          </div>
        ) : isLocked ? (
          <div className="space-y-2">
            <button
              type="button"
              onClick={onPurchase}
              disabled={
                isHintLoading || (userXp !== undefined && userXp < nextCost)
              }
              className={`w-full text-[10px] font-semibold h-10 rounded-lg transition-all flex items-center justify-center gap-2 group relative overflow-hidden uppercase tracking-wider ${
                userXp !== undefined && userXp < nextCost
                  ? "bg-amber-900/20 border border-amber-500/20 text-amber-600/40 cursor-not-allowed"
                  : "bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-500/30"
              }`}
            >
              {isHintLoading ? (
                <Spinner className="w-3 h-3" />
              ) : (
                <Sparkles size={12} className="fill-current" />
              )}
              <span className="relative z-10">Get Hint</span>
              <span className="opacity-70 text-[9px] relative z-10 font-normal ml-1 flex items-center gap-0.5">
                (<Gem size={8} className="inline" />
                {nextCost})
              </span>
            </button>
            {userXp !== undefined && userXp < nextCost && (
              <div className="text-[9px] text-red-400/80 text-center font-bold uppercase tracking-tighter flex items-center justify-center gap-1">
                <span>Insufficient XP</span>
                <Gem size={10} className="text-red-400" />
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={onGetHint}
            disabled={isHintLoading}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white border border-purple-500/30 text-[10px] font-semibold h-10 rounded-lg transition-all flex items-center justify-center gap-2 uppercase tracking-wider"
          >
            {isHintLoading ? (
              <Spinner className="w-3 h-3" />
            ) : (
              <Sparkles size={12} />
            )}
            Unlock Intelligence
          </button>
        )}

        <button
          type="button"
          onClick={onAnalyze}
          disabled={isReviewLoading || !isCodePassed}
          className={`w-full text-[10px] font-semibold h-10 rounded-lg transition-all flex items-center justify-center gap-2 uppercase tracking-wider ${
            !isCodePassed
              ? "bg-slate-800/50 text-slate-500/60 border border-slate-600/20 cursor-not-allowed"
              : isReviewLoading
                ? "bg-blue-900/30 text-blue-400/60 border border-blue-500/20"
                : "bg-blue-600 hover:bg-blue-500 text-white border border-blue-500/30"
          }`}
        >
          {isReviewLoading ? (
            <Spinner className="w-3 h-3" />
          ) : !isCodePassed ? (
            <Lock size={12} className="opacity-60" />
          ) : (
            <Sparkles size={12} />
          )}
          {!isCodePassed
            ? "Locked - Pass Tests First"
            : review
              ? "Re-analyze Code"
              : "Analyze Code"}
        </button>
      </div>
    </section>
  );
};

export default memo(AIAssistantPane);
