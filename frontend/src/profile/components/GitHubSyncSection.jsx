import { useState } from "react";
import { ExternalLink, RefreshCw, GitGraph, Check, ChevronRight } from "lucide-react";
import { useGitHubSync } from "../../hooks/useGitHubSync";

export default function GitHubSyncSection() {
  const {
    connection,
    connected,
    history,
    isLoading,
    error,
    initiateConnect,
    disconnect,
    toggle,
    updateRepoName,
    retryPush,
    fetchHistory,
  } = useGitHubSync();

  const [showHistory, setShowHistory] = useState(false);
  const [editingRepo, setEditingRepo] = useState(false);
  const [repoInput, setRepoInput] = useState("");
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 animate-pulse">
        <div className="h-3 w-20 bg-neutral-800 rounded mb-3" />
        <div className="h-3 w-32 bg-neutral-800 rounded" />
      </div>
    );
  }

  // ─── Not Connected ────────────────────────────────────────────────

  if (!connected) {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="flex items-center gap-3 mb-3">
          <GitHubIcon className="w-4 h-4 text-neutral-500" />
          <span className="text-[12px] font-medium text-neutral-400">GitHub Sync</span>
        </div>
        <p className="text-[11px] text-neutral-600 mb-4 leading-relaxed">
          Auto-push solutions to GitHub when you complete levels.
        </p>
        <button
          onClick={initiateConnect}
          className="w-full h-8 rounded-lg bg-neutral-900 border border-neutral-800 text-[11px] font-medium text-neutral-300 hover:text-white hover:border-neutral-700 transition-colors flex items-center justify-center gap-2"
        >
          <GitHubIcon className="w-3.5 h-3.5" />
          Connect
        </button>
        {error && <p className="mt-2 text-[10px] text-red-400/70">{error}</p>}
      </div>
    );
  }

  // ─── Connected ────────────────────────────────────────────────────

  const hasError = connection?.last_error?.length > 0;

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <GitHubIcon className="w-3.5 h-3.5 text-neutral-500" />
          <span className="text-[12px] font-medium text-neutral-300">
            @{connection.github_username}
          </span>
          <span className={`w-1.5 h-1.5 rounded-full ${connection.is_enabled ? "bg-emerald-400" : "bg-neutral-600"}`} />
        </div>
        <button
          onClick={toggle}
          className={`text-[10px] font-medium px-2 py-0.5 rounded transition-colors ${
            connection.is_enabled
              ? "text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20"
              : "text-neutral-500 bg-neutral-800 hover:bg-neutral-700"
          }`}
        >
          {connection.is_enabled ? "On" : "Off"}
        </button>
      </div>

      {/* Error */}
      {hasError && (
        <p className="text-[10px] text-red-400/80 mb-3 leading-relaxed">
          {connection.last_error}
        </p>
      )}

      {/* Stats */}
      <div className="flex items-center gap-3 text-[11px] text-neutral-600 mb-3">
        <span>{connection.total_pushes} pushes</span>
        <span>·</span>
        <span className="font-mono">{connection.repo_name}</span>
      </div>

      {/* Actions */}
      {editingRepo ? (
        <div className="flex gap-1.5 mb-3">
          <input
            type="text"
            value={repoInput}
            onChange={(e) => setRepoInput(e.target.value)}
            className="flex-1 px-2.5 py-1.5 rounded-md bg-black border border-neutral-800 text-[11px] text-white font-mono focus:outline-none focus:border-neutral-600"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") { updateRepoName(repoInput); setEditingRepo(false); }
              if (e.key === "Escape") setEditingRepo(false);
            }}
          />
          <button
            onClick={() => { updateRepoName(repoInput); setEditingRepo(false); }}
            className="px-2 py-1.5 rounded-md bg-neutral-800 text-neutral-300 text-[10px] hover:bg-neutral-700"
          >
            <Check size={11} />
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2 mb-3">
          <button
            onClick={() => { setRepoInput(connection.repo_name); setEditingRepo(true); }}
            className="text-[10px] text-neutral-600 hover:text-neutral-300 transition-colors"
          >
            Change repo
          </button>
          <span className="text-neutral-800">·</span>
          <a
            href={`https://github.com/${connection.github_username}/${connection.repo_name}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] text-neutral-600 hover:text-neutral-300 transition-colors flex items-center gap-1"
          >
            Open <ExternalLink size={9} />
          </a>
          <span className="text-neutral-800">·</span>
          <button
            onClick={() => { setShowHistory(!showHistory); if (!showHistory) fetchHistory(); }}
            className="text-[10px] text-neutral-600 hover:text-neutral-300 transition-colors flex items-center gap-1"
          >
            Logs <ChevronRight size={9} className={`transition-transform ${showHistory ? "rotate-90" : ""}`} />
          </button>
        </div>
      )}

      {/* History */}
      {showHistory && (
        <div className="space-y-1 mb-3 max-h-32 overflow-y-auto">
          {history.length === 0 && (
            <p className="text-[10px] text-neutral-700 py-2">No pushes yet</p>
          )}
          {history.slice(0, 8).map((log) => (
            <div key={log.id} className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2 min-w-0">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  log.status === "SUCCESS" ? "bg-emerald-400" :
                  log.status === "FAILED" ? "bg-red-400" :
                  "bg-neutral-600 animate-pulse"
                }`} />
                <span className="text-[10px] text-neutral-400 truncate">{log.challenge_title}</span>
              </div>
              {log.status === "FAILED" && (
                <button
                  onClick={() => retryPush(log.id)}
                  className="text-[9px] text-amber-400 hover:text-amber-300 shrink-0 ml-2"
                >
                  <RefreshCw size={9} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Disconnect */}
      <div className="border-t border-neutral-900 pt-3">
        {confirmDisconnect ? (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-neutral-600">Disconnect?</span>
            <button onClick={() => { disconnect(); setConfirmDisconnect(false); }} className="text-[10px] text-red-400 font-medium border border-red-500/20 px-2 py-0.5 rounded hover:bg-red-500/10 transition-colors">Yes</button>
            <button onClick={() => setConfirmDisconnect(false)} className="text-[10px] text-neutral-500 border border-neutral-800 px-2 py-0.5 rounded hover:border-neutral-700 transition-colors">Cancel</button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDisconnect(true)}
            className="text-[10px] text-red-400/70 border border-red-500/15 px-2.5 py-1 rounded-md hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/5 transition-colors"
          >
            Disconnect
          </button>
        )}
      </div>
    </div>
  );
}

function GitHubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  );
}
