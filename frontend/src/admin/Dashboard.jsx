import React from "react";
import { Skeleton } from "boneyard-js/react";

// Components
import AdminSidebar from "./AdminSidebar";
import UserTable from "./UserTable";
import AdminTasks from "./AdminTasks";
import Analytics from "./analytics";
import AdminBroadcast from "./AdminBroadcast";
import AdminAuditLogs from "./AdminAuditLogs";
import AdminStore from "./AdminStore";
import AdminReports from "./AdminReports";
import AdminCeleryMonitor from "./AdminCeleryMonitor";
import AppBackdrop from "../components/AppBackdrop";
import SystemOverview from "./components/SystemOverview";

// Hooks
import { useAdminDashboard } from "./hooks/useAdminDashboard";

const AdminDashboard = () => {
  const {
    user,
    loading,
    activeTab,
    setActiveTab,
    rawStats,
    userList,
    tableLoading,
    userFilters,
    integrity,
    fetchUsers,
    handleBlockToggle,
    handleDeleteUser,
    handleLogout,
  } = useAdminDashboard();

  const handleUsersQueryChange = (changes) => {
    fetchUsers(changes);
  };

  return (
    <Skeleton name="admin-dashboard" loading={loading}>
      <div className="relative h-screen overflow-hidden bg-black font-sans antialiased text-foreground">
        <AppBackdrop variant="admin" />
        <div className="relative z-10 flex h-full flex-col md:flex-row">
          <AdminSidebar
            user={user}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            handleLogout={handleLogout}
          />

          <main className="flex-1 min-h-0 h-full overflow-y-auto ds-scrollbar">
            <div className="mx-auto max-w-7xl space-y-6 p-3 sm:p-6 lg:p-8">
              {activeTab === "users" && (
                <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
                  <SystemOverview
                    integrity={integrity}
                    rawStats={rawStats}
                    setActiveTab={setActiveTab}
                  />

                  <UserTable
                    userList={userList}
                    tableLoading={tableLoading}
                    currentUser={user}
                    handleBlockToggle={handleBlockToggle}
                    handleDeleteUser={handleDeleteUser}
                    fetchUsers={fetchUsers}
                    userFilters={userFilters}
                    onUsersQueryChange={handleUsersQueryChange}
                  />
                </div>
              )}

              {activeTab === "analytics" && (
                <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
                  <Analytics />
                </div>
              )}

              {activeTab === "tasks" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminTasks />
                </div>
              )}

              {activeTab === "store" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminStore />
                </div>
              )}

              {activeTab === "broadcast" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminBroadcast />
                </div>
              )}

              {activeTab === "audit" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminAuditLogs />
                </div>
              )}

              {activeTab === "reports" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminReports />
                </div>
              )}

              {activeTab === "celery" && (
                <div className="animate-in slide-in-from-bottom-4 duration-500">
                  <AdminCeleryMonitor />
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </Skeleton>
  );
};

export default AdminDashboard;
