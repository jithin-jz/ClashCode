import { useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import githubSyncService from "../services/api/githubSyncService";

/**
 * GitHub OAuth Callback Handler
 *
 * Route: /settings/github/callback
 *
 * GitHub redirects here after user authorizes the app.
 * Exchanges the code for a connection then redirects to profile.
 */
export default function GitHubSyncCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const called = useRef(false);

  useEffect(() => {
    // Prevent double-call in StrictMode
    if (called.current) return;
    called.current = true;

    const code = searchParams.get("code");

    if (!code) {
      navigate("/profile?github=error&reason=no_code", { replace: true });
      return;
    }

    githubSyncService.connect(code)
      .then(() => {
        navigate("/profile?github=connected", { replace: true });
      })
      .catch(() => {
        navigate("/profile?github=error&reason=exchange_failed", { replace: true });
      });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="text-center space-y-4">
        <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-neutral-500 text-xs font-medium">
          Connecting your GitHub account...
        </p>
      </div>
    </div>
  );
}
