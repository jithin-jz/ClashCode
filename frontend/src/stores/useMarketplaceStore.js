import { create } from "zustand";
import { storeAPI } from "../services/api";

const CACHE_DURATION_MS = 5 * 60 * 1000;

const useMarketplaceStore = create((set, get) => ({
  items: [],
  isLoading: false,
  isMutating: false,
  activeMutationItemId: null,
  error: null,
  lastFetchedAt: null,

  fetchItems: async (force = false) => {
    const { items, lastFetchedAt } = get();
    const now = Date.now();

    if (
      !force &&
      items.length > 0 &&
      lastFetchedAt &&
      now - lastFetchedAt < CACHE_DURATION_MS
    ) {
      return items;
    }

    set({ isLoading: true, error: null });
    try {
      const response = await storeAPI.getItems();
      const nextItems = Array.isArray(response.data) ? response.data : [];
      set({
        items: nextItems,
        isLoading: false,
        lastFetchedAt: now,
        error: null,
      });
      return nextItems;
    } catch (error) {
      set({
        isLoading: false,
        error: error.response?.data?.error || "Failed to load store items.",
      });
      return [];
    }
  },

  purchaseItem: async (itemId) => {
    set({ isMutating: true, activeMutationItemId: itemId, error: null });
    try {
      const response = await storeAPI.purchaseItem(itemId);
      set((state) => ({
        items: state.items.map((item) =>
          item.id === itemId ? { ...item, is_owned: true } : item,
        ),
        isMutating: false,
        activeMutationItemId: null,
      }));
      return { success: true, data: response.data };
    } catch (error) {
      const message = error.response?.data?.error || "Purchase failed.";
      set({ isMutating: false, activeMutationItemId: null, error: message });
      return { success: false, error: message };
    }
  },

  equipItem: async (itemId) => {
    set({ isMutating: true, activeMutationItemId: itemId, error: null });
    try {
      const response = await storeAPI.equipItem(itemId);
      set({ isMutating: false, activeMutationItemId: null });
      return { success: true, data: response.data };
    } catch (error) {
      const message = error.response?.data?.error || "Failed to equip.";
      set({ isMutating: false, activeMutationItemId: null, error: message });
      return { success: false, error: message };
    }
  },

  unequipCategory: async (category) => {
    set({ isMutating: true, activeMutationItemId: null, error: null });
    try {
      const response = await storeAPI.unequipItem(category);
      set({ isMutating: false, activeMutationItemId: null });
      return { success: true, data: response.data };
    } catch (error) {
      const message = error.response?.data?.error || "Failed to unequip.";
      set({ isMutating: false, activeMutationItemId: null, error: message });
      return { success: false, error: message };
    }
  },

  clearStoreState: () =>
    set({
      items: [],
      isLoading: false,
      isMutating: false,
      activeMutationItemId: null,
      error: null,
      lastFetchedAt: null,
    }),
}));

export default useMarketplaceStore;
