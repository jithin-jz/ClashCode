import React from "react";
import { User as UserIcon } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { AdminTableLoadingRow } from "../AdminSkeletons";
import { getActionBadge, renderDetails } from "../utils/auditUtils";

/**
 * AuditLogTable Component
 * 
 * Desktop-optimized table for viewing system audit logs.
 */
const AuditLogTable = ({
  loading,
  logs,
}) => {
  return (
    <div className="hidden overflow-hidden md:block admin-panel">
      <Table className="min-w-[980px]">
        <TableHeader>
          <TableRow className="border-white/10 hover:bg-transparent bg-white/[0.02]">
            <TableHead className="px-6 py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Admin
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Action
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Subject
            </TableHead>
            <TableHead className="w-1/3 py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Details
            </TableHead>
            <TableHead className="px-6 py-3 text-right text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Timestamp
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            [...Array(8)].map((_, i) => (
              <AdminTableLoadingRow key={i} colSpan={5} />
            ))
          ) : logs.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="h-32 text-center text-neutral-500 text-xs italic"
              >
                No logs recorded.
              </TableCell>
            </TableRow>
          ) : (
            logs.map((log, idx) => (
              <TableRow
                key={
                  log.request_id ||
                  `${log.timestamp}-${log.admin}-${log.action}-${log.target}-${idx}`
                }
                className="border-white/10 hover:bg-white/5 transition-colors group"
              >
                <TableCell className="py-3 px-6">
                  <div className="flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-[10px] font-bold text-neutral-500">
                      {log.admin ? log.admin[0].toUpperCase() : "S"}
                    </div>
                    <span className="text-sm font-medium text-neutral-100 tracking-tight">
                      {log.admin || "System"}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="py-3">
                  {getActionBadge(log.action)}
                </TableCell>
                <TableCell className="py-3 text-neutral-300">
                  <div className="flex items-center gap-1.5 text-[11px] font-medium">
                    <UserIcon size={12} className="text-neutral-500" />
                    {log.target}
                  </div>
                </TableCell>
                <TableCell className="py-3 text-[10px] font-mono text-neutral-500 group-hover:text-neutral-300 transition-all">
                  <div
                    className="max-w-xs truncate"
                    title={JSON.stringify(log.details)}
                  >
                    {renderDetails(log.details)}
                  </div>
                </TableCell>
                <TableCell className="text-right py-3 px-6">
                  <div className="flex flex-col items-end">
                    <span className="text-[11px] font-medium text-neutral-300">
                      {log.timestamp
                        ? formatDistanceToNow(new Date(log.timestamp), {
                            addSuffix: true,
                          })
                        : "Unknown"}
                    </span>
                    <span className="text-[9px] text-neutral-600 font-mono uppercase">
                      {log.timestamp
                        ? new Date(log.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : ""}
                    </span>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default AuditLogTable;
