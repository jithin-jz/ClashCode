import React from "react";
import { User as UserIcon } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { getActionBadge, renderDetails } from "../utils/auditUtils";

/**
 * AuditLogMobileList Component
 * 
 * Card-based view for viewing system audit logs on mobile devices.
 */
const AuditLogMobileList = ({
  loading,
  logs,
}) => {
  if (loading) {
    return (
      <div className="space-y-3 md:hidden">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="admin-panel h-36 animate-pulse bg-white/[0.02]"
          />
        ))}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="admin-panel px-4 py-10 text-center text-sm italic text-neutral-500 md:hidden">
        No logs recorded.
      </div>
    );
  }

  return (
    <div className="space-y-3 md:hidden">
      {logs.map((log, idx) => (
        <div
          key={
            log.request_id ||
            `${log.timestamp}-${log.admin}-${log.action}-${log.target}-${idx}`
          }
          className="admin-panel p-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-[10px] font-bold text-neutral-500">
                  {log.admin ? log.admin[0].toUpperCase() : "S"}
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-neutral-100">
                    {log.admin || "System"}
                  </div>
                  <div className="truncate text-[11px] text-neutral-500">
                    {log.target}
                  </div>
                </div>
              </div>
            </div>
            <div className="shrink-0">{getActionBadge(log.action)}</div>
          </div>
          <div className="mt-3 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-[10px] font-mono text-neutral-400">
            {renderDetails(log.details)}
          </div>
          <div className="mt-3 flex items-center justify-between gap-3 text-[11px]">
            <div className="flex items-center gap-1.5 text-neutral-400">
              <UserIcon size={12} className="text-neutral-500" />
              <span className="truncate">{log.target}</span>
            </div>
            <div className="text-right">
              <div className="text-neutral-300">
                {log.timestamp
                  ? formatDistanceToNow(new Date(log.timestamp), {
                      addSuffix: true,
                    })
                  : "Unknown"}
              </div>
              <div className="text-[9px] uppercase text-neutral-600">
                {log.timestamp
                  ? new Date(log.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : ""}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default AuditLogMobileList;
