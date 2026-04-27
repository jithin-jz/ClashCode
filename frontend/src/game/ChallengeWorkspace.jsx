import React, { useState, useEffect, useRef, useCallback } from "react";
import { BookOpen, Terminal, Bot, Play, Sparkles } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import useAuthStore from "../stores/useAuthStore";
import { useChallenge } from "./hooks/useChallenge";
import CursorEffects from "./CursorEffects";
import ChallengeWorkspaceSkeleton from "./ChallengeWorkspaceSkeleton";

// Subcomponents
import HeaderBar from "./components/HeaderBar";
import EditorPane from "./components/EditorPane";
import ProblemPane from "./components/ProblemPane";
import ConsolePane from "./components/ConsolePane";
import AIAssistantPane from "./components/AIAssistantPane";
import CompletionModal from "./components/CompletionModal";

// Utils
import { defineMonacoThemes, THEME_NAME_MAP, VALID_THEMES } from "../utils/monacoThemes";

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
    streamingHint,
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
    const activeTheme = user?.profile?.active_theme;

    if (activeTheme && VALID_THEMES.includes(activeTheme)) {
      const monacoThemeName = THEME_NAME_MAP[activeTheme] || activeTheme;
      monaco.editor.setTheme(monacoThemeName);
    } else {
      monaco.editor.setTheme("industrial");
    }

    const selectedFont = user?.profile?.active_font || "Fira Code";
    const fontFamily = `"${selectedFont}", 'Fira Code', 'JetBrains Mono', Consolas, monospace`;

    editor.updateOptions({ fontFamily });
    monaco.editor.remeasureFonts();
    editor.layout();
  }, [user?.profile?.active_theme, user?.profile?.active_font]);

  const handleEditorDidMount = useCallback(
    (editor, monaco) => {
      editorRef.current = editor;
      monacoRef.current = monaco;

      defineMonacoThemes(monaco);

      editor.onDidChangeCursorPosition((e) => {
        if (user?.profile?.active_effect && window.spawnCursorEffect) {
          const scrolledVisiblePosition = editor.getScrolledVisiblePosition(e.position);
          if (scrolledVisiblePosition) {
            const domNode = editor.getDomNode();
            const rect = domNode.getBoundingClientRect();
            window.spawnCursorEffect(
              rect.left + scrolledVisiblePosition.left,
              rect.top + scrolledVisiblePosition.top + 10,
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
      <CompletionModal
        data={completionData}
        activeVictory={user?.profile?.active_victory}
        onNext={() => {
          setCompletionData(null);
          navigate(`/level/${completionData.next_level_slug}`);
        }}
        onDashboard={() => navigate("/home")}
      />

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
        <div
          className={`lg:flex flex-1 lg:flex-none w-full lg:w-[24rem] min-h-0 flex-col bg-black border-y sm:border border-white/5 sm:rounded-xl shadow-2xl overflow-y-auto ${mobileTab === "problem" ? "flex" : "hidden"}`}
        >
          <ProblemPane challenge={challenge} loading={!challenge} />
        </div>

        {/* Center: Editor & Console */}
        <div
          className={`lg:flex flex-1 flex-col min-w-0 sm:rounded-xl sm:border border-white/5 shadow-2xl overflow-hidden bg-black ${mobileTab === "code" ? "flex" : "hidden"}`}
        >
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

            {/* Editor Action Bar */}
            <div className="shrink-0 h-11 bg-[#0a0a0a] border-t border-white/5 flex items-center justify-between px-4">
              <div className="flex items-center gap-1.5 opacity-50">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">
                  Sandbox Active
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={runCode}
                  disabled={isRunning || isSubmitting || !challenge}
                  className={`h-7 px-4 rounded border border-white/10 transition-all flex items-center gap-2 ${isRunning || isSubmitting || !challenge ? "opacity-50 text-zinc-600 cursor-not-allowed" : "bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white active:scale-95"}`}
                >
                  {isRunning ? (
                    <div className="w-2.5 h-2.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Play size={10} fill="currentColor" />
                  )}
                  <span className="text-[10px] font-bold uppercase tracking-widest">Run</span>
                </button>
                <button
                  onClick={submitCode}
                  disabled={isRunning || isSubmitting || !challenge}
                  className={`h-7 px-5 rounded relative transition-all flex items-center gap-2 ${isRunning || isSubmitting || !challenge ? "bg-zinc-800 text-zinc-500 cursor-not-allowed" : lastRunPassed ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]" : "bg-white text-black hover:bg-zinc-200"} active:scale-95`}
                >
                  {isSubmitting ? (
                    <div className="w-2.5 h-2.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  ) : (
                    <Sparkles size={10} fill="currentColor" />
                  )}
                  <span className="text-[10px] font-bold uppercase tracking-widest">Submit</span>
                </button>
              </div>
            </div>

            {/* Terminal/Console */}
            <div className="h-48 border-t border-white/5 flex flex-col bg-black">
              <div className="shrink-0 px-3 py-2 border-b border-white/5 flex items-center justify-between h-8 bg-black">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">
                    Terminal
                  </span>
                  {output.length > 0 && (
                    <button
                      onClick={() => setOutput([])}
                      className="p-1 hover:bg-white/5 rounded text-zinc-600 hover:text-zinc-400 transition-colors"
                      title="Clear Console"
                    >
                      <Terminal size={10} />
                    </button>
                  )}
                </div>
                {output.some((l) => l.type === "error") && (
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
        <div
          className={`lg:flex flex-1 lg:flex-none w-full lg:w-[22rem] flex-col bg-black border-y sm:border border-white/5 sm:rounded-xl shadow-2xl overflow-hidden ${mobileTab === "ai" ? "flex" : "hidden"}`}
        >
          <AIAssistantPane
            onGetHint={handleGetHint}
            onPurchase={handlePurchaseAIAssist}
            onAnalyze={handleAnalyzeCode}
            hint={hint}
            streamingHint={streamingHint}
            review={review}
            isHintLoading={isHintLoading}
            isReviewLoading={isReviewLoading}
            hintLevel={hintLevel}
            ai_hints_purchased={challenge?.ai_hints_purchased || 0}
            userXp={user?.profile?.xp || 0}
            isCodePassed={lastRunPassed}
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
