import { Navigate, useLocation } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import { isBoneyard } from "../utils/isBoneyard";
import { PageSkeletonForPath } from "../bones/RouteSkeleton";

/**
 * ProtectedRoute - Requires authentication
 * Redirects unauthenticated users to landing page
 */
const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, isInitialized, loading } = useAuthStore(
    useShallow((s) => ({
      isAuthenticated: s.isAuthenticated,
      isInitialized: s.isInitialized,
      loading: s.loading,
    })),
  );

  if (!isInitialized || loading) {
    return <PageSkeletonForPath pathname={location.pathname} />;
  }

  if (!isAuthenticated && !isBoneyard()) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
