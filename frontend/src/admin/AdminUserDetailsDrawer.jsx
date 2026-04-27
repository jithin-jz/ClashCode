import React, { useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { 
  User as UserIcon, 
  Mail, 
  Calendar, 
  Shield, 
  Activity, 
  FileText, 
  Flag, 
  ShoppingBag, 
  Trophy, 
  Clock,
  ExternalLink,
  MessageSquare
} from "lucide-react";
import { authAPI } from "../services/api";
import { notify } from "../services/notification";
import { getErrorMessage } from "../utils/errorUtils";
import { Badge } from "../components/ui/badge";

const AdminUserDetailsDrawer = ({
  username,
  open,
  onOpenChange,
  onRefreshUsers,
}) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("overview"); // overview, history, moderation
  
  const [noteBody, setNoteBody] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [reportSummary, setReportSummary] = useState("");
  
  const [savingRole, setSavingRole] = useState(false);
  const [savingNote, setSavingNote] = useState(false);
  const [savingReport, setSavingReport] = useState(false);

  const fetchDetails = async () => {
    if (!username) return;
    setLoading(true);
    try {
      const response = await authAPI.getUserDetails(username);
      setDetails(response.data);
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to load user details"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && username) {
      fetchDetails();
      setActiveTab("overview");
    }
  }, [open, username]);

  const roleValue = useMemo(() => details?.role || "user", [details?.role]);

  const handleRoleChange = async (event) => {
    const nextRole = event.target.value;
    if (!username || !nextRole || nextRole === roleValue) return;
    setSavingRole(true);
    try {
      await authAPI.updateUserRole(username, nextRole);
      notify.success(`Updated role to ${nextRole}`);
      await fetchDetails();
      onRefreshUsers?.();
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to update role"));
    } finally {
      setSavingRole(false);
    }
  };

  const handleAddNote = async () => {
    if (!noteBody.trim() || !username) return;
    setSavingNote(true);
    try {
      await authAPI.createUserNote(username, { body: noteBody.trim() });
      setNoteBody("");
      notify.success("Admin note added");
      await fetchDetails();
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to add note"));
    } finally {
      setSavingNote(false);
    }
  };

  const handleCreateReport = async () => {
    if (!reportTitle.trim() || !reportSummary.trim() || !username) return;
    setSavingReport(true);
    try {
      await authAPI.createReport({
        target: username,
        title: reportTitle.trim(),
        summary: reportSummary.trim(),
      });
      setReportTitle("");
      setReportSummary("");
      notify.success("Report added to queue");
      await fetchDetails();
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to create report"));
    } finally {
      setSavingReport(false);
    }
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "history", label: "History", icon: Clock },
    { id: "moderation", label: "Moderation", icon: Shield },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl border-white/10 bg-[#0A0A0A] p-0 overflow-hidden text-white sm:rounded-2xl">
        <DialogHeader className="sr-only">
          <DialogTitle>User Workspace</DialogTitle>
        </DialogHeader>

        {loading || !details ? (
          <div className="p-8 space-y-6">
            <div className="flex items-center gap-4 animate-pulse">
              <div className="h-16 w-16 rounded-full bg-white/5" />
              <div className="space-y-2 flex-1">
                <div className="h-4 w-1/3 rounded bg-white/5" />
                <div className="h-3 w-1/2 rounded bg-white/5" />
              </div>
            </div>
            <div className="h-64 w-full animate-pulse rounded-xl bg-white/[0.02]" />
          </div>
        ) : (
          <div className="flex flex-col h-full max-h-[85vh]">
            {/* Header Section */}
            <div className="relative border-b border-white/5 bg-white/[0.02] p-5 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="relative group">
                    <div className="h-16 w-16 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition-transform group-hover:scale-105">
                      {details.user?.profile?.avatar_url ? (
                        <img
                          src={details.user.profile.avatar_url}
                          alt={details.user.username}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                          <UserIcon size={24} className="text-indigo-400" />
                        </div>
                      )}
                    </div>
                    <div className={`absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-[#0A0A0A] ${details.summary?.last_login ? 'bg-emerald-500' : 'bg-neutral-600'}`} />
                  </div>
                  
                  <div className="min-w-0">
                    <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                      {details.user?.username}
                      <Badge variant="outline" className="text-[9px] uppercase tracking-wider h-4 border-white/10 bg-white/5 font-mono">
                        ID: {details.user?.id || "N/A"}
                      </Badge>
                    </h2>
                    <div className="mt-1 flex items-center gap-3 text-sm text-neutral-500">
                      <span className="flex items-center gap-1.5 whitespace-nowrap"><Mail size={12} /> {details.user?.email}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 sm:self-start">
                  <div className="relative">
                    <select
                      value={roleValue}
                      onChange={handleRoleChange}
                      disabled={savingRole}
                      style={{ colorScheme: "dark" }}
                      className="appearance-none bg-white/10 border border-white/10 rounded-lg px-3 py-1.5 pr-8 text-xs font-medium text-neutral-200 hover:bg-white/15 transition-colors focus:outline-none focus:ring-1 focus:ring-white/20"
                    >
                      <option value="user" className="bg-[#0A0A0A] text-white">User</option>
                      <option value="staff" className="bg-[#0A0A0A] text-white">Staff</option>
                      <option value="superuser" className="bg-[#0A0A0A] text-white">Superuser</option>
                    </select>
                    <Shield size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-500 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="mt-6 flex items-center gap-1 overflow-x-auto ds-scrollbar pb-1 px-5 sm:px-6">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-medium transition-all whitespace-nowrap ${
                        activeTab === tab.id
                          ? "bg-white text-black shadow-lg shadow-white/5"
                          : "text-neutral-500 hover:bg-white/5 hover:text-neutral-300"
                      }`}
                    >
                      <Icon size={14} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto ds-scrollbar p-5 sm:p-6">
              {activeTab === "overview" && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <StatBox icon={Trophy} label="Completed" value={details.summary?.completed_challenges || 0} color="text-yellow-400" />
                    <StatBox icon={ExternalLink} label="Unlocked" value={details.summary?.unlocked_challenges || 0} color="text-blue-400" />
                    <StatBox icon={ShoppingBag} label="Purchases" value={details.summary?.purchase_count || 0} color="text-purple-400" />
                    <StatBox icon={Flag} label="Reports" value={details.summary?.open_reports || 0} color="text-red-400" />
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                      <div className="flex items-center gap-2 text-xs font-medium text-neutral-500 uppercase tracking-wider mb-3">
                        <Calendar size={14} /> Account Activity
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-neutral-400">Joined Date</span>
                          <span className="text-xs font-medium text-neutral-200">
                            {details.summary?.joined_at ? new Date(details.summary.joined_at).toLocaleDateString() : "N/A"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-neutral-400">Last Login</span>
                          <span className="text-xs font-medium text-neutral-200">
                            {details.summary?.last_login ? new Date(details.summary.last_login).toLocaleString() : "Never"}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex flex-col justify-center items-center text-center">
                      <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-2">
                        <Activity size={20} />
                      </div>
                      <div className="text-xs font-medium text-neutral-200">Account Health</div>
                      <div className="text-[10px] text-neutral-500 mt-1 uppercase tracking-tighter">Good Standing</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "history" && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <CompactHistoryCard
                    title="Recent Challenges"
                    icon={Trophy}
                    rows={details.recent_completions || []}
                    renderRow={(row) => (
                      <div className="flex items-center justify-between w-full">
                        <span className="font-medium text-neutral-200 truncate pr-2">{row.challenge}</span>
                        <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/20 text-yellow-500 text-[10px] shrink-0">
                          {row.stars} ★
                        </Badge>
                      </div>
                    )}
                  />
                  <CompactHistoryCard
                    title="Recent Purchases"
                    icon={ShoppingBag}
                    rows={details.recent_purchases || []}
                    renderRow={(row) => (
                      <div className="flex items-center justify-between w-full">
                        <span className="font-medium text-neutral-200 truncate pr-2">{row.name}</span>
                        <span className="text-neutral-500 font-mono text-[11px] shrink-0">{row.cost} XP</span>
                      </div>
                    )}
                  />
                </div>
              )}

              {activeTab === "moderation" &&                 <div className="grid sm:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  {/* Admin Notes */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                      <h3 className="text-[10px] font-bold text-white flex items-center gap-2 uppercase tracking-[0.15em]">
                        <MessageSquare size={12} className="text-neutral-500" /> Admin Notes
                      </h3>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-2.5 focus-within:border-white/20 transition-colors">
                      <Textarea
                        value={noteBody}
                        onChange={(e) => setNoteBody(e.target.value)}
                        placeholder="Type an internal note..."
                        className="bg-transparent border-none p-0 min-h-[40px] text-[11px] resize-none focus-visible:ring-0 placeholder:text-neutral-600"
                      />
                      <div className="mt-2 flex justify-end">
                        <Button
                          onClick={handleAddNote}
                          disabled={savingNote || !noteBody.trim()}
                          size="sm"
                          className="h-6 px-2.5 bg-white text-black hover:bg-neutral-200 text-[10px] font-black"
                        >
                          {savingNote ? "..." : "Add Note"}
                        </Button>
                      </div>
                    </div>
                    <div className="space-y-1.5 max-h-[180px] overflow-y-auto ds-scrollbar pr-1">
                      {(details.notes || []).length === 0 ? (
                        <p className="text-center text-[10px] text-neutral-600 py-4 italic uppercase tracking-wider">No notes recorded.</p>
                      ) : (
                        details.notes.map((note) => (
                          <div key={note.id} className="rounded-lg border border-white/5 bg-white/[0.01] p-2.5 group">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-tighter">{note.admin}</span>
                              <span className="text-[8px] text-neutral-600 font-mono uppercase">
                                {new Date(note.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <p className="text-[10px] text-neutral-500 leading-relaxed line-clamp-2 group-hover:line-clamp-none transition-all">{note.body}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Reports Queue */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                      <h3 className="text-[10px] font-bold text-white flex items-center gap-2 uppercase tracking-[0.15em]">
                        <Flag size={12} className="text-neutral-500" /> Create Report
                      </h3>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-2.5 space-y-2.5">
                      <input
                        value={reportTitle}
                        onChange={(e) => setReportTitle(e.target.value)}
                        placeholder="Subject title..."
                        className="w-full bg-transparent border-b border-white/5 pb-1.5 text-xs text-white focus:outline-none placeholder:text-neutral-600 font-bold"
                      />
                      <Textarea
                        value={reportSummary}
                        onChange={(e) => setReportSummary(e.target.value)}
                        placeholder="Context/Reasoning..."
                        className="bg-transparent border-none p-0 min-h-[40px] text-[11px] resize-none focus-visible:ring-0 placeholder:text-neutral-600"
                      />
                      <div className="flex justify-end">
                        <Button
                          onClick={handleCreateReport}
                          disabled={savingReport || !reportTitle.trim() || !reportSummary.trim()}
                          size="sm"
                          className="h-6 px-2.5 border border-white/10 bg-transparent text-white hover:bg-white/5 text-[10px] font-black"
                        >
                          {savingReport ? "..." : "File Report"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>v>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

const StatBox = ({ icon: Icon, label, value, color }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3 text-center group hover:bg-white/[0.04] transition-colors">
    <div className={`mx-auto mb-1.5 flex h-7 w-7 items-center justify-center rounded-lg bg-white/[0.03] ${color}`}>
      <Icon size={14} />
    </div>
    <div className="text-[9px] font-bold uppercase tracking-[0.1em] text-neutral-600 group-hover:text-neutral-400 transition-colors">
      {label}
    </div>
    <div className="text-lg font-bold text-neutral-100">{value}</div>
  </div>
);

const CompactHistoryCard = ({ title, icon: Icon, rows, renderRow }) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2 px-1">
      <div className="h-6 w-6 rounded-md bg-white/5 flex items-center justify-center text-neutral-500">
        <Icon size={14} />
      </div>
      <h3 className="text-xs font-semibold text-neutral-300 uppercase tracking-widest">{title}</h3>
    </div>
    <div className="space-y-1.5">
      {rows.length === 0 ? (
        <div className="text-center py-6 border border-dashed border-white/5 rounded-xl">
          <p className="text-[10px] text-neutral-600 uppercase tracking-widest">No Activity</p>
        </div>
      ) : (
        rows.map((row, index) => (
          <div
            key={index}
            className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.01] p-3 text-xs transition-colors hover:bg-white/[0.03]"
          >
            {renderRow(row)}
          </div>
        ))
      )}
    </div>
  </div>
);

export default AdminUserDetailsDrawer;
