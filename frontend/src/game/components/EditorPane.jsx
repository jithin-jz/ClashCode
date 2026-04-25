import React, { memo } from "react";
import Editor from "@monaco-editor/react";
import useWorkspaceStore from "../../stores/useWorkspaceStore";

const EditorPane = ({
  code,
  setCode,
  handleEditorDidMount,
  loading,
  editorFontFamily,
}) => {
  const fontSize = useWorkspaceStore((state) => state.fontSize);

  if (loading) {
    return (
      <div className="flex-1 border-r border-white/10 flex flex-col p-4 animate-pulse bg-black">
        <div className="w-48 h-6 bg-white/5 rounded-md mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
            <div
              key={i}
              className="h-4 bg-white/5 rounded-md"
              style={{ width: `${((i * 7 + 30) % 60) + 30}%` }}
            ></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-black relative group h-full overflow-hidden">
      <div className="flex-1 bg-black">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value)}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: fontSize || 14,
            lineHeight: (fontSize || 14) * 1.6,
            padding: { top: 16, bottom: 16 },
            scrollBeyondLastLine: false,
            fontLigatures: true,
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: true,
            renderLineHighlight: "all",
            lineNumbersMinChars: 3,
            glyphMargin: false,
            folding: true,
            fontFamily:
              editorFontFamily ||
              "'Fira Code', 'JetBrains Mono', Consolas, monospace",
            scrollbar: {
              vertical: "visible",
              horizontal: "visible",
              useShadows: false,
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
            },
            fixedOverflowWidgets: true,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
};

export default memo(EditorPane);
