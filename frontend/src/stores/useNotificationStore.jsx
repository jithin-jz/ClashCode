import { create } from "zustand";
import { notificationsAPI } from "../services/api";
import { notify } from "../services/notification";
import { isBoneyard } from "../utils/isBoneyard";
import { playNotificationSound } from "../utils/playNotificationSound";

/**
 * Centralized notification management.
 * Shared between NotificationDrawer and NotificationDropdown
 * for consistent state and unread count.
 */
const useNotificationStore = create((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,
  totalCount: 0,
  currentPage: 1,
  pageSize: 50,
  totalPages: 1,
  hasMore: false,
  isLoading: false,
  isLoadingMore: false,
  error: null,
  lastFetched: null,
  fcmToken: null,
  permission:
    typeof Notification !== "undefined" ? Notification.permission : "default",
  _recentToastMap: new Map(),
  socket: null,
  isWSConnected: false,
  wsShouldReconnect: false,
  _realtimeSyncTimer: null,
  _fetchPromise: null,
  _deniedWarned: false,
  _promptShown: false,
  _listenerSetup: false,
  CACHE_DURATION: 2 * 60 * 1000,


  /**
   * Helper to show de-duplicated toast.
   */
  _showToast: (title, body) => {
    if (!title && !body) return;
    const key = `${title}:${body}`;
    const now = Date.now();

    // We use a Map to track the last show time for each unique notification content.
    // This catches simultaneous fire from WS and FCM in the foreground.
    const recent = get()._recentToastMap || new Map();
    const lastTime = recent.get(key);

    // If shown in the last 3 seconds, ignore.
    if (lastTime && now - lastTime < 3000) {
      return;
    }

    recent.set(key, now);
    set({ _recentToastMap: recent });

    // Auto-cleanup stale entries from the map every now and then
    if (recent.size > 50) {
      for (const [k, time] of recent.entries()) {
        if (now - time > 10000) recent.delete(k);
      }
    }

    playNotificationSound();

    notify.info(title || "New Notification", {
      description: body,
      duration: 5000,
      icon: (
        <img src="/favicon.png" className="w-5 h-5 rounded-md" alt="logo" />
      ),
    });
    get().scheduleRealtimeSync();
  },

  /**
   * Debounced forced-sync for realtime events.
   */
  scheduleRealtimeSync: (delayMs = 300) => {
    const existing = get()._realtimeSyncTimer;
    if (existing) clearTimeout(existing);

    const timerId = setTimeout(() => {
      set({ _realtimeSyncTimer: null });
      get().fetchNotifications(true);
    }, delayMs);

    set({ _realtimeSyncTimer: timerId });
  },

  /**
   * Fetch all notifications with caching.
   */
  fetchNotifications: async (force = false, options = {}) => {
    const state = get();
    const now = Date.now();
    if (isBoneyard()) return [];

    const page = Math.max(options.page || 1, 1);
    const append = Boolean(options.append && page > 1);
    const pageSize = Math.max(options.pageSize || state.pageSize || 50, 1);

    // De-duplicate concurrent calls from multiple mounted components
    if (state._fetchPromise) {
      return state._fetchPromise;
    }

    // Use cache if valid
    if (
      !force &&
      page === 1 &&
      state.lastFetched &&
      now - state.lastFetched < state.CACHE_DURATION &&
      state.notifications.length > 0
    ) {
      return state.notifications;
    }

    const fetchPromise = (async () => {
      set({
        isLoading: !append,
        isLoadingMore: append,
        error: null,
      });

      try {
        const response = await notificationsAPI.getNotifications({
          page,
          page_size: pageSize,
        });
        const payload = Array.isArray(response.data)
          ? {
              count: response.data.length,
              unread_count: response.data.filter((n) => !n.is_read).length,
              page,
              page_size: pageSize,
              total_pages: 1,
              results: response.data,
            }
          : (response.data ?? {});
        const fetchedNotifications = Array.isArray(payload.results)
          ? payload.results
          : [];
        const notifications = append
          ? [
              ...state.notifications,
              ...fetchedNotifications.filter(
                (nextItem) =>
                  !state.notifications.some(
                    (existing) => existing.id === nextItem.id,
                  ),
              ),
            ]
          : fetchedNotifications;
        const unreadCount =
          typeof payload.unread_count === "number"
            ? payload.unread_count
            : notifications.filter((n) => !n.is_read).length;
        const totalPages = Math.max(
          payload.total_pages ||
            Math.ceil((payload.count || 0) / pageSize) ||
            1,
          1,
        );

        set({
          notifications,
          unreadCount,
          totalCount: payload.count ?? notifications.length,
          currentPage: payload.page || page,
          pageSize: payload.page_size || pageSize,
          totalPages,
          hasMore: (payload.page || page) < totalPages,
          isLoading: false,
          isLoadingMore: false,
          lastFetched: Date.now(),
          error: null,
        });

        return notifications;
      } catch (error) {
        console.error("Failed to fetch notifications:", error);
        set({
          isLoading: false,
          isLoadingMore: false,
          error: error.response?.data?.error || "Failed to load notifications",
        });
        return [];
      } finally {
        set({ _fetchPromise: null });
      }
    })();

    set({ _fetchPromise: fetchPromise });
    return fetchPromise;
  },

  loadMoreNotifications: async () => {
    const state = get();
    if (state.isLoading || state.isLoadingMore || !state.hasMore) {
      return state.notifications;
    }

    return get().fetchNotifications(true, {
      page: state.currentPage + 1,
      pageSize: state.pageSize,
      append: true,
    });
  },

  /**
   * Mark a notification as read.
   */
  markAsRead: async (notificationId) => {
    try {
      await notificationsAPI.markRead(notificationId);

      // Update local state
      set((state) => {
        const target = state.notifications.find((n) => n.id === notificationId);
        const updatedNotifications = state.notifications.map((n) =>
          n.id === notificationId ? { ...n, is_read: true } : n,
        );

        return {
          notifications: updatedNotifications,
          unreadCount:
            target && !target.is_read
              ? Math.max(state.unreadCount - 1, 0)
              : state.unreadCount,
        };
      });

      return { success: true };
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Mark all notifications as read.
   */
  markAllAsRead: async () => {
    try {
      await notificationsAPI.markAllRead();

      // Update local state
      set((state) => ({
        notifications: state.notifications.map((n) => ({
          ...n,
          is_read: true,
        })),
        unreadCount: 0,
      }));

      return { success: true };
    } catch (error) {
      console.error("Failed to mark all as read:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Clear all notifications.
   */
  clearAll: async () => {
    try {
      await notificationsAPI.clearAll();

      set({
        notifications: [],
        unreadCount: 0,
        totalCount: 0,
        currentPage: 1,
        totalPages: 1,
        hasMore: false,
      });

      return { success: true };
    } catch (error) {
      console.error("Failed to clear notifications:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Add a new notification (for real-time updates).
   */
  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
      totalCount: state.totalCount + 1,
    }));
  },

  /**
   * Clear error state.
   */
  clearError: () => set({ error: null }),

  /**
   * Clear cache and reset state.
   */
  clearCache: () => {
    const { socket, _realtimeSyncTimer } = get();
    if (socket) socket.close();
    if (_realtimeSyncTimer) clearTimeout(_realtimeSyncTimer);

    set({
      notifications: [],
      unreadCount: 0,
      totalCount: 0,
      currentPage: 1,
      pageSize: 50,
      totalPages: 1,
      hasMore: false,
      lastFetched: null,
      error: null,
      fcmToken: null,
      _deniedWarned: false,
      _promptShown: false,
      _fetchPromise: null,
      _realtimeSyncTimer: null,
      socket: null,
      isWSConnected: false,
      wsShouldReconnect: false,
      isLoadingMore: false,
    });
  },
}));

export default useNotificationStore;
