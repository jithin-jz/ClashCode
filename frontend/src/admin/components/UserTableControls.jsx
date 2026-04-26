import React from "react";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { RefreshCw } from "lucide-react";

const UserTableControls = ({
  searchValue,
  setSearchValue,
  userFilters,
  onUsersQueryChange,
  pageSize,
  setPageSize,
  setPage,
  selectedBulkAction,
  setSelectedBulkAction,
  handleBulkAction,
  selectedUsersCount,
  handleExport,
  fetchUsers,
  tableLoading,
}) => {
  return (
    <div className="flex flex-col lg:flex-row gap-3 lg:items-center lg:justify-between">
      <div className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2">
          <Input
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search username or email..."
            className="admin-control h-9 w-full min-w-0 sm:w-72 text-neutral-200"
          />
          <select
            value={userFilters?.role || ""}
            onChange={(e) => onUsersQueryChange?.({ role: e.target.value })}
            className="admin-control h-9 w-full sm:w-auto rounded-md text-xs px-3"
          >
            <option value="">All Roles</option>
            <option value="user">Users</option>
            <option value="staff">Staff</option>
            <option value="superuser">Superusers</option>
          </select>
          <select
            value={userFilters?.status || ""}
            onChange={(e) => onUsersQueryChange?.({ status: e.target.value })}
            className="admin-control h-9 w-full sm:w-auto rounded-md text-xs px-3"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
          </select>
          <select
            value={String(pageSize)}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="admin-control h-9 w-full sm:w-auto rounded-md text-xs px-3"
          >
            <option value="10">10 / page</option>
            <option value="25">25 / page</option>
            <option value="50">50 / page</option>
          </select>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <select
            value={selectedBulkAction}
            onChange={(e) => setSelectedBulkAction(e.target.value)}
            className="admin-control h-9 w-full rounded-md px-3 text-xs sm:w-auto"
          >
            <option value="block">Bulk block</option>
            <option value="unblock">Bulk unblock</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={handleBulkAction}
            disabled={selectedUsersCount === 0}
            className="h-9 w-full rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
          >
            Apply to {selectedUsersCount || 0}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="h-9 w-full gap-2 rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
          >
            Export CSV
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchUsers(userFilters)}
          disabled={tableLoading}
          className="h-9 w-full gap-2 rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span className="text-xs font-medium uppercase tracking-wider">
            {tableLoading ? "Refreshing..." : "Refresh"}
          </span>
        </Button>
      </div>
    </div>
  );
};

export default UserTableControls;
