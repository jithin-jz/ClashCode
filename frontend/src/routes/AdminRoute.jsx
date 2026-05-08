import { Navigate, useLocation } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import { isBoneyard } from "../utils/isBoneyard";
import { PageSkeletonForPath } from "../bones/RouteSkeleton";

/**
 * AdminRoute - For admin-only pages
 * Requires user to be authenticated AND be staff/superuser
 */
const AdminRoute = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, user, loading, isInitialized } = useAuthStore(
    useShallow((s) => ({
      isAuthenticated: s.isAuthenticated,
      user: s.user,
      loading: s.loading,
      isInitialized: s.isInitialized,
    })),
  );

  if (loading || !isInitialized) {
    return <PageSkeletonForPath pathname={location.pathname} />;
  }

  // Allow Boneyard crawler to pass through
  if (isBoneyard()) {
    return children;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_staff && !user?.is_superuser) {
    return <Navigate to="/home" replace />;
  }

  return children;
};

export default AdminRoute;
