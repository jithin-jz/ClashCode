import { useState } from "react";
import { ExternalLink, RefreshCw, GitGraph, Check, ChevronRight } from "lucide-react";
import { useGitHubSync } from "../../hooks/useGitHubSync";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";

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

  // ─── Loading ──────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <Card className="bg-[#0d0d0d] border-[#1a1a1a] overflow-hidden">
        <div className="p-5 animate-pulse space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/[0.03]" />
            <div className="space-y-1.5">
              <div className="h-3 w-24 bg-white/[0.03] rounded" />
              <div className="h-2.5 w-36 bg-white/[0.03] rounded" />
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // ─── Not Connected ────────────────────────────────────────────────

  if (!connected) {
    return (
      <Card className="bg-[#0d0d0d] border-[#1a1a1a] overflow-hidden group hover:border-[#333] transition-all duration-300">
        {/* Hero Area */}
        <div className="h-28 flex items-center justify-center bg-black border-b border-[#1a1a1a] relative overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-[0.02]">
            <div className="absolute inset-0" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }} />
          </div>

          <div className="text-neutral-700 group-hover:text-white/20 transition-colors duration-500">
            <GitHubIcon className="w-12 h-12" />
          </div>

          {/* Status Badge */}
          <div className="absolute top-3 left-3">
            <Badge className="bg-black/60 text-neutral-600 border-[#222] text-[7px] px-1.5 py-0.5 rounded-sm border font-bold uppercase tracking-[0.2em] font-mono backdrop-blur-sm">
              Integration
            </Badge>
          </div>
        </div>

        <CardHeader className="p-4 pb-2 space-y-0.5">
          <CardTitle className="text-[11px] uppercase tracking-wider font-bold font-mono text-neutral-300">
            GitHub Auto-Sync
          </CardTitle>
          <p className="text-[9px] text-neutral-600 font-medium leading-relaxed">
            Push solutions to a repo automatically when you complete levels
          </p>
        </CardHeader>

        <CardContent className="p-4 pt-3">
          {/* Value Props */}
          <div className="flex items-center gap-3 mb-4">
            {["Portfolio", "Track Progress", "Share"].map((label) => (
              <span
                key={label}
                className="text-[8px] font-bold uppercase tracking-wider text-neutral-600 bg-white/[0.02] border border-white/5 px-2 py-1 rounded"
              >
                {label}
              </span>
            ))}
          </div>

          <button
            onClick={initiateConnect}
            className="w-full flex items-center justify-center gap-2.5 h-10 rounded-xl bg-[#161b22] border border-[#30363d] hover:border-[#8b949e]/50 hover:bg-[#1c2128] text-[11px] font-semibold text-[#c9d1d9] transition-all duration-200 active:scale-[0.97]"
          >
            <GitHubIcon className="w-4 h-4 text-white" />
            Connect with GitHub
          </button>

          {error && (
            <p className="mt-2.5 text-[9px] text-red-400/70 text-center">{error}</p>
          )}
        </CardContent>
      </Card>
    );
  }

  // ─── Connected ────────────────────────────────────────────────────

  const hasError = connection?.last_error?.length > 0;
  const isActive = connection.is_enabled && !hasError;

  return (
    <Card className="bg-[#0d0d0d] border-[#1a1a1a] overflow-hidden hover:border-[#333] transition-all duration-300">
      {/* Subtle top accent */}
      <div className={`h-[2px] w-full ${isActive ? "bg-gradient-to-r from-emerald-500/0 via-emerald-500/40 to-emerald-500/0" : hasError ? "bg-gradient-to-r from-red-500/0 via-red-500/30 to-red-500/0" : "bg-gradient-to-r from-white/0 via-white/5 to-white/0"}`} />

      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl border flex items-center justify-center transition-colors ${isActive ? "bg-emerald-500/5 border-emerald-500/15" : "bg-white/[0.02] border-white/5"}`}>
              <GitHubIcon className="w-[18px] h-[18px]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-[11px] font-bold text-white uppercase tracking-wide font-mono">
                  GitHub Sync
                </h4>
                <span className={`w-1.5 h-1.5 rounded-full ${isActive ? "bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.5)]" : hasError ? "bg-red-400" : "bg-neutral-600"}`} />
              </div>
              <p className="text-[10px] text-neutral-500 font-mono mt-0.5">
                @{connection.github_username}
              </p>
            </div>
          </div>

          {/* Toggle */}
          <button
            onClick={toggle}
            className="group/toggle relative"
            aria-label={connection.is_enabled ? "Disable sync" : "Enable sync"}
          >
            <span className={`block w-8 h-[18px] rounded-full transition-colors duration-200 ${connection.is_enabled ? "bg-emerald-500/20" : "bg-white/5"}`} />
            <span className={`absolute top-[3px] w-3 h-3 rounded-full transition-all duration-200 ${connection.is_enabled ? "left-[14px] bg-emerald-400" : "left-[3px] bg-neutral-600"}`} />
          </button>
        </div>

        {/* Error Banner */}
        {hasError && (
          <div className="bg-red-500/5 border border-red-500/10 rounded-xl px-3.5 py-2.5 space-y-1.5">
            <div className="flex items-start gap-2">
              <span className="w-1 h-1 rounded-full bg-red-400 mt-1.5 shrink-0" />
              <p className="text-[10px] text-red-300/80 leading-relaxed">
                {connection.last_error}
              </p>
            </div>
            {connection.last_error.includes("reconnect") && (
              <button
                onClick={initiateConnect}
                className="text-[9px] font-bold text-red-400 hover:text-red-300 uppercase tracking-wider transition-colors ml-3"
              >
                Reconnect Account →
              </button>
            )}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-white/[0.02] border border-white/5 rounded-lg px-3 py-2 text-center">
            <div className="text-sm font-bold text-white font-mono">{connection.total_pushes}</div>
            <div className="text-[8px] text-neutral-600 uppercase tracking-wider font-bold mt-0.5">Pushes</div>
          </div>
          <div className="bg-white/[0.02] border border-white/5 rounded-lg px-3 py-2 text-center">
            <div className="text-[10px] font-bold text-white font-mono truncate">{connection.repo_name}</div>
            <div className="text-[8px] text-neutral-600 uppercase tracking-wider font-bold mt-0.5">Repo</div>
          </div>
          <div className="bg-white/[0.02] border border-white/5 rounded-lg px-3 py-2 text-center">
            <div className="text-[10px] font-bold text-white capitalize">{connection.is_enabled ? "Active" : "Paused"}</div>
            <div className="text-[8px] text-neutral-600 uppercase tracking-wider font-bold mt-0.5">Status</div>
          </div>
        </div>

        {/* Actions Row */}
        <div className="flex items-center gap-2">
          {editingRepo ? (
            <div className="flex gap-1.5 flex-1">
              <input
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="repo-name"
                className="flex-1 px-3 py-1.5 rounded-lg bg-black border border-white/10 text-white text-[10px] font-mono focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/10 transition-all"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") { updateRepoName(repoInput); setEditingRepo(false); }
                  if (e.key === "Escape") setEditingRepo(false);
                }}
              />
              <button
                onClick={() => { updateRepoName(repoInput); setEditingRepo(false); }}
                className="px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold uppercase tracking-wider hover:bg-emerald-500/20 transition-colors"
              >
                <Check size={12} />
              </button>
            </div>
          ) : (
            <>
              <button
                onClick={() => { setRepoInput(connection.repo_name); setEditingRepo(true); }}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/5 text-[9px] text-neutral-500 hover:text-white hover:border-white/15 font-bold uppercase tracking-wider transition-all"
              >
                <GitGraph size={10} />
                Repo
              </button>
              <a
                href={`https://github.com/${connection.github_username}/${connection.repo_name}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/5 text-[9px] text-neutral-500 hover:text-white hover:border-white/15 font-bold uppercase tracking-wider transition-all"
              >
                <ExternalLink size={10} />
                Open
              </a>
              <button
                onClick={() => { setShowHistory(!showHistory); if (!showHistory) fetchHistory(); }}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/5 text-[9px] text-neutral-500 hover:text-white hover:border-white/15 font-bold uppercase tracking-wider transition-all ml-auto"
              >
                <ChevronRight size={10} className={`transition-transform ${showHistory ? "rotate-90" : ""}`} />
                Logs
              </button>
            </>
          )}
        </div>

        {/* Push History */}
        {showHistory && (
          <div className="space-y-1 max-h-44 overflow-y-auto rounded-xl border border-white/5 bg-black/30 p-2">
            {history.length === 0 && (
              <div className="flex flex-col items-center justify-center py-6 gap-2">
                <GitGraph size={20} className="text-neutral-700" />
                <p className="text-[9px] text-neutral-600 font-medium text-center">
                  No pushes yet. Complete a level<br />to see your first sync!
                </p>
              </div>
            )}
            {history.slice(0, 10).map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between px-2.5 py-2 rounded-lg hover:bg-white/[0.02] transition-colors group/item"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <StatusDot status={log.status} />
                  <div className="min-w-0">
                    <span className="text-[10px] text-neutral-300 truncate block font-medium">
                      {log.challenge_title}
                    </span>
                    {log.pushed_at && (
                      <span className="text-[8px] text-neutral-600 font-mono">
                        {new Date(log.pushed_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 opacity-0 group-hover/item:opacity-100 transition-opacity">
                  {log.status === "FAILED" && (
                    <button
                      onClick={() => retryPush(log.id)}
                      className="flex items-center gap-1 text-[8px] font-bold text-amber-400 hover:text-amber-300 uppercase tracking-wider"
                    >
                      <RefreshCw size={9} />
                      Retry
                    </button>
                  )}
                  {log.commit_sha && (
                    <a
                      href={log.commit_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[9px] font-mono text-neutral-600 hover:text-emerald-400 transition-colors"
                    >
                      {log.commit_sha.slice(0, 7)}
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer — Disconnect */}
        <div className="pt-3 border-t border-white/[0.03]">
          {confirmDisconnect ? (
            <div className="flex items-center justify-between bg-red-500/5 border border-red-500/10 rounded-lg px-3 py-2">
              <span className="text-[9px] text-red-300/70 font-medium">Remove GitHub connection?</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { disconnect(); setConfirmDisconnect(false); }}
                  className="text-[9px] font-bold text-red-400 hover:text-red-300 uppercase tracking-wider"
                >
                  Confirm
                </button>
                <button
                  onClick={() => setConfirmDisconnect(false)}
                  className="text-[9px] text-neutral-600 hover:text-neutral-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDisconnect(true)}
              className="text-[9px] text-neutral-700 hover:text-red-400/60 transition-colors font-medium uppercase tracking-wider"
            >
              Disconnect
            </button>
          )}
        </div>
      </div>
    </Card>
  );
}

// ─── Sub-Components ─────────────────────────────────────────────────────

function StatusDot({ status }) {
  const config = {
    SUCCESS: { color: "bg-emerald-400", shadow: "shadow-[0_0_4px_rgba(52,211,153,0.5)]" },
    FAILED: { color: "bg-red-400", shadow: "" },
    PENDING: { color: "bg-amber-400", shadow: "", animate: "animate-pulse" },
    IN_PROGRESS: { color: "bg-blue-400", shadow: "", animate: "animate-pulse" },
    SKIPPED: { color: "bg-neutral-600", shadow: "" },
  };
  const c = config[status] || config.SKIPPED;
  return <span className={`w-2 h-2 rounded-full shrink-0 ${c.color} ${c.shadow || ""} ${c.animate || ""}`} />;
}

function GitHubIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  );
}
