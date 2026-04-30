import { create } from "zustand";
import { buildWebSocketUrl } from "../utils/websocketUrl";
import { isBoneyard } from "../utils/isBoneyard";

const useChatStore = create((set, get) => ({
  // State
  socket: null,
  isConnected: false,
  messages: [],
  onlineCount: 0,
  error: null,
  shouldReconnect: false,
  typingUsers: [], // [{username, timeout}]
  pinnedMessage: null, // {timestamp, message, pinned_by}
  currentRoom: "global",
  isChatOpen: false,
  lastTimestamp: null,
  hasMore: false,
  isLoadingMore: false,
  searchResults: [],
  isSearching: false,

  // Actions
  connect: async (roomName = "global") => {
    set({ shouldReconnect: true, currentRoom: roomName });

    if (isBoneyard()) return;

    // Prevent multiple connections to the SAME room
    const state = get();
    if (state.socket) {
      if (
        state.socket.readyState === WebSocket.OPEN ||
        state.socket.readyState === WebSocket.CONNECTING
      ) {
        return;
      }
      state.socket.close();
    }

    // Only clear messages on first connection, not on reconnects
    const isFirstConnection =
      !state.lastTimestamp && state.messages.length === 0;

    set({
      shouldReconnect: true,
      currentRoom: roomName,
      isConnected: false,
      ...(isFirstConnection && {
        messages: [],
        lastTimestamp: null,
        hasMore: true,
      }),
    });

    const wsUrl = buildWebSocketUrl({
      explicitUrl: import.meta.env.VITE_WS_URL || import.meta.env.VITE_CHAT_URL,
      apiUrl: import.meta.env.VITE_API_URL,
      defaultPath: `/ws/chat/${roomName}`,
      legacyPaths: ["/chat", "/ws", "/ws/chat"],
      label: "Chat",
      token: localStorage.getItem("clashcode_access_token"),
    });

    const socket = new WebSocket(wsUrl);

    socket.onopen = async () => {
      set({ isConnected: true, error: null });

      // Auto-load ALL history after connection
      // This will load older messages beyond the initial 50
      setTimeout(() => {
        get().autoLoadAllHistory();
      }, 500);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "chat_message") {
          set((state) => {
            const isDuplicate = state.messages.some((msg) => {
              if (data.id && msg.id === data.id) return true;
              const msgTime = new Date(msg.timestamp).getTime();
              const dataTime = new Date(data.timestamp).getTime();
              const isTimeClose = Math.abs(msgTime - dataTime) < 1000;
              return (
                msg.message === data.message &&
                msg.user_id === data.user_id &&
                isTimeClose
              );
            });
            if (isDuplicate) return state;
            return { messages: [...state.messages, data] };
          });
        } else if (data.type === "chat_edit") {
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.timestamp === data.timestamp
                ? { ...msg, message: data.message }
                : msg,
            ),
          }));
        } else if (data.type === "chat_delete") {
          set((state) => ({
            messages: state.messages.filter(
              (msg) => msg.timestamp !== data.timestamp,
            ),
          }));
        } else if (data.type === "chat_react") {
          set((state) => ({
            messages: state.messages.map((msg) => {
              if (msg.timestamp !== data.timestamp) return msg;
              const reactions = { ...(msg.reactions || {}) };
              const currentUsers = reactions[data.emoji] || [];
              const isRemoving = currentUsers.includes(data.username);

              if (isRemoving) {
                // Just remove the user from this specific emoji
                const filtered = currentUsers.filter((u) => u !== data.username);
                if (filtered.length === 0) {
                  delete reactions[data.emoji];
                } else {
                  reactions[data.emoji] = filtered;
                }
              } else {
                // Adding a new reaction: Remove user from ALL other emojis first (mutually exclusive)
                Object.keys(reactions).forEach((emoji) => {
                  reactions[emoji] = reactions[emoji].filter(
                    (u) => u !== data.username,
                  );
                  if (reactions[emoji].length === 0) delete reactions[emoji];
                });
                // Add to the new emoji
                reactions[data.emoji] = [
                  ...(reactions[data.emoji] || []),
                  data.username,
                ];
              }
              return { ...msg, reactions };
            }),
          }));
        } else if (data.type === "typing") {
          set((state) => {
            const filtered = state.typingUsers.filter(
              (t) => t.username !== data.username,
            );
            const timeout = setTimeout(() => {
              set((s) => ({
                typingUsers: s.typingUsers.filter(
                  (t) => t.username !== data.username,
                ),
              }));
            }, 3000);
            return {
              typingUsers: [...filtered, { username: data.username, timeout }],
            };
          });
        } else if (data.type === "chat_pin") {
          set({
            pinnedMessage: {
              timestamp: data.timestamp,
              message: data.message,
              pinned_by: data.pinned_by,
            },
          });
        } else if (data.type === "chat_unpin") {
          set({ pinnedMessage: null });
        } else if (data.type === "chat_read") {
          set((state) => ({
            messages: state.messages.map((msg) => {
              if (msg.timestamp !== data.timestamp) return msg;
              const readBy = new Set(msg.read_by || []);
              readBy.add(data.username);
              return { ...msg, read_by: Array.from(readBy) };
            }),
          }));
        } else if (data.type === "history") {
          // Don't replace messages - prepend history to existing messages
          // This preserves messages from previous connections
          set((state) => {
            // Filter out duplicates from history
            const existingTimestamps = new Set(
              state.messages.map((msg) => msg.timestamp),
            );
            const newMessages = data.messages.filter(
              (msg) => !existingTimestamps.has(msg.timestamp),
            );

            return {
              messages: [...newMessages, ...state.messages],
              lastTimestamp: data.last_timestamp,
              hasMore: data.last_timestamp !== null,
            };
          });
        } else if (data.type === "presence") {
          set({ onlineCount: data.count });
        } else if (data.type === "error") {
          set({ error: data.message });
          setTimeout(() => set({ error: null }), 3000);
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };

    socket.onclose = () => {
      set({ isConnected: false, socket: null });
      if (get().shouldReconnect) {
        setTimeout(() => get().connect(get().currentRoom), 5000);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      set({ isConnected: false, error: "Connection error" });
    };

    set({ socket });
  },

  setChatOpen: (val) =>
    set((state) => ({
      isChatOpen: typeof val === "function" ? val(state.isChatOpen) : val,
    })),

  // REMOVED: startDM

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({
        socket: null,
        isConnected: false,
        messages: [],
        shouldReconnect: false,
        typingUsers: [],
        pinnedMessage: null,
        currentRoom: "global",
      });
    }
  },

  _send: (payload) => {
    const { socket, isConnected } = get();
    if (socket && isConnected && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  },

  sendMessage: (content) => {
    get()._send({ action: "send", message: content });
  },

  editMessage: (timestamp, newContent) => {
    get()._send({
      action: "edit",
      target_timestamp: timestamp,
      message: newContent,
    });
  },

  deleteMessage: (timestamp) => {
    get()._send({
      action: "delete",
      target_timestamp: timestamp,
      message: "deleted",
    });
  },

  sendTyping: () => {
    get()._send({ action: "typing" });
  },

  toggleReaction: (timestamp, emoji) => {
    get()._send({ action: "react", target_timestamp: timestamp, emoji });
  },

  pinMessage: (timestamp, message) => {
    get()._send({ action: "pin", target_timestamp: timestamp, message });
  },

  unpinMessage: (timestamp) => {
    get()._send({ action: "unpin", target_timestamp: timestamp });
  },

  clearMessages: () =>
    set({ messages: [], lastTimestamp: null, hasMore: true }),

  loadMore: async () => {
    const { currentRoom, lastTimestamp, hasMore, isLoadingMore, messages } =
      get();
    if (!hasMore || isLoadingMore || !lastTimestamp) return;

    set({ isLoadingMore: true });
    try {
      const { default: api } = await import("../services/api");
      const url = `/chat/history/${currentRoom}?limit=50&last_timestamp=${lastTimestamp}`;
      const response = await api.get(url);
      const data = response.data;

      set({
        messages: [...data.messages, ...messages],
        lastTimestamp: data.last_timestamp,
        hasMore: data.has_more,
        isLoadingMore: false,
      });
    } catch (err) {
      console.error("Failed to load more messages", err);
      set({ isLoadingMore: false });
    }
  },

  // Auto-load ALL history from DynamoDB
  autoLoadAllHistory: async () => {
    const currentRoom = get().currentRoom;
    if (!currentRoom) return;

    try {
      const { default: api } = await import("../services/api");
      let allMessages = [];
      let lastTimestamp = null;
      let hasMore = true;
      let pageCount = 0;
      const maxPages = 50; // Load up to 2500 messages automatically

      while (hasMore && pageCount < maxPages) {
        const url = lastTimestamp
          ? `/chat/history/${currentRoom}?limit=50&last_timestamp=${lastTimestamp}`
          : `/chat/history/${currentRoom}?limit=50`;

        const response = await api.get(url);
        const data = response.data;

        if (!data.messages || data.messages.length === 0) {
          hasMore = false;
          break;
        }

        // Each batch is oldest-to-newest. Prepend batches to maintain order.
        allMessages = [...data.messages, ...allMessages];
        lastTimestamp = data.last_timestamp;
        hasMore = data.has_more;
        pageCount++;

        // Small delay to prevent blocking the UI thread too much
        if (pageCount % 5 === 0) {
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
      }

      // Merge with existing messages, avoiding duplicates
      if (allMessages.length > 0) {
        set((state) => {
          const existingTimestamps = new Set(
            state.messages.map((m) => m.timestamp),
          );
          const newMessages = allMessages.filter(
            (msg) => !existingTimestamps.has(msg.timestamp),
          );

          if (newMessages.length > 0) {
            return {
              messages: [...newMessages, ...state.messages],
              lastTimestamp: lastTimestamp || state.lastTimestamp,
              hasMore: hasMore,
            };
          }
          return state;
        });
      }
    } catch (err) {
      console.error("Failed to auto-load history:", err);
    }
  },

  sendImage: async (file) => {
    try {
      const { authAPI } = await import("../services/api");
      const response = await authAPI.uploadMedia(file);
      const url = response.data.url;
      const { user } = (await import("./useAuthStore")).default.getState();
      const messageContent = `IMAGE:${url}|${user?.username || "user"}`;
      get().sendMessage(messageContent);
    } catch (err) {
      console.error("Failed to upload image", err);
      set({ error: "Failed to upload image" });
      setTimeout(() => set({ error: null }), 3000);
    }
  },

  markAsRead: (timestamp) => {
    const socket = get().socket;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          action: "read",
          target_timestamp: timestamp,
        }),
      );
    }
  },

  searchMessages: (query) => {
    const { messages } = get();

    if (!query || !query.trim()) {
      set({ searchResults: [], isSearching: false });
      return;
    }

    const searchTerm = query.toLowerCase().trim();

    // Filter messages client-side
    const filtered = messages.filter((msg) => {
      const messageText = msg.message?.toLowerCase() || "";
      const username = msg.username?.toLowerCase() || "";
      return messageText.includes(searchTerm) || username.includes(searchTerm);
    });

    set({ searchResults: filtered, isSearching: false });
  },

  clearSearch: () => set({ searchResults: [], isSearching: false }),
}));

export default useChatStore;
