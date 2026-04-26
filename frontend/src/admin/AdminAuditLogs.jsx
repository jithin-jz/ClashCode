import React, { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";
import { authAPI } from "../services/api";
import { notify } from "../services/notification";
import { getErrorMessage } from "../utils/errorUtils";
import { sortLogs } from "./utils/auditUtils";

// Sub-components
import AuditLogFilters from "./components/AuditLogFilters";
import AuditLogTable from "./components/AuditLogTable";
import AuditLogMobileList from "./components/AuditLogMobileList";
import AuditLogPagination from "./components/AuditLogPagination";

/**
 * AdminAuditLogs Component
 * 
 * The main container for system audit logs.
 * Orchestrates data fetching, filtering, and view switching.
 */
const AdminAuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState({
    page: 1,
    page_size: 25,
    search: "",
    action: "",
    admin: "",
    target: "",
    date_from: "",
    date_to: "",
    ordering: "-timestamp",
  });
  const [searchValue, setSearchValue] = useState("");
  const [adminValue, setAdminValue] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [pagination, setPagination] = useState({
    count: 0,
    page: 1,
    page_size: 25,
    total_pages: 1,
  });
  const requestRef = useRef(0);
  const queryRef = useRef(query);

  const fetchLogs = useCallback(async (overrides = {}) => {
    const nextQuery = { ...queryRef.current, ...overrides };
    queryRef.current = nextQuery;
    setQuery(nextQuery);
    setLoading(true);
    const requestId = ++requestRef.current;
    try {
      const response = await authAPI.getAuditLogs(nextQuery);
      if (requestId !== requestRef.current) return;
      const payload = response.data;
      if (Array.isArray(payload)) {
        setLogs(sortLogs(payload, nextQuery.ordering));
        setPagination({
          count: payload.length,
          page: 1,
          page_size: payload.length || nextQuery.page_size,
          total_pages: 1,
        });
      } else {
        const results = payload?.results || [];
        setLogs(sortLogs(results, nextQuery.ordering));
        setPagination({
          count: payload?.count ?? results.length,
          page: payload?.page ?? nextQuery.page,
          page_size: payload?.page_size ?? nextQuery.page_size,
          total_pages: payload?.total_pages ?? 1,
        });
      }
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to fetch audit logs"));
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    queryRef.current = query;
  }, [query]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchValue !== query.search) {
        fetchLogs({ search: searchValue, page: 1 });
      }
    }, 350);
    return () => clearTimeout(timeout);
  }, [searchValue, query.search, fetchLogs]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (adminValue !== query.admin || targetValue !== query.target) {
        fetchLogs({ admin: adminValue, target: targetValue, page: 1 });
      }
    }, 350);
    return () => clearTimeout(timeout);
  }, [adminValue, targetValue, query.admin, query.target, fetchLogs]);

  const handleExport = async () => {
    try {
      const response = await authAPI.exportAuditLogs(query);
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "admin-audit-logs.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to export audit logs"));
    }
  };

  const page = pagination.page || 1;
  const pageSize = pagination.page_size || 25;
  const totalPages = pagination.total_pages || 1;
  const count = pagination.count || 0;
  const start = count > 0 ? (page - 1) * pageSize + 1 : 0;
  const end = count > 0 ? Math.min(page * pageSize, count) : 0;

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h2 className="text-xl font-semibold text-neutral-100 tracking-tight">
            Audit Logs
          </h2>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="h-9 w-full rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
            >
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchLogs(query)}
              disabled={loading}
              className="h-9 w-full gap-2 rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              <span className="text-xs font-medium">
                {loading ? "Refreshing..." : "Refresh"}
              </span>
            </Button>
          </div>
        </div>

        <AuditLogFilters
          searchValue={searchValue}
          setSearchValue={setSearchValue}
          adminValue={adminValue}
          setAdminValue={setAdminValue}
          targetValue={targetValue}
          setTargetValue={setTargetValue}
          dateFrom={dateFrom}
          setDateFrom={setDateFrom}
          dateTo={dateTo}
          setDateTo={setDateTo}
          query={query}
          fetchLogs={fetchLogs}
        />
      </div>

      <AuditLogMobileList loading={loading} logs={logs} />
      <AuditLogTable loading={loading} logs={logs} />

      <AuditLogPagination
        page={page}
        totalPages={totalPages}
        start={start}
        end={end}
        count={count}
        loading={loading}
        fetchLogs={fetchLogs}
      />

      <div className="flex items-center gap-2 px-1">
        <div className="h-1 w-1 rounded-full bg-white/30" />
        <p className="text-[9px] text-neutral-600 font-medium uppercase tracking-wider">
          Audit records are immutable.
        </p>
      </div>
    </div>
  );
};

export default AdminAuditLogs;
