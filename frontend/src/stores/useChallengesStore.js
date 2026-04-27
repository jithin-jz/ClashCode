import { create } from "zustand";
import { challengesApi } from "../services/challengesApi";
import { isBoneyard } from "../utils/isBoneyard";

/**
 * Centralized store for challenge data management.
 * Provides caching, loading states, and reduces duplicate API calls.
 */
const useChallengesStore = create((set, get) => ({
  // State
  challenges: [],
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastFetched: null,
  _fetchPromise: null,

  // Cache duration (5 minutes)
  CACHE_DURATION: 5 * 60 * 1000,

  /**
   * Fetch all challenges with smart caching.
   * Only refetches if cache is stale or force=true.
   */
  fetchChallenges: async (force = false) => {
    const state = get();
    const now = Date.now();
    const hasCachedData = state.challenges.length > 0;
    const isCacheFresh =
      state.lastFetched && now - state.lastFetched < state.CACHE_DURATION;

    // De-duplicate concurrent calls from multiple mounted components.
    if (state._fetchPromise) {
      return state._fetchPromise;
    }

    // Serve cache instantly when fresh.
    if (!force && hasCachedData && isCacheFresh) {
      return state.challenges;
    }

    if (isBoneyard()) return [];

    set({
      isLoading: !hasCachedData,
      isRefreshing: hasCachedData,
      error: null,
    });

    const fetchPromise = (async () => {
      try {
        const data = await challengesApi.getAll();
        set({
          challenges: data,
          isLoading: false,
          isRefreshing: false,
          lastFetched: Date.now(),
          error: null,
        });
        return data;
      } catch (error) {
        console.error("Failed to fetch challenges:", error);
        set({
          isLoading: false,
          isRefreshing: false,
          error: error.message || "Failed to fetch challenges",
        });
        return get().challenges;
      } finally {
        set({ _fetchPromise: null });
      }
    })();

    set({ _fetchPromise: fetchPromise });
    return fetchPromise;
  },

  /**
   * Fetch only when cache is older than maxAgeMs.
   * Useful for periodic/focus-based real-time refresh without request spam.
   */
  ensureFreshChallenges: async (maxAgeMs = 30000) => {
    const state = get();
    const isStale =
      !state.lastFetched || Date.now() - state.lastFetched > maxAgeMs;
    if (!isStale && state.challenges.length > 0) {
      return state.challenges;
    }
    return get().fetchChallenges(true);
  },

  /**
   * Merge a challenge detail payload into cache.
   * Keeps cache in sync when level detail is opened.
   */
  upsertChallenge: (challenge) => {
    if (!challenge?.slug) return;
    set((state) => {
      const idx = state.challenges.findIndex((c) => c.slug === challenge.slug);
      if (idx === -1) {
        const merged = [...state.challenges, challenge].sort(
          (a, b) => (a.order ?? 9999) - (b.order ?? 9999),
        );
        return { challenges: merged };
      }
      const next = [...state.challenges];
      next[idx] = { ...next[idx], ...challenge };
      return { challenges: next };
    });
  },

  /**
   * Optimistically apply completion progress to keep UI instant.
   */
  applySubmissionResult: (slug, result) => {
    if (!slug || !result) return;
    set((state) => {
      const idx = state.challenges.findIndex((c) => c.slug === slug);
      if (idx === -1) return state;

      const next = [...state.challenges];
      const current = next[idx];
      next[idx] = {
        ...current,
        status: "COMPLETED",
        stars: Math.max(current.stars || 0, result.stars || 0),
      };

      // Unlock next challenge immediately if backend returned it.
      if (result.next_level_slug) {
        const nextIdx = next.findIndex(
          (c) => c.slug === result.next_level_slug,
        );
        if (nextIdx !== -1 && next[nextIdx].status === "LOCKED") {
          next[nextIdx] = { ...next[nextIdx], status: "UNLOCKED" };
        }
      }

      return { challenges: next };
    });
  },

  /**
   * Optimistically sync AI hint purchase count for a challenge.
   */
  setChallengeHintsPurchased: (slug, hintsPurchased) => {
    if (!slug || typeof hintsPurchased !== "number") return;
    set((state) => ({
      challenges: state.challenges.map((challenge) =>
        challenge.slug === slug
          ? { ...challenge, ai_hints_purchased: hintsPurchased }
          : challenge,
      ),
    }));
  },

  /**
   * Clear all cached data.
   */
  clearCache: () => {
    set({
      challenges: [],
      lastFetched: null,
      error: null,
      isRefreshing: false,
      _fetchPromise: null,
    });
  },
}));

export default useChallengesStore;
