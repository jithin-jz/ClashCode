import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../../stores/useAuthStore";
import { authAPI } from "../../services/api";
import { notify } from "../../services/notification";

const normalizeText = (value) => String(value || "").toLowerCase();

const validAdminTabs = new Set([
  "users",
  "analytics",
  "tasks",
  "store",
  "broadcast",
  "audit",
  "reports",
]);

const userMatchesQuery = (user, query) => {
  const search = normalizeText(query?.search).trim();
  if (search) {
    const searchable = [
      user?.username,
      user?.email,
      user?.first_name,
      user?.last_name,
    ]
      .map(normalizeText)
      .join(" ");
    if (!searchable.includes(search)) {
      return false;
    }
  }

  const role = normalizeText(query?.role).trim();
  if (role === "superuser" && !user?.is_superuser) return false;
  if (role === "staff" && (!user?.is_staff || user?.is_superuser)) return false;
  if (role === "user" && (user?.is_staff || user?.is_superuser)) return false;

  const status = normalizeText(query?.status).trim();
  if (status === "active" && !user?.is_active) return false;
  if (status === "blocked" && user?.is_active) return false;

  return true;
};

export const useAdminDashboard = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, checkAuth } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem("admin_active_tab");
    return validAdminTabs.has(savedTab) ? savedTab : "users";
  });

  useEffect(() => {
    localStorage.setItem("admin_active_tab", activeTab);
  }, [activeTab]);

  const [rawStats, setRawStats] = useState({
    total_users: 0,
    active_sessions: 0,
    oauth_logins: 0,
    total_gems: 0,
  });

  const [userList, setUserList] = useState([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [userFilters, setUserFilters] = useState({
    search: "",
    role: "",
    status: "",
  });
  const [integrity, setIntegrity] = useState(null);
  const usersRequestRef = useRef(0);

  useEffect(() => {
    const verifyAdmin = async () => {
      await checkAuth();
      setLoading(false);
    };
    verifyAdmin();
  }, [checkAuth]);

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        navigate("/login");
      } else if (!user?.is_staff && !user?.is_superuser) {
        navigate("/home");
      } else {
        fetchUsers();
        fetchStats();
        fetchIntegrity();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, isAuthenticated, user, navigate, activeTab]);

  const fetchUsers = async (queryOverrides = {}) => {
    const query = { ...userFilters, ...queryOverrides };
    setUserFilters(query);
    setTableLoading(true);
    const requestId = ++usersRequestRef.current;
    try {
      const pageSize = 100;
      const response = await authAPI.getUsers({
        ...query,
        page: 1,
        page_size: pageSize,
      });
      if (requestId !== usersRequestRef.current) return;
      const payload = response.data;

      if (Array.isArray(payload)) {
        const filtered = payload.filter((row) => userMatchesQuery(row, query));
        setUserList(filtered);
      } else {
        let results = payload?.results || [];
        const totalPages = Number(payload?.total_pages || 1);

        if (totalPages > 1) {
          const pageRequests = [];
          for (
            let currentPage = 2;
            currentPage <= totalPages;
            currentPage += 1
          ) {
            pageRequests.push(
              authAPI.getUsers({
                ...query,
                page: currentPage,
                page_size: pageSize,
              }),
            );
          }
          const extraPages = await Promise.all(pageRequests);
          if (requestId !== usersRequestRef.current) return;
          for (const pageResponse of extraPages) {
            const pagePayload = pageResponse.data;
            if (Array.isArray(pagePayload)) {
              results = results.concat(pagePayload);
            } else {
              results = results.concat(pagePayload?.results || []);
            }
          }
        }

        const filteredResults = results.filter((row) =>
          userMatchesQuery(row, query),
        );
        setUserList(filteredResults);
      }
    } catch (error) {
      console.error("Failed to fetch users", error);
    } finally {
      if (requestId === usersRequestRef.current) {
        setTableLoading(false);
      }
    }
  };

  const fetchStats = async () => {
    try {
      const response = await authAPI.getAdminStats();
      setRawStats(response.data);
    } catch (error) {
      console.error("Failed to fetch admin stats", error);
    }
  };

  const fetchIntegrity = async () => {
    try {
      const response = await authAPI.getSystemIntegrity();
      setIntegrity(response.data);
    } catch (error) {
      console.error("Failed to fetch system integrity", error);
    }
  };

  const handleBlockToggle = (username) => {
    const currentUserData = userList.find((u) => u.username === username);
    const action = currentUserData?.is_active ? "ban" : "unban";

    notify.warning("Confirm Action", {
      description: `Are you sure you want to ${action} the user ${username}?`,
      action: {
        label: "Confirm",
        onClick: () => confirmBlockToggle(username),
      },
      cancel: {
        label: "Cancel",
        onClick: () => {},
      },
    });
  };

  const confirmBlockToggle = async (username) => {
    try {
      await authAPI.toggleBlockUser(username);
      notify.success(`User status updated for ${username}`);
      fetchUsers();
    } catch (error) {
      notify.error(
        error.response?.data?.error || "Failed to toggle block status",
      );
    }
  };

  const handleDeleteUser = (username) => {
    notify.warning("Delete User", {
      description: `Permanently delete user ${username}? This cannot be undone.`,
      action: {
        label: "Delete",
        onClick: () => confirmDeleteUser(username),
      },
      cancel: {
        label: "Cancel",
        onClick: () => {},
      },
    });
  };

  const confirmDeleteUser = async (username) => {
    try {
      await authAPI.deleteUser(username);
      notify.success(`User ${username} deleted successfully`);
      fetchUsers();
    } catch (error) {
      notify.error(error.response?.data?.error || "Failed to delete user");
    }
  };

  const handleLogout = async () => {
    localStorage.removeItem("admin_active_tab");
    await logout();
    navigate("/login");
  };

  return {
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
  };
};
