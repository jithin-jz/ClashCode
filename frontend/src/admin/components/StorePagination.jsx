import React from "react";
import { Button } from "../../components/ui/button";

/**
 * StorePagination Component
 * 
 * Pagination controls and page size selector for Store Management.
 */
const StorePagination = ({
  page,
  setPage,
  totalPages,
  pageSize,
  setPageSize,
  totalCount,
}) => {
  return (
    <div className="flex flex-col gap-3 text-xs text-neutral-500 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <span>
          Showing {totalCount === 0 ? 0 : (page - 1) * pageSize + 1}-
          {Math.min(page * pageSize, totalCount)} of {totalCount}
        </span>
        <select
          value={String(pageSize)}
          onChange={(e) => {
            setPageSize(Number(e.target.value));
            setPage(1);
          }}
          className="admin-control h-8 rounded-md text-xs px-3"
        >
          <option value="10">10 / page</option>
          <option value="25">25 / page</option>
          <option value="50">50 / page</option>
        </select>
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-8 flex-1 px-3 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:flex-none"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Prev
        </Button>
        <span className="text-neutral-400">
          Page {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="h-8 flex-1 px-3 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:flex-none"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default StorePagination;
