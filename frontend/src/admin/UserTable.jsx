import React from "react";
import AdminUserDetailsDrawer from "./AdminUserDetailsDrawer";
import UserTableControls from "./components/UserTableControls";
import UserTableMobile from "./components/UserTableMobile";
import UserTableDesktop from "./components/UserTableDesktop";
import UserTablePagination from "./components/UserTablePagination";
import { useUserTable } from "./hooks/useUserTable";

/**
 * UserTable.jsx
 * Now refactored into a coordinator component that manages sub-components.
 */
const UserTable = ({
  userList,
  tableLoading,
  currentUser,
  handleBlockToggle,
  handleDeleteUser,
  fetchUsers,
  userFilters,
  onUsersQueryChange,
}) => {
  const {
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
  } = useUserTable(userList, fetchUsers, userFilters, onUsersQueryChange);

  return (
    <div className="space-y-4">
      <UserTableControls
        searchValue={searchValue}
        setSearchValue={setSearchValue}
        userFilters={userFilters}
        onUsersQueryChange={onUsersQueryChange}
        pageSize={pageSize}
        setPageSize={setPageSize}
        setPage={setPage}
        selectedBulkAction={selectedBulkAction}
        setSelectedBulkAction={setSelectedBulkAction}
        handleBulkAction={handleBulkAction}
        selectedUsersCount={selectedUsers.length}
        handleExport={handleExport}
        fetchUsers={fetchUsers}
        tableLoading={tableLoading}
      />

      <div className="space-y-3 md:hidden">
        <UserTableMobile
          paginatedUsers={paginatedUsers}
          tableLoading={tableLoading}
          selectedUsers={selectedUsers}
          toggleSelectedUser={toggleSelectedUser}
          currentUser={currentUser}
          setDetailsUser={setDetailsUser}
          handleDeleteUser={handleDeleteUser}
          handleBlockToggle={handleBlockToggle}
        />
      </div>

      <UserTableDesktop
        paginatedUsers={paginatedUsers}
        tableLoading={tableLoading}
        selectedUsers={selectedUsers}
        setSelectedUsers={setSelectedUsers}
        toggleSelectedUser={toggleSelectedUser}
        currentUser={currentUser}
        setDetailsUser={setDetailsUser}
        handleDeleteUser={handleDeleteUser}
        handleBlockToggle={handleBlockToggle}
      />

      <UserTablePagination
        start={start}
        end={end}
        count={count}
        page={page}
        totalPages={totalPages}
        tableLoading={tableLoading}
        setPage={setPage}
      />

      <AdminUserDetailsDrawer
        username={detailsUser}
        open={Boolean(detailsUser)}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setDetailsUser(null);
          }
        }}
        onRefreshUsers={() => fetchUsers(userFilters)}
      />
    </div>
  );
};

export default UserTable;
