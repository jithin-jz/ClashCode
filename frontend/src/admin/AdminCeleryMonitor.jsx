import React, { useEffect, useState, useCallback, useRef } from "react";
import { RefreshCw, Activity, CheckCircle2, X, Clock, Search, ChevronRight, List, Terminal } from "lucide-react";
import { Button } from "../components/ui/button";
import { tasksApi } from "../services/tasksApi";
import { notify } from "../services/notification";
import { getErrorMessage } from "../utils/errorUtils";

/**
 * AdminCeleryMonitor Component
 * 
 * Provides a real-time monitoring interface for Celery tasks.
 * Fetches data from the django-celery-results backend via TaskResultsListView.
 */
const AdminCeleryMonitor = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedTask, setExpandedTask] = useState(null);
  const [filterStatus, setFilterStatus] = useState("");
  const [limit, setLimit] = useState(25);
  
  const refreshInterval = useRef(null);

  const fetchTasks = useCallback(async (isAuto = false) => {
    if (!isAuto) setLoading(true);
    try {
      const params = { limit };
      if (filterStatus) params.status = filterStatus;
      
      const data = await tasksApi.getResults(params);
      setTasks(data.results || []);
    } catch (error) {
      if (!isAuto) {
        notify.error(getErrorMessage(error, "Failed to fetch task logs"));
      }
      console.error("Task fetch error:", error);
    } finally {
      if (!isAuto) setLoading(false);
    }
  }, [filterStatus, limit]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  useEffect(() => {
    if (autoRefresh) {
      refreshInterval.current = setInterval(() => {
        fetchTasks(true);
      }, 5000);
    } else {
      if (refreshInterval.current) clearInterval(refreshInterval.current);
    }
    return () => {
      if (refreshInterval.current) clearInterval(refreshInterval.current);
    };
  }, [autoRefresh, fetchTasks]);

  const getStatusIcon = (status) => {
    switch (status) {
      case "SUCCESS": return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case "FAILURE": return <X className="h-4 w-4 text-rose-500" />;
      case "STARTED":
      case "RETRY": return <Activity className="h-4 w-4 text-amber-500 animate-pulse" />;
      default: return <Clock className="h-4 w-4 text-neutral-500" />;
    }
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case "SUCCESS": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "FAILURE": return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "STARTED":
      case "RETRY": return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default: return "bg-neutral-500/10 text-neutral-400 border-neutral-500/20";
    }
  };

  return (
    <div className="space-y-4">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-neutral-100 flex items-center gap-2">
            <Terminal className="h-5 w-5 text-indigo-400" />
            Worker Task Monitor
          </h2>
          <p className="text-xs text-neutral-500 font-medium">
            Real-time background job execution logs from Celery workers.
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 bg-white/[0.03] border border-white/10 rounded-md px-3 h-9">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Auto Refresh</span>
            <button 
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`relative inline-flex h-4 w-8 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${autoRefresh ? "bg-indigo-600" : "bg-neutral-700"}`}
            >
              <span className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${autoRefresh ? "translate-x-4" : "translate-x-0"}`} />
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchTasks()}
            disabled={loading}
            className="h-9 gap-2 rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="text-xs font-medium">Refresh</span>
          </Button>
        </div>
      </div>

      {/* Filters Section */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <select 
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="h-9 bg-white/[0.03] border border-white/10 rounded-md px-3 text-xs text-neutral-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="SUCCESS">Success</option>
          <option value="FAILURE">Failure</option>
          <option value="STARTED">Started</option>
          <option value="RETRY">Retry</option>
        </select>

        <select 
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="h-9 bg-white/[0.03] border border-white/10 rounded-md px-3 text-xs text-neutral-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="25">Show 25</option>
          <option value="50">Show 50</option>
          <option value="100">Show 100</option>
        </select>
      </div>

      {/* Table Section */}
      <div className="overflow-hidden rounded-xl border border-white/8 bg-black/40 backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/8 bg-white/[0.02]">
                <th className="px-4 py-3 font-semibold text-neutral-400">Status</th>
                <th className="px-4 py-3 font-semibold text-neutral-400">Task Name</th>
                <th className="px-4 py-3 font-semibold text-neutral-400">Completed</th>
                <th className="px-4 py-3 font-semibold text-neutral-400">Worker</th>
                <th className="px-4 py-3 font-semibold text-neutral-400 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/4">
              {loading && tasks.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-12 text-center text-neutral-500">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 opacity-20" />
                    Loading worker logs...
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-12 text-center text-neutral-500 font-medium">
                    No tasks found matching your filters.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <React.Fragment key={task.task_id}>
                    <tr className={`group transition-colors hover:bg-white/[0.02] ${expandedTask === task.task_id ? "bg-white/[0.03]" : ""}`}>
                      <td className="px-4 py-3">
                        <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-tight uppercase ${getStatusStyle(task.status)}`}>
                          {getStatusIcon(task.status)}
                          {task.status}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-neutral-200">
                        {task.task_name || "Unknown Task"}
                        <div className="text-[10px] text-neutral-600 mt-0.5">{task.task_id.substring(0, 8)}...</div>
                      </td>
                      <td className="px-4 py-3 text-neutral-400">
                        {new Date(task.date_done).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-neutral-400 italic">
                        {task.worker || "N/A"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setExpandedTask(expandedTask === task.task_id ? null : task.task_id)}
                          className="h-7 w-7 p-0 hover:bg-white/10"
                        >
                          {expandedTask === task.task_id ? <List size={14} /> : <ChevronRight size={14} />}
                        </Button>
                      </td>
                    </tr>
                    
                    {/* Expanded Content */}
                    {expandedTask === task.task_id && (
                      <tr className="bg-black/60 border-l-2 border-indigo-500/50">
                        <td colSpan="5" className="px-6 py-4">
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <label className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Arguments/Result</label>
                                <pre className="p-3 rounded-lg bg-neutral-900/80 border border-white/5 text-[10px] text-neutral-300 overflow-x-auto font-mono whitespace-pre-wrap max-h-40">
                                  {JSON.stringify(task.result, null, 2)}
                                </pre>
                              </div>
                              {task.traceback && (
                                <div className="space-y-2">
                                  <label className="text-[10px] font-bold text-rose-500 uppercase tracking-widest">Error Traceback</label>
                                  <pre className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/10 text-[10px] text-rose-300 overflow-x-auto font-mono whitespace-pre-wrap max-h-40 italic">
                                    {task.traceback}
                                  </pre>
                                </div>
                              )}
                            </div>
                            <div className="flex gap-4 text-[10px] font-medium text-neutral-600 uppercase tracking-tighter">
                              <span>Full Task ID: {task.task_id}</span>
                              <span>Date Created: {task.date_created ? new Date(task.date_created).toLocaleString() : "N/A"}</span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Footer Info */}
        <div className="border-t border-white/8 bg-white/[0.02] px-4 py-2 flex items-center justify-between">
          <p className="text-[10px] text-neutral-500 font-medium italic">
            * Task logs are retained for 24 hours.
          </p>
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-neutral-400 font-semibold uppercase tracking-wider">Celery Cluster Online</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminCeleryMonitor;
