import React from "react";
import { Link } from "react-router-dom";
import { Eye, Trash } from "lucide-react";
import { Button } from "../../components/ui/button";

const UserTableMobile = ({
  paginatedUsers,
  tableLoading,
  selectedUsers,
  toggleSelectedUser,
  currentUser,
  setDetailsUser,
  handleDeleteUser,
  handleBlockToggle,
}) => {
  if (tableLoading) {
    return [...Array(4)].map((_, i) => (
      <div key={i} className="admin-panel h-36 animate-pulse bg-white/[0.02]" />
    ));
  }

  if (paginatedUsers.length === 0) {
    return (
      <div className="admin-panel px-4 py-10 text-center text-sm italic text-neutral-500">
        No users found.
      </div>
    );
  }

  return paginatedUsers.map((usr) => (
    <div key={usr.username} className="admin-panel p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <input
            type="checkbox"
            checked={selectedUsers.includes(usr.username)}
            onChange={() => toggleSelectedUser(usr.username)}
            className="mt-1 h-4 w-4 rounded border-white/20 bg-transparent"
          />
          <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-white/10 bg-white/[0.04]">
            {usr.profile?.avatar_url ? (
              <img
                src={usr.profile.avatar_url}
                alt={usr.username}
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="text-xs font-bold text-neutral-500">
                {usr.username[0]?.toUpperCase()}
              </span>
            )}
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-neutral-100">
              {usr.username}
              {currentUser.username === usr.username && (
                <span className="ml-2 text-[10px] font-normal text-neutral-500">
                  (You)
                </span>
              )}
            </div>
            <div className="truncate text-[11px] text-neutral-500">
              {usr.email}
            </div>
          </div>
        </div>
        <div className="shrink-0">
          {usr.is_superuser ? (
            <div className="rounded-md border border-red-500/15 bg-red-500/8 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-red-400">
              Admin
            </div>
          ) : usr.is_staff ? (
            <div className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-neutral-200">
              Staff
            </div>
          ) : (
            <div className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-neutral-300">
              User
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 border-t border-white/8 pt-3">
        <div className="text-[11px] font-medium">
          {usr.is_active ? (
            <div className="flex items-center gap-1.5 text-emerald-400">
              <div className="h-1 w-1 rounded-full bg-emerald-400" />
              Active
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-neutral-500">
              <div className="h-1 w-1 rounded-full bg-neutral-600" />
              Blocked
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDetailsUser(usr.username)}
            className="h-8 px-2 text-[10px] uppercase tracking-wider text-neutral-400 hover:bg-white/10 hover:text-white rounded-md"
          >
            Manage
          </Button>
          <Button
            variant="ghost"
            size="sm"
            asChild
            className="h-8 w-8 p-0 text-neutral-400 hover:bg-white/10 hover:text-white rounded-md"
          >
            <Link to={`/profile/${usr.username}`} target="_blank">
              <Eye className="h-3.5 w-3.5" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDeleteUser(usr.username)}
            disabled={currentUser.username === usr.username}
            className="h-8 w-8 p-0 text-neutral-400 hover:text-red-400 hover:bg-red-500/10 rounded-md"
          >
            <Trash className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={() => handleBlockToggle(usr.username)}
        disabled={currentUser.username === usr.username}
        className={`mt-3 h-9 w-full rounded-md text-[10px] font-semibold uppercase tracking-wider ${
          usr.is_active
            ? "border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-red-500/10 hover:text-red-400"
            : "border-white/10 bg-white/[0.03] text-emerald-400 hover:bg-emerald-500/10"
        }`}
      >
        {usr.is_active ? "Block User" : "Unblock User"}
      </Button>
    </div>
  ));
};

export default UserTableMobile;
