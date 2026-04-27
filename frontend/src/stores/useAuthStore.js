import { create } from "zustand";
import { authAPI } from "../services/api";
import useChallengesStore from "./useChallengesStore";
import useNotificationStore from "./useNotificationStore";
import { notify } from "../services/notification";
import { isBoneyard } from "../utils/isBoneyard";
import { SLog } from "../services/logger";

// Helper function to open OAuth in a popup window
const openOAuthPopup = (url, name = "OAuth Login") => {
  const width = 500;
  const height = 600;
  const left = window.screenX + (window.outerWidth - width) / 2;
  const top = window.screenY + (window.outerHeight - height) / 2;

  return window.open(
    url,
    name,
    `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,status=yes`,
  );
};

// Helper to generate random state
const generateState = () => {
  const bytes = new Uint8Array(24);
  window.crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
};

const getOAuthStateKey = (provider) => `oauth_state_${provider}`;

const useAuthStore = create((set, get) => ({
  // State
  user: null,
  isAuthenticated: false,
  loading: true,
  isInitialized: false, // Tracks if initial auth check is complete
  error: null,
  oauthPopup: null,
  email: "",
  otp: "",
  showOtpInput: false,
  isOtpLoading: false,
  isOAuthLoading: false,
  oauthCooldownUntil: 0,
  otpCooldownUntil: 0,
  lastOtpEmail: "",
  lastAuthCheck: null,
  authCheckPromise: null,

  // Actions
  setLoading: (loading) => set({ loading }),
  setEmail: (email) => set({ email }),
  setOtp: (otp) => set({ otp }),
  setShowOtpInput: (showOtpInput) => set({ showOtpInput }),

  clearError: () => set({ error: null }),

  // Set User (Used by useUserStore to update profile data)
  setUser: (user) => set({ user }),

  checkAuth: async (force = false) => {
    const state = get();
    const now = Date.now();

    // De-duplicate concurrent auth checks across components.
    if (state.authCheckPromise) {
      return state.authCheckPromise;
    }

    // Reuse recent auth state to reduce request spam.
    if (
      !force &&
      state.isInitialized &&
      state.lastAuthCheck &&
      now - state.lastAuthCheck < 30000 &&
      state.isAuthenticated &&
      state.user
    ) {
      return state.user;
    }

    const authPromise = (async () => {
      // Boneyard Capture Bypass:
      if (isBoneyard()) {
        const mockUser = {
          id: "boneyard-bot",
          username: "boneyard-bot",
          email: "boneyard@clashcode.ai",
          avatar_url: "https://api.dicebear.com/7.x/bottts/svg?seed=boneyard",
          isCrawler: true,
          is_staff: true,
          level: 99,
          xp: 0,
        };
        set({
          user: mockUser,
          isAuthenticated: true,
          loading: false,
          error: null,
          isInitialized: true,
        });
        return mockUser;
      }

      try {
        const response = await authAPI.getCurrentUser();
        const user = response.data;
        set({
          user,
          isAuthenticated: true,
          loading: false,
          error: null,
          isInitialized: true,
          lastAuthCheck: Date.now(),
        });

        // Save tokens to localStorage for WebSocket services if present
        if (response.data.access_token) {
          localStorage.setItem(
            "clashcode_access_token",
            response.data.access_token,
          );
        }
        if (response.data.refresh_token) {
          localStorage.setItem(
            "clashcode_refresh_token",
            response.data.refresh_token,
          );
        }

        SLog.setUser(user);
        return user;
      } catch {
        set({
          user: null,
          isAuthenticated: false,
          loading: false,
          isInitialized: true,
        });
        SLog.setUser(null);
        return null;
      } finally {
        set({
          authCheckPromise: null,
          lastAuthCheck: Date.now(),
        });
      }
    })();

    set({ authCheckPromise: authPromise });
    return authPromise;
  },

  // Open OAuth in popup
  openOAuthPopup: async (provider) => {
    const now = Date.now();
    const storeState = get();
    if (storeState.isOAuthLoading) return null;
    if (storeState.oauthCooldownUntil && now < storeState.oauthCooldownUntil) {
      const seconds = Math.ceil((storeState.oauthCooldownUntil - now) / 1000);
      set({
        error: `Please wait ${seconds}s before trying ${provider} login again.`,
      });
      return null;
    }

    // Open popup immediately inside user gesture to avoid browser popup blocking.
    const popupName = provider === "google" ? "Google Login" : "GitHub Login";
    const popup = openOAuthPopup("about:blank", popupName);
    if (!popup) {
      set({
        loading: false,
        isOAuthLoading: false,
        error: "Popup blocked by browser. Please allow popups and try again.",
      });
      return null;
    }

    set({ loading: true, isOAuthLoading: true, error: null });

    try {
      const oauthState = generateState();
      // Use localStorage so popup and opener can both read it.
      // Keep sessionStorage fallback for backward compatibility.
      localStorage.setItem(getOAuthStateKey(provider), oauthState);
      sessionStorage.setItem(getOAuthStateKey(provider), oauthState);

      let response;

      switch (provider) {
        case "github":
          response = await authAPI.getGithubAuthUrl(oauthState);
          break;
        case "google":
          response = await authAPI.getGoogleAuthUrl(oauthState);
          break;
        default:
          throw new Error("Unknown provider");
      }

      popup.location.href = response.data.url;
      set({
        oauthPopup: popup,
        loading: false,
        isOAuthLoading: false,
        oauthCooldownUntil: Date.now() + 5000,
      });

      return popup;
    } catch (error) {
      if (popup && !popup.closed) {
        popup.close();
      }
      set({
        loading: false,
        isOAuthLoading: false,
        oauthCooldownUntil: Date.now() + 5000,
        error:
          error.response?.data?.error || `Failed to get ${provider} auth URL`,
      });
      return null;
    }
  },

  handleOAuthCallback: async (provider, code, returnedState) => {
    set({ loading: true, error: null });

    // Verify State
    const stateKey = getOAuthStateKey(provider);
    const savedState =
      localStorage.getItem(stateKey) ||
      sessionStorage.getItem(stateKey) ||
      localStorage.getItem("oauth_state") ||
      sessionStorage.getItem("oauth_state");
    localStorage.removeItem(stateKey);
    sessionStorage.removeItem(stateKey);
    localStorage.removeItem("oauth_state");
    sessionStorage.removeItem("oauth_state");

    if (!savedState || savedState !== returnedState) {
      set({
        loading: false,
        error:
          "Security Error: State mismatch (CSRF protection). Please try again.",
      });
      return false;
    }

    try {
      let response;
      switch (provider) {
        case "github":
          response = await authAPI.githubCallback(code);
          break;
        case "google":
          response = await authAPI.googleCallback(code);
          break;
        default:
          throw new Error("Unknown provider");
      }

      const { user } = response.data;

      set({
        user,
        isAuthenticated: true,
        isInitialized: true,
        lastAuthCheck: Date.now(),
        loading: false,
        error: null,
      });

      // Save tokens to localStorage for WebSocket services if present
      if (response.data.access_token) {
        localStorage.setItem(
          "clashcode_access_token",
          response.data.access_token,
        );
      }
      if (response.data.refresh_token) {
        localStorage.setItem(
          "clashcode_refresh_token",
          response.data.refresh_token,
        );
      }

      SLog.setUser(user);
      return true;
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.error || "OAuth callback failed",
      });
      return false;
    }
  },

  handleOAuthMessage: async (event) => {
    const { checkAuth } = useAuthStore.getState();

    // Relaxed origin check for development to handle port changes (5173 vs 5174 etc)
    if (event.origin !== window.location.origin) {
      console.warn(
        "Login: Received message from different origin:",
        event.origin,
        "Expected:",
        window.location.origin,
      );
      // In production, you might want to force strict equality or a whitelist
      const authorizedOrigin = new URL(
        import.meta.env.VITE_API_URL,
        window.location.origin,
      ).origin;
      if (
        event.origin !== authorizedOrigin &&
        event.origin !== window.location.origin
      ) {
        return;
      }
    }

    const { type, provider, error } = event.data;
    if (type === "oauth-success") {
      await checkAuth(true);
    } else if (type === "oauth-error") {
      console.error(`OAuth error from ${provider}:`, error);
      if (error === "User account is disabled.") {
        notify.error("Your account has been blocked by an administrator.", {
          duration: 5000,
        });
      } else {
        notify.error(`Login failed: ${error}`);
      }
    }
  },

  requestOtp: async (email) => {
    const state = get();
    const now = Date.now();

    if (state.isOtpLoading) return false;

    if (
      state.lastOtpEmail === email &&
      state.otpCooldownUntil &&
      now < state.otpCooldownUntil
    ) {
      const seconds = Math.ceil((state.otpCooldownUntil - now) / 1000);
      set({
        error: `Please wait ${seconds}s before requesting another code.`,
      });
      return false;
    }

    set({ isOtpLoading: true, error: null });
    try {
      await authAPI.requestOtp(email);

      set({
        isOtpLoading: false,
        otpCooldownUntil: Date.now() + 60000,
        lastOtpEmail: email,
      });

      return true;
    } catch (error) {
      const retryAfter = Number(error.response?.headers?.["retry-after"]);
      const cooldownMs =
        Number.isFinite(retryAfter) && retryAfter > 0
          ? retryAfter * 1000
          : 60000;
      set({
        isOtpLoading: false,
        error: error.response?.data?.error || "Failed to send OTP",
        otpCooldownUntil: Date.now() + cooldownMs,
        lastOtpEmail: email,
      });
      return false;
    }
  },

  verifyOtp: async (email, otp) => {
    set({ isOtpLoading: true, error: null });
    try {
      const response = await authAPI.verifyOtp(email, otp);
      const { user } = response.data;

      set({
        user,
        isAuthenticated: true,
        isInitialized: true,
        loading: false,
        lastAuthCheck: Date.now(),
        isOtpLoading: false,
        error: null,
      });

      // Save tokens to localStorage for WebSocket services if present
      if (response.data.access_token) {
        localStorage.setItem(
          "clashcode_access_token",
          response.data.access_token,
        );
      }
      if (response.data.refresh_token) {
        localStorage.setItem(
          "clashcode_refresh_token",
          response.data.refresh_token,
        );
      }

      SLog.setUser(user);
      return true;
    } catch (error) {
      set({
        isOtpLoading: false,
        error: error.response?.data?.error || "Invalid OTP",
      });
      return false;
    }
  },

  logout: async () => {
    try {
      await authAPI.logout();
    } catch {
      // Continue with logout even if API fails
    }

    // Clear tokens from localStorage
    localStorage.removeItem("clashcode_access_token");
    localStorage.removeItem("clashcode_refresh_token");

    // Clear caches
    useChallengesStore.getState().clearCache();
    useNotificationStore.getState().clearCache();

    set({
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,
      email: "",
      otp: "",
      showOtpInput: false,
      isOAuthLoading: false,
      oauthCooldownUntil: 0,
      otpCooldownUntil: 0,
      lastOtpEmail: "",
      lastAuthCheck: null,
      authCheckPromise: null,
    });
    SLog.setUser(null);
  },

  deleteAccount: async () => {
    try {
      await authAPI.deleteAccount();

      // Clear challenges cache
      useChallengesStore.getState().clearCache();

      set({
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        email: "",
        otp: "",
        showOtpInput: false,
        isOAuthLoading: false,
        oauthCooldownUntil: 0,
        otpCooldownUntil: 0,
        lastOtpEmail: "",
        lastAuthCheck: null,
        authCheckPromise: null,
      });

      return true;
    } catch (error) {
      console.error("Delete account failed:", error);
      throw error;
    }
  },
}));

export default useAuthStore;
