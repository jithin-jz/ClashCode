import React, { useState, useEffect, useRef, useCallback } from "react";
import { BookOpen, Terminal, Bot, Sparkles, Gem, Play } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import useAuthStore from "../stores/useAuthStore";
import { useChallenge } from "./hooks/useChallenge";
import { motion as Motion } from "framer-motion";
import CursorEffects from "./CursorEffects";
import VictoryAnimation from "./VictoryAnimation";
import ChallengeWorkspaceSkeleton from "./ChallengeWorkspaceSkeleton";

// Subcomponents
import HeaderBar from "./components/HeaderBar";
import EditorPane from "./components/EditorPane";
import ProblemPane from "./components/ProblemPane";
import ConsolePane from "./components/ConsolePane";
import AIAssistantPane from "./components/AIAssistantPane";

const MOBILE_TABS = [
  { id: "problem", label: "Problem", Icon: BookOpen },
  { id: "code", label: "Code", Icon: Terminal },
  { id: "ai", label: "AI", Icon: Bot },
];

const ChallengeWorkspace = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  
  const {
    challenge,
    isLoadingChallenge,
    code,
    setCode,
    output,
    setOutput,
    isRunning,
    isSubmitting,
    lastRunPassed,
    mobileTab,
    setMobileTab,
    completionData,
    setCompletionData,
    hint,
    hintLevel,
    review,
    runCode,
    submitCode,
    handleGetHint,
    handlePurchaseAIAssist,
    handleAnalyzeCode,
    stopCode,
    isHintLoading,
    isReviewLoading,
  } = useChallenge(id);

  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const applyEditorPreferences = useCallback(() => {
    if (!editorRef.current || !monacoRef.current) return;

    const editor = editorRef.current;
    const monaco = monacoRef.current;

    const themeNameMap = {
      solarized_dark: "solarized-dark",
    };

    const activeTheme = user?.profile?.active_theme;
    const validThemes = [
      "dracula",
      "nord",
      "monokai",
      "solarized_dark",
      "solarized-dark",
      "cyberpunk",
    ];

    if (activeTheme && validThemes.includes(activeTheme)) {
      const monacoThemeName = themeNameMap[activeTheme] || activeTheme;
      monaco.editor.setTheme(monacoThemeName);
    } else {
      monaco.editor.setTheme("industrial");
    }

    const selectedFont = user?.profile?.active_font || "Fira Code";
    const fontFamily = selectedFont
      ? `"${selectedFont}", 'Fira Code', 'JetBrains Mono', Consolas, monospace`
      : "'Fira Code', 'JetBrains Mono', Consolas, monospace";

    editor.updateOptions({ fontFamily });
    monaco.editor.remeasureFonts();
    editor.layout();
  }, [user?.profile?.active_theme, user?.profile?.active_font]);

  const handleEditorDidMount = useCallback(
    (editor, monaco) => {
      editorRef.current = editor;
      monacoRef.current = monaco;

      const themes = {
        industrial: {
          base: "vs-dark",
          inherit: true,
          rules: [
            { token: "comment", foreground: "444444" },
            { token: "keyword", foreground: "ffffff", fontStyle: "bold" },
            { token: "string", foreground: "a3a3a3" },
          ],
          colors: { "editor.background": "#000000", "editor.foreground": "#e8e8e8" },
        },
        dracula: { base: "vs-dark", inherit: true, rules: [], colors: { "editor.background": "#282a36" } },
        nord: { base: "vs-dark", inherit: true, rules: [], colors: { "editor.background": "#2e3440" } },
        monokai: { base: "vs-dark", inherit: true, rules: [], colors: { "editor.background": "#272822" } },
        "solarized-dark": { base: "vs-dark", inherit: true, rules: [], colors: { "editor.background": "#002b36" } },
        cyberpunk: { base: "vs-dark", inherit: true, rules: [], colors: { "editor.background": "#0d0d0d" } },
      };

      Object.entries(themes).forEach(([name, config]) => {
        monaco.editor.defineTheme(name, config);
      });

      editor.onDidChangeCursorPosition((e) => {
        if (user?.profile?.active_effect && window.spawnCursorEffect) {
          const scrolledVisiblePosition = editor.getScrolledVisiblePosition(e.position);
          if (scrolledVisiblePosition) {
            const domNode = editor.getDomNode();
            const rect = domNode.getBoundingClientRect();
            window.spawnCursorEffect(
              rect.left + scrolledVisiblePosition.left, 
              rect.top + scrolledVisiblePosition.top + 10
            );
          }
        }
      });

      applyEditorPreferences();
    },
    [user?.profile?.active_effect, applyEditorPreferences],
  );

  useEffect(() => {
    applyEditorPreferences();
  }, [applyEditorPreferences]);

  if (isLoadingChallenge) {
    return <ChallengeWorkspaceSkeleton />;
  }

  return (
    <div className="h-dvh flex flex-col bg-[#0a0a0a] text-white overflow-hidden relative font-sans selection:bg-white/10">
      <div className="absolute inset-0 pointer-events-none bg-[#0a0a0a]" />
      <CursorEffects effectType={user?.profile?.active_effect} />

      {/* Completion Modal */}
      {completionData && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4">
          <VictoryAnimation type={user?.profile?.active_victory} />
          <Motion.div
            initial={{ scale: 0.98, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#111]/95 backdrop-blur-md border border-[#222] rounded-2xl p-6 sm:p-10 max-w-sm w-full flex flex-col items-center text-center shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            <div className="relative z-10 flex flex-col items-center gap-6">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-2 bg-green-500/10 border border-green-500/20">
                <Sparkles size={32} className="text-green-500" />
              </div>

              <div className="space-y-1">
                <h2 className="text-xl font-bold text-white uppercase tracking-wider">Challenge Complete</h2>
                <p className="text-gray-500 text-xs text-balance">Validation successful. You've beaten the challenge.</p>
              </div>

              <div className="flex gap-2 my-1">
                {[1, 2, 3].map((star) => (
                  <div key={star} className={`w-6 h-6 flex items-center justify-center ${star <= completionData.stars ? "text-[#ffa116]" : "text-gray-800"}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-5.82 3.25L7.38 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </div>
                ))}
              </div>

              {completionData.xp_earned > 0 && (
                <div className="text-white text-sm font-mono tracking-tighter flex items-center gap-1.5">
                  <Gem size={14} className="text-red-500 fill-red-500/10" />+{completionData.xp_earned} EARNED
                </div>
              )}

              <div className="flex flex-col w-full gap-2 mt-4">
                {completionData.next_level_slug && (
                  <button
                    onClick={() => { setCompletionData(null); navigate(`/level/${completionData.next_level_slug}`); }}
                    className="w-full h-10 rounded-xl bg-[#ffa116] text-black hover:bg-[#ff8f00] font-bold uppercase text-xs transition-colors"
                  >
                    Next Challenge
                  </button>
                )}
                <button
                  onClick={() => navigate("/home")}
                  className="w-full h-10 rounded-xl border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:bg-white/10 font-bold uppercase text-xs transition-colors"
                >
                  Dashboard
                </button>
              </div>
            </div>
          </Motion.div>
        </div>
      )}

      <div className="shrink-0 relative z-10">
        <HeaderBar
          title={challenge?.title || "Loading..."}
          navigate={navigate}
          isRunning={isRunning}
          isSubmitting={isSubmitting}
          stopCode={stopCode}
        />
      </div>

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative z-10 p-0 sm:p-3 gap-0 sm:gap-3">
        {/* Left: Problem */}
        <div className={`lg:flex flex-1 lg:flex-none w-full lg:w-[24rem] min-h-0 flex-col bg-black border-y sm:border border-white/5 sm:rounded-xl shadow-2xl overflow-y-auto ${mobileTab === "problem" ? "flex" : "hidden"}`}>
          <ProblemPane challenge={challenge} loading={!challenge} />
        </div>

        {/* Center: Editor & Console */}
        <div className={`lg:flex flex-1 flex-col min-w-0 sm:rounded-xl sm:border border-white/5 shadow-2xl overflow-hidden bg-black ${mobileTab === "code" ? "flex" : "hidden"}`}>
          <div className="flex-1 flex flex-col relative group overflow-hidden bg-black">
            <div className="flex-1 relative">
              <EditorPane
                code={code}
                setCode={setCode}
                handleEditorDidMount={handleEditorDidMount}
                loading={!challenge}
                editorFontFamily={user?.profile?.active_font}
              />
            </div>
            
            <div className="shrink-0 h-11 bg-[#0a0a0a] border-t border-white/5 flex items-center justify-between px-4">
              <div className="flex items-center gap-1.5 opacity-50">
                 <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Sandbox Active</span>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={runCode}
                  disabled={isRunning || isSubmitting || !challenge}
                  className={`h-7 px-4 rounded border border-white/10 transition-all flex items-center gap-2 ${isRunning || isSubmitting || !challenge ? "opacity-50 text-zinc-600 cursor-not-allowed" : "bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white active:scale-95"}`}
                >
                  {isRunning ? <div className="w-2.5 h-2.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Play size={10} fill="currentColor" />}
                  <span className="text-[10px] font-bold uppercase tracking-widest">Run</span>
                </button>
                <button
                  onClick={submitCode}
                  disabled={isRunning || isSubmitting || !challenge}
                  className={`h-7 px-5 rounded relative transition-all flex items-center gap-2 ${isRunning || isSubmitting || !challenge ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" : lastRunPassed ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]" : "bg-white text-black hover:bg-zinc-200"} active:scale-95`}
                >
                  {isSubmitting ? <div className="w-2.5 h-2.5 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <Sparkles size={10} fill="currentColor" />}
                  <span className="text-[10px] font-bold uppercase tracking-widest">Submit</span>
                </button>
              </div>
            </div>

            <div className="h-48 border-t border-white/5 flex flex-col bg-black">
              <div className="shrink-0 px-3 py-2 border-b border-white/5 flex items-center justify-between h-8 bg-black">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">Terminal</span>
                  {output.length > 0 && (
                    <button onClick={() => setOutput([])} className="p-1 hover:bg-white/5 rounded text-zinc-600 hover:text-zinc-400 transition-colors" title="Clear Console"><Terminal size={10} /></button>
                  )}
                </div>
                {output.some(l => l.type === "error") && (
                  <span className="text-[10px] font-bold text-red-400 uppercase tracking-tighter flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-red-400" /> Error
                  </span>
                )}
              </div>
              <div className="flex-1 overflow-hidden">
                <ConsolePane output={output} loading={!challenge} />
              </div>
            </div>
          </div>
        </div>

        {/* Right: AI Assistant */}
        <div className={`lg:flex flex-1 lg:flex-none w-full lg:w-[22rem] flex-col bg-black border-y sm:border border-white/5 sm:rounded-xl shadow-2xl overflow-hidden ${mobileTab === "ai" ? "flex" : "hidden"}`}>
          <AIAssistantPane
            onGetHint={handleGetHint}
            onPurchase={handlePurchaseAIAssist}
            onAnalyze={handleAnalyzeCode}
            hint={hint}
            review={review}
            isHintLoading={isHintLoading}
            isReviewLoading={isReviewLoading}
            hintLevel={hintLevel}
            ai_hints_purchased={challenge?.ai_hints_purchased || 0}
            userXp={user?.profile?.xp || 0}
          />
        </div>
      </div>

      {/* Mobile Tab Bar */}
      <div className="lg:hidden h-14 bg-black border-t border-white/5 flex items-center justify-around relative z-20">
        {MOBILE_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setMobileTab(tab.id)}
            className={`flex-1 flex flex-col items-center justify-center gap-1 transition-colors ${mobileTab === tab.id ? "text-white bg-white/5" : "text-neutral-600"}`}
          >
            <tab.Icon size={16} />
            <span className="text-[9px] font-bold uppercase tracking-[0.15em]">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ChallengeWorkspace;
