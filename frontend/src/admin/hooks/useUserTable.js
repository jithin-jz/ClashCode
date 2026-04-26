import { useState, useEffect, useMemo } from "react";
import { authAPI } from "../../services/api";
import { notify } from "../../services/notification";
import { getErrorMessage } from "../../utils/errorUtils";

export const useUserTable = (
  userList,
  fetchUsers,
  userFilters,
  onUsersQueryChange,
) => {
  const [searchValue, setSearchValue] = useState(userFilters?.search || "");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [selectedBulkAction, setSelectedBulkAction] = useState("block");
  const [detailsUser, setDetailsUser] = useState(null);

  useEffect(() => {
    setSearchValue(userFilters?.search || "");
  }, [userFilters?.search]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if ((userFilters?.search || "") !== searchValue) {
        onUsersQueryChange?.({ search: searchValue });
      }
    }, 350);
    return () => clearTimeout(timeout);
  }, [searchValue, userFilters?.search, onUsersQueryChange]);

  useEffect(() => {
    setPage(1);
  }, [userFilters?.search, userFilters?.role, userFilters?.status]);

  const count = userList.length;
  const totalPages = Math.max(1, Math.ceil(count / pageSize));

  const paginatedUsers = useMemo(() => {
    const startIndex = (page - 1) * pageSize;
    return userList.slice(startIndex, startIndex + pageSize);
  }, [userList, page, pageSize]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  useEffect(() => {
    setSelectedUsers((current) =>
      current.filter((username) =>
        userList.some((user) => user.username === username),
      ),
    );
  }, [userList]);

  const toggleSelectedUser = (username) => {
    setSelectedUsers((current) =>
      current.includes(username)
        ? current.filter((item) => item !== username)
        : current.concat(username),
    );
  };

  const handleBulkAction = async () => {
    if (selectedUsers.length === 0) {
      notify.error("Select at least one user first");
      return;
    }
    try {
      const response = await authAPI.bulkUserAction({
        action: selectedBulkAction,
        usernames: selectedUsers,
      });
      const updatedCount = response.data?.updated?.length || 0;
      const skippedCount = response.data?.skipped?.length || 0;
      notify.success(
        `Bulk action finished: ${updatedCount} updated${skippedCount ? `, ${skippedCount} skipped` : ""}`,
      );
      setSelectedUsers([]);
      fetchUsers(userFilters);
    } catch (error) {
      notify.error(getErrorMessage(error, "Bulk action failed"));
    }
  };

  const handleExport = async () => {
    try {
      const response = await authAPI.exportUsers(userFilters);
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "admin-users.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      notify.error(getErrorMessage(error, "Failed to export users"));
    }
  };

  const start = count > 0 ? (page - 1) * pageSize + 1 : 0;
  const end = count > 0 ? Math.min(page * pageSize, count) : 0;

  return {
    searchValue,
    setSearchValue,
    page,
    setPage,
    pageSize,
    setPageSize,
    selectedUsers,
    setSelectedUsers,
    selectedBulkAction,
    setSelectedBulkAction,
    detailsUser,
    setDetailsUser,
    paginatedUsers,
    totalPages,
    toggleSelectedUser,
    handleBulkAction,
    handleExport,
    count,
    start,
    end,
  };
};
