import React, { useEffect, useState, useCallback } from "react";
import { Button } from "../components/ui/button";
import { authAPI } from "../services/api";
import { notify } from "../services/notification";
import { getErrorMessage } from "../utils/errorUtils";

const AdminReports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [reportsUnavailable, setReportsUnavailable] = useState(false);

  const fetchReports = useCallback(async (overrides = {}, options = {}) => {
    setLoading(true);
    try {
      const params = {
        status: overrides.status ?? statusFilter,
        priority: overrides.priority ?? priorityFilter,
      };
      const response = await authAPI.getReports(params);
      setReports(response.data?.results || []);
      setStatusFilter(params.status ?? statusFilter);
      setPriorityFilter(params.priority ?? priorityFilter);
      setReportsUnavailable(false);
    } catch (error) {
      const unavailable = error?.response?.status === 404;
      setReportsUnavailable(unavailable);
      if (!options.silent) {
        notify.error(getErrorMessage(error, "Failed to load reports"));
      }
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter]);

  useEffect(() => {
    fetchReports({}, { silent: true });
  }, [fetchReports]);

  const updateStatus = async (reportId, status) => {
    try {
      await authAPI.updateReport(reportId, { status });
      notify.success("Report updated");
      fetchReports();
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to update report"));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-semibold text-neutral-100 tracking-tight">
          Reports Queue
        </h2>
        <div className="flex flex-col gap-2 sm:flex-row">
          <select
            value={statusFilter}
            onChange={(e) => fetchReports({ status: e.target.value })}
            style={{ colorScheme: "dark" }}
            className="admin-control h-9 rounded-md px-3 text-xs"
          >
            <option value="" className="bg-[#0A0A0A] text-white">All Statuses</option>
            <option value="OPEN" className="bg-[#0A0A0A] text-white">Open</option>
            <option value="IN_REVIEW" className="bg-[#0A0A0A] text-white">In Review</option>
            <option value="RESOLVED" className="bg-[#0A0A0A] text-white">Resolved</option>
          </select>
          <select
            value={priorityFilter}
            onChange={(e) => fetchReports({ priority: e.target.value })}
            style={{ colorScheme: "dark" }}
            className="admin-control h-9 rounded-md px-3 text-xs"
          >
            <option value="" className="bg-[#0A0A0A] text-white">All Priorities</option>
            <option value="LOW" className="bg-[#0A0A0A] text-white">Low</option>
            <option value="MEDIUM" className="bg-[#0A0A0A] text-white">Medium</option>
            <option value="HIGH" className="bg-[#0A0A0A] text-white">High</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchReports()}
            className="h-9 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
          >
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="admin-panel h-32 animate-pulse bg-white/[0.02]"
            />
          ))}
        </div>
      ) : reportsUnavailable ? (
        <div className="admin-panel px-4 py-6 text-sm text-amber-200">
          Reports are not available from the current backend process yet.
          Restart the `core` service once and this queue will begin loading.
        </div>
      ) : reports.length === 0 ? (
        <div className="admin-panel px-4 py-10 text-center text-sm italic text-neutral-500">
          No reports in queue.
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div key={report.id} className="admin-panel p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold text-neutral-100">
                      {report.title}
                    </h3>
                    <span className="admin-muted-badge rounded-md px-2 py-0.5 text-[9px] uppercase tracking-wider">
                      {report.priority}
                    </span>
                    <span className="admin-muted-badge rounded-md px-2 py-0.5 text-[9px] uppercase tracking-wider">
                      {report.status}
                    </span>
                  </div>
                  <div className="text-xs text-neutral-500">
                    Target: {report.target} • By: {report.created_by}
                  </div>
                  <p className="text-sm text-neutral-400">{report.summary}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateStatus(report.id, "IN_REVIEW")}
                    className="h-9 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
                  >
                    Review
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateStatus(report.id, "RESOLVED")}
                    className="h-9 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
                  >
                    Resolve
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminReports;
