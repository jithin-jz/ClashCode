import { Navigate, useLocation } from "react-router-dom";
import useAuthStore from "../stores/useAuthStore";
import { isBoneyard } from "../utils/isBoneyard";
import { PageSkeletonForPath } from "../bones/RouteSkeleton";

/**
 * PublicOnlyRoute - For login/register pages
 * Redirects authenticated users based on role:
 * - Admins → /admin/dashboard
 * - Regular users → /home
 */
const PublicOnlyRoute = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, isInitialized, user, loading } = useAuthStore();

  // Wait for auth check to complete before rendering
  if (!isInitialized || loading) {
    return <PageSkeletonForPath pathname={location.pathname} />;
  }

  // Redirect authenticated users away from public pages (unless crawler)
  if (isAuthenticated && !isBoneyard()) {
    if (user?.is_staff || user?.is_superuser) {
      return <Navigate to="/admin/dashboard" replace />;
    }
    return <Navigate to="/home" replace />;
  }

  return children;
};

export default PublicOnlyRoute;
