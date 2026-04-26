import React, { lazy, Suspense, memo } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
  Outlet,
} from "react-router-dom";

// Components (loaded immediately)
import ErrorBoundary from "./components/ErrorBoundary";

// Route Guards (loaded immediately)
import ProtectedRoute from "./routes/ProtectedRoute";
import PublicOnlyRoute from "./routes/PublicOnlyRoute";
import AdminRoute from "./routes/AdminRoute";

// Lazy-loaded Pages (code splitting)
const Login = lazy(() => import("./auth/Login"));
const Profile = lazy(() => import("./profile/Profile"));
const Home = lazy(() => import("./pages/Home"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const OAuthCallback = lazy(() => import("./pages/OAuthCallback"));
const AdminDashboard = lazy(() => import("./admin/Dashboard"));
const NotFound = lazy(() => import("./pages/NotFound"));
const BuyXpPage = lazy(() => import("./pages/BuyXpPage"));
const GameRedirectPage = lazy(() => import("./pages/GameRedirectPage"));
const CertificateVerification = lazy(
  () => import("./pages/CertificateVerification"),
);

const ChallengeWorkspace = lazy(() => import("./game/ChallengeWorkspace"));
const MarketplacePage = lazy(() => import("./marketplace/MarketplacePage"));
const AchievementsPage = lazy(() => import("./pages/AchievementsPage"));

// Skeletons — layout-accurate, boneyard-wrapped
import {
  HomeSkeleton,
  ProfileSkeleton,
  AchievementsSkeleton,
  MarketplaceSkeleton,
  LoginSkeleton,
  AdminSkeleton,
  BuyXpSkeleton,
  LandingSkeleton,
  GenericSkeleton,
} from "./bones/PageSkeletons";
import ChallengeWorkspaceSkeleton from "./game/ChallengeWorkspaceSkeleton";

import { useInitializeApp } from "./hooks/useInitializeApp";
import MainLayout from "./common/MainLayout";
import { Toaster } from "./components/ui/sonner";

import { isBoneyard } from "./utils/isBoneyard";

const AppContent = memo(() => {
  const location = useLocation();
  const { user, authLoading } = useInitializeApp();

  // Root application loader — show layout-accurate skeleton while auth initialises
  // BYPASS: If this is the Boneyard crawler, we skip the initial skeleton to render the actual routes/markers.
  if (authLoading && !isBoneyard()) {
    if (location.pathname.startsWith("/level"))
      return <ChallengeWorkspaceSkeleton />;
    if (location.pathname.startsWith("/admin")) return <AdminSkeleton />;
    if (location.pathname.startsWith("/store")) return <MarketplaceSkeleton />;
    if (
      location.pathname.startsWith("/shop") ||
      location.pathname.startsWith("/buy-xp")
    )
      return <BuyXpSkeleton />;
    if (location.pathname.startsWith("/profile")) return <ProfileSkeleton />;
    if (location.pathname.startsWith("/achievements"))
      return <AchievementsSkeleton />;
    if (location.pathname === "/home") return <HomeSkeleton />;
    if (location.pathname === "/login") return <LoginSkeleton />;
    return <GenericSkeleton />;
  }

  return (
    <>
      <Toaster />
      <Routes>
        {/* Public Landing */}
        <Route
          path="/"
          element={
            user ? (
              <Navigate to="/home" replace />
            ) : (
              <Suspense fallback={<LandingSkeleton />}>
                <LandingPage />
              </Suspense>
            )
          }
        />

        {/* Authentication - Public Only */}
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <Suspense fallback={<LoginSkeleton />}>
                <Login />
              </Suspense>
            </PublicOnlyRoute>
          }
        />

        {/* OAuth Callbacks */}
        <Route
          path="/auth/github/callback"
          element={
            <Suspense fallback={<LoginSkeleton />}>
              <OAuthCallback provider="github" />
            </Suspense>
          }
        />
        <Route
          path="/auth/google/callback"
          element={
            <Suspense fallback={<LoginSkeleton />}>
              <OAuthCallback provider="google" />
            </Suspense>
          }
        />

        {/* Public Certificate Verification */}
        <Route
          path="/verify/:certificateId"
          element={
            <Suspense fallback={<GenericSkeleton />}>
              <CertificateVerification />
            </Suspense>
          }
        />

        {/* Protected Routes wrapped in MainLayout */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<GenericSkeleton />}>
                  <Outlet />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        >
          <Route
            path="/home"
            element={
              <Suspense fallback={<HomeSkeleton />}>
                <Home />
              </Suspense>
            }
          />
          <Route
            path="/profile"
            element={
              <Suspense fallback={<ProfileSkeleton />}>
                <Profile />
              </Suspense>
            }
          />
          <Route
            path="/profile/:username"
            element={
              <Suspense fallback={<ProfileSkeleton />}>
                <Profile />
              </Suspense>
            }
          />
          <Route
            path="/shop"
            element={
              <Suspense fallback={<BuyXpSkeleton />}>
                <BuyXpPage />
              </Suspense>
            }
          />
          <Route
            path="/buy-xp"
            element={
              <Suspense fallback={<BuyXpSkeleton />}>
                <BuyXpPage />
              </Suspense>
            }
          />
          <Route
            path="/game"
            element={
              <Suspense fallback={<GenericSkeleton />}>
                <GameRedirectPage />
              </Suspense>
            }
          />
          <Route
            path="/store"
            element={
              <Suspense fallback={<MarketplaceSkeleton />}>
                <MarketplacePage />
              </Suspense>
            }
          />
          <Route
            path="/achievements"
            element={
              <Suspense fallback={<AchievementsSkeleton />}>
                <AchievementsPage />
              </Suspense>
            }
          />
        </Route>

        {/* Workspace Routes (Separate Layouts) */}
        <Route
          path="/level/:id"
          element={
            <ProtectedRoute>
              <Suspense fallback={<ChallengeWorkspaceSkeleton />}>
                <ChallengeWorkspace />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard - Admin Only */}
        <Route
          path="/admin/dashboard"
          element={
            <AdminRoute>
              <Suspense fallback={<AdminSkeleton />}>
                <AdminDashboard />
              </Suspense>
            </AdminRoute>
          }
        />

        <Route
          path="/admin"
          element={<Navigate to="/admin/dashboard" replace />}
        />

        {/* 404 Route */}
        <Route
          path="*"
          element={
            <Suspense fallback={<GenericSkeleton />}>
              <NotFound />
            </Suspense>
          }
        />
      </Routes>
    </>
  );

});

AppContent.displayName = "AppContent";

const App = () => {
  return (
    <Router>
      <ErrorBoundary>
        <AppContent />
      </ErrorBoundary>
    </Router>
  );
};

export default App;
