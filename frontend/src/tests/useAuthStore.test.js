import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import useAuthStore from "../../stores/useAuthStore";

// Mock dependencies
vi.mock("../../services/api", () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
    requestOtp: vi.fn(),
    verifyOtp: vi.fn(),
  },
}));

vi.mock("../../stores/useChallengesStore", () => ({
  default: { getState: () => ({ clearCache: vi.fn() }) },
}));

vi.mock("../../stores/useNotificationStore", () => ({
  default: { getState: () => ({ clearCache: vi.fn() }) },
}));

vi.mock("../../services/notification", () => ({
  notify: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("../../utils/isBoneyard", () => ({
  isBoneyard: () => false,
}));

vi.mock("../../services/logger", () => ({
  SLog: { setUser: vi.fn(), init: vi.fn() },
}));

describe("useAuthStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      loading: true,
      isInitialized: false,
      error: null,
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
    });
  });

  it("initializes with correct default state", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.loading).toBe(true);
    expect(state.isInitialized).toBe(false);
  });

  it("sets email correctly", () => {
    act(() => {
      useAuthStore.getState().setEmail("test@example.com");
    });
    expect(useAuthStore.getState().email).toBe("test@example.com");
  });

  it("clears error", () => {
    useAuthStore.setState({ error: "some error" });
    act(() => {
      useAuthStore.getState().clearError();
    });
    expect(useAuthStore.getState().error).toBeNull();
  });

  it("checkAuth sets user when API succeeds", async () => {
    const { authAPI } = await import("../../services/api");
    const mockUser = { id: 1, username: "testuser", email: "test@test.com" };
    authAPI.getCurrentUser.mockResolvedValueOnce({ data: mockUser });

    await act(async () => {
      await useAuthStore.getState().checkAuth(true);
    });

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isInitialized).toBe(true);
    expect(state.loading).toBe(false);
  });

  it("checkAuth clears user when API fails", async () => {
    const { authAPI } = await import("../../services/api");
    authAPI.getCurrentUser.mockRejectedValueOnce(new Error("Unauthorized"));

    await act(async () => {
      await useAuthStore.getState().checkAuth(true);
    });

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isInitialized).toBe(true);
  });

  it("logout clears all state", async () => {
    const { authAPI } = await import("../../services/api");
    authAPI.logout.mockResolvedValueOnce({});

    useAuthStore.setState({
      user: { id: 1, username: "test" },
      isAuthenticated: true,
      email: "test@test.com",
    });

    await act(async () => {
      await useAuthStore.getState().logout();
    });

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.email).toBe("");
  });

  it("deduplicates concurrent checkAuth calls", async () => {
    const { authAPI } = await import("../../services/api");
    const mockUser = { id: 1, username: "testuser" };
    authAPI.getCurrentUser.mockResolvedValue({ data: mockUser });

    let results;
    await act(async () => {
      results = await Promise.all([
        useAuthStore.getState().checkAuth(true),
        useAuthStore.getState().checkAuth(true),
        useAuthStore.getState().checkAuth(true),
      ]);
    });

    // Should have only made one API call despite 3 concurrent calls
    expect(authAPI.getCurrentUser).toHaveBeenCalledTimes(1);
    expect(results[0]).toEqual(mockUser);
    expect(results[1]).toEqual(mockUser);
    expect(results[2]).toEqual(mockUser);
  });

  it("respects OTP cooldown", async () => {
    useAuthStore.setState({
      otpCooldownUntil: Date.now() + 30000,
      lastOtpEmail: "test@test.com",
    });

    let result;
    await act(async () => {
      result = await useAuthStore.getState().requestOtp("test@test.com");
    });

    expect(result).toBe(false);
    expect(useAuthStore.getState().error).toContain("Please wait");
  });
});
