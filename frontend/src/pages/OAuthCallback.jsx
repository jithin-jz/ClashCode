import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import useAuthStore from "../stores/useAuthStore";
import { Skeleton } from "boneyard-js/react";

const OAuthCallback = ({ provider }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const {
    user,
    loading,
    error,
    isAuthenticated,
    handleOAuthCallback,
    clearError,
  } = useAuthStore();
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPopup, setIsPopup] = useState(false);

  // Helper to determine redirect path based on user role
  const getRedirectPath = () => "/home";

  useEffect(() => {
    // Check if this is a popup window
    const isPopupWindow = window.opener && !window.opener.closed;
    const targetOrigin = window.location.origin;
    setIsPopup(isPopupWindow);

    const processCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const errorParam = searchParams.get("error");

      if (errorParam) {
        if (isPopupWindow) {
          // Send error to parent and close
          window.opener.postMessage(
            {
              type: "oauth-error",
              provider,
              error: errorParam,
            },
            targetOrigin,
          );
          window.close();
        }
        return;
      }

      if (!code) {
        return;
      }

      // Check if this code was already processed using sessionStorage
      const processedKey = `oauth_processed_${code}`;
      if (sessionStorage.getItem(processedKey)) {
        return;
      }

      // Mark as processing
      setIsProcessing(true);
      sessionStorage.setItem(processedKey, "true");

      try {
        const success = await handleOAuthCallback(provider, code, state);

        if (success) {
          if (isPopupWindow) {
            // Notify parent window and close popup
            window.opener.postMessage(
              {
                type: "oauth-success",
                provider,
              },
              targetOrigin,
            );
            window.close();
          } else {
            // Get fresh user data from store and redirect based on role
            const currentUser = useAuthStore.getState().user;
            const redirectPath = getRedirectPath(currentUser);
            navigate(redirectPath, { replace: true });
          }
        } else {
          // Handle failure (e.g. Blocked User)
          const storeError = useAuthStore.getState().error;
          if (isPopupWindow) {
            window.opener.postMessage(
              {
                type: "oauth-error",
                provider,
                error: storeError,
              },
              targetOrigin,
            );
            window.close();
          }
        }
      } catch (err) {
        console.error("OAuth callback error:", err);
        // Clear the processed flag on error so user can retry
        sessionStorage.removeItem(processedKey);

        if (isPopupWindow) {
          window.opener.postMessage(
            {
              type: "oauth-error",
              provider,
              error: err.message,
            },
            targetOrigin,
          );
          window.close();
        }
      } finally {
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [searchParams, provider, handleOAuthCallback, navigate]);

  useEffect(() => {
    if (isAuthenticated && !isPopup) {
      const redirectPath = getRedirectPath(user);
      navigate(redirectPath, { replace: true });
    }
  }, [isAuthenticated, navigate, isPopup, user]);

  if (loading || isProcessing) {
    return (
      <Skeleton
        name="oauth-callback"
        loading
        className="min-h-screen flex items-center justify-center px-4 bg-[#000000]"
      >
        <div className="w-full max-w-md rounded-[2rem] border border-white/10 bg-[#141414]/60 backdrop-blur-3xl p-8 space-y-6 text-center">
          <div className="h-10 w-48 rounded-md mx-auto bg-white/[0.04] animate-pulse" />
          <div className="h-4 w-64 rounded mx-auto bg-white/[0.04] animate-pulse" />
          <div className="space-y-4 pt-4">
            <div className="h-12 w-full rounded-2xl bg-white/[0.04] animate-pulse" />
            <div className="h-12 w-full rounded-2xl bg-white/[0.04] animate-pulse" />
          </div>
        </div>
      </Skeleton>
    );
  }

  if (error || searchParams.get("error")) {
    const errorMessage =
      error ||
      `Authentication was cancelled or failed: ${searchParams.get("error")}`;
    return (
      <div className="flex items-center justify-center bg-[#000000] px-4 py-20">
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center max-w-md">
          <div className="text-5xl mb-4">❌</div>
          <h2 className="text-white text-2xl font-semibold mb-3">
            Authentication Failed
          </h2>
          <p className="text-white/60 mb-6">{errorMessage}</p>
          <button
            onClick={() => {
              clearError();
              if (isPopup) {
                window.close();
              } else {
                navigate("/login");
              }
            }}
            className="px-8 py-3 bg-linear-to-r from-blue-600 to-blue-500 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all hover:-translate-y-0.5"
          >
            {isPopup ? "Close" : "Try Again"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <Skeleton
      name="oauth-callback"
      loading={false}
      className="min-h-screen flex items-center justify-center px-4 bg-[#000000]"
    >
      <div className="w-full max-w-md rounded-[2rem] border border-white/10 bg-[#141414]/60 backdrop-blur-3xl p-8 space-y-6 text-center">
        <div className="h-10 w-56 rounded-md mx-auto bg-white/[0.04] animate-pulse" />
        <div className="h-4 w-64 rounded mx-auto bg-white/[0.04] animate-pulse" />
        <div className="space-y-4 pt-4">
          <div className="h-12 w-full rounded-2xl bg-white/[0.04] animate-pulse" />
          <div className="h-12 w-full rounded-2xl bg-white/[0.04] animate-pulse" />
        </div>
      </div>
    </Skeleton>
  );
};

export default OAuthCallback;
