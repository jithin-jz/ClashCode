import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { buildWebSocketUrl } from "../utils/websocketUrl";

vi.mock("../services/api", () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
    verifyOtp: vi.fn(),
  },
}));
vi.mock("../stores/useChallengesStore", () => ({
  default: { getState: () => ({ clearCache: vi.fn() }) },
}));
vi.mock("../stores/useNotificationStore", () => ({
  default: { getState: () => ({ clearCache: vi.fn() }) },
}));
vi.mock("../services/notification", () => ({
  notify: { error: vi.fn(), success: vi.fn() },
}));
vi.mock("../utils/isBoneyard", () => ({ isBoneyard: () => false }));
vi.mock("../services/logger", () => ({
  SLog: { setUser: vi.fn(), init: vi.fn() },
}));

const LEGACY_KEYS = ["clashcode_access_token", "clashcode_refresh_token"];

describe("token handling", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("never puts a token in WebSocket URLs", () => {
    const url = buildWebSocketUrl({
      apiUrl: "https://api.example.com/api",
      defaultPath: "/ws/tasks/",
      token: "should-be-ignored",
    });
    expect(url).toBe("wss://api.example.com/ws/tasks/");
    expect(url).not.toContain("token");
  });

  it("keeps relative API URLs on the current host", () => {
    const url = buildWebSocketUrl({ apiUrl: "/api", defaultPath: "/ws/chat/global" });
    expect(url).toBe(`ws://${window.location.host}/ws/chat/global`);
  });

  it("purges tokens left in localStorage by older builds", async () => {
    LEGACY_KEYS.forEach((key) => localStorage.setItem(key, "old-jwt"));
    const { purgeLegacyTokens } = await import("../stores/useAuthStore");
    purgeLegacyTokens();
    LEGACY_KEYS.forEach((key) => expect(localStorage.getItem(key)).toBeNull());
  });

  it("does not store tokens even if the API returns them in the body", async () => {
    const { authAPI } = await import("../services/api");
    const { default: useAuthStore } = await import("../stores/useAuthStore");
    authAPI.getCurrentUser.mockResolvedValueOnce({
      data: { id: 1, username: "u", access_token: "a.b.c", refresh_token: "d.e.f" },
    });

    await act(async () => {
      await useAuthStore.getState().checkAuth(true);
    });

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    LEGACY_KEYS.forEach((key) => expect(localStorage.getItem(key)).toBeNull());
  });

  it("logout clears legacy tokens", async () => {
    const { authAPI } = await import("../services/api");
    const { default: useAuthStore } = await import("../stores/useAuthStore");
    authAPI.logout.mockResolvedValueOnce({});
    LEGACY_KEYS.forEach((key) => localStorage.setItem(key, "old-jwt"));

    await act(async () => {
      await useAuthStore.getState().logout();
    });

    LEGACY_KEYS.forEach((key) => expect(localStorage.getItem(key)).toBeNull());
  });
});
