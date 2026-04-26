import React from "react";
import { Link } from "react-router-dom";
import { Eye, Trash } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Button } from "../../components/ui/button";
import { AdminTableLoadingRow } from "../AdminSkeletons";

const UserTableDesktop = ({
  paginatedUsers,
  tableLoading,
  selectedUsers,
  setSelectedUsers,
  toggleSelectedUser,
  currentUser,
  setDetailsUser,
  handleDeleteUser,
  handleBlockToggle,
}) => {
  return (
    <div className="hidden overflow-hidden md:block admin-panel">
      <Table className="min-w-[760px]">
        <TableHeader>
          <TableRow className="border-white/10 bg-white/[0.02] hover:bg-transparent">
            <TableHead className="w-[48px] py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              <input
                type="checkbox"
                checked={
                  paginatedUsers.length > 0 &&
                  paginatedUsers.every((user) =>
                    selectedUsers.includes(user.username),
                  )
                }
                onChange={(e) =>
                  setSelectedUsers(
                    e.target.checked
                      ? paginatedUsers.map((u) => u.username)
                      : [],
                  )
                }
                className="h-4 w-4 rounded border-white/20 bg-transparent"
              />
            </TableHead>
            <TableHead className="w-[80px] py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Avatar
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              User
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Role
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Status
            </TableHead>
            <TableHead className="py-3 text-right text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tableLoading ? (
            [...Array(6)].map((_, i) => (
              <AdminTableLoadingRow key={i} colSpan={6} />
            ))
          ) : paginatedUsers.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={6}
                className="h-24 text-center text-neutral-500 text-sm italic"
              >
                No users found.
              </TableCell>
            </TableRow>
          ) : (
            paginatedUsers.map((usr) => (
              <TableRow
                key={usr.username}
                className="border-white/10 hover:bg-white/5 transition-colors group"
              >
                <TableCell className="py-3">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(usr.username)}
                    onChange={() => toggleSelectedUser(usr.username)}
                    className="h-4 w-4 rounded border-white/20 bg-transparent"
                  />
                </TableCell>
                <TableCell className="py-3">
                  <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border border-white/10 bg-white/[0.04]">
                    {usr.profile?.avatar_url ? (
                      <img
                        src={usr.profile.avatar_url}
                        alt={usr.username}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-[10px] font-bold text-neutral-500">
                        {usr.username[0]?.toUpperCase()}
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="py-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-neutral-100 tracking-tight">
                      {usr.username}
                      {currentUser.username === usr.username && (
                        <span className="ml-2 text-[10px] text-neutral-500 font-normal">
                          (You)
                        </span>
                      )}
                    </span>
                    <span className="text-[11px] text-neutral-500">
                      {usr.email}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="py-3">
                  <div className="flex items-center gap-2">
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
                </TableCell>
                <TableCell className="py-3 text-[11px] font-medium">
                  {usr.is_active ? (
                    <div className="flex items-center gap-1.5 text-emerald-400">
                      <div className="h-1 w-1 rounded-full bg-emerald-400" />
                      Active
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-neutral-500">
                      <div className="w-1 h-1 rounded-full bg-neutral-600" />
                      Blocked
                    </div>
                  )}
                </TableCell>
                <TableCell className="text-right py-3">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDetailsUser(usr.username)}
                      className="h-8 px-2 text-[10px] uppercase tracking-wider text-neutral-400 hover:text-white hover:bg-white/10 rounded-md"
                    >
                      Manage
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                      className="h-8 w-8 p-0 text-neutral-400 hover:text-white hover:bg-white/10 rounded-md"
                    >
                      <Link to={`/profile/${usr.username}`} target="_blank">
                        <Eye className="h-3.5 w-3.5" />
                      </Link>
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleBlockToggle(usr.username)}
                      disabled={currentUser.username === usr.username}
                      className={`h-8 px-2 text-[10px] font-semibold uppercase tracking-wider rounded-md transition-colors ${
                        usr.is_active
                          ? "text-neutral-400 hover:text-red-400 hover:bg-red-500/10"
                          : "text-emerald-400 hover:bg-emerald-500/10"
                      }`}
                    >
                      {usr.is_active ? "Block" : "Unblock"}
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
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default UserTableDesktop;
