import React from "react";
import { Button } from "../../components/ui/button";

const UserTablePagination = ({
  start,
  end,
  count,
  page,
  totalPages,
  tableLoading,
  setPage,
}) => {
  return (
    <div className="flex flex-col gap-3 text-xs text-neutral-500 sm:flex-row sm:items-center sm:justify-between">
      <span>
        Showing {start}-{end} of {count}
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-8 flex-1 px-3 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:flex-none"
          disabled={page <= 1 || tableLoading}
          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
        >
          Prev
        </Button>
        <span className="min-w-0 text-center text-neutral-400">
          Page {page} / {Math.max(totalPages, 1)}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="h-8 flex-1 px-3 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:flex-none"
          disabled={page >= totalPages || tableLoading}
          onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default UserTablePagination;
