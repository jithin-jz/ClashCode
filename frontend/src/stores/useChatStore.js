import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { buildWebSocketUrl } from "../utils/websocketUrl";
import { isBoneyard } from "../utils/isBoneyard";

const useChatStore = create(
  persist(
    (set, get) => ({
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
            // If already connected to the same room, do nothing
            if (state.currentRoom === roomName) return;
          }
          state.socket.close();
        }

        // Only clear messages if room changes
        const roomChanged = state.currentRoom !== roomName;

        set({
          shouldReconnect: true,
          currentRoom: roomName,
          isConnected: false,
          ...(roomChanged && {
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

          // Auto-load ALL history after connection if we don't have enough
          if (get().messages.length < 50 || roomChanged) {
            setTimeout(() => {
              get().autoLoadAllHistory();
            }, 500);
          }
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
                  msg.timestamp === data.timestamp || msg.timestamp === data.original_timestamp
                    ? { ...msg, message: data.message, timestamp: data.timestamp }
                    : msg,
                ),
              }));
            } else if (data.type === "chat_delete") {
              set((state) => ({
                messages: state.messages.filter(
                  (msg) => msg.timestamp !== data.timestamp && msg.timestamp !== data.original_timestamp,
                ),
              }));
            } else if (data.type === "chat_react") {
              set((state) => ({
                messages: state.messages.map((msg) => {
                  if (msg.timestamp !== data.timestamp && msg.timestamp !== data.original_timestamp) return msg;
                  // Use server-provided reactions as the source of truth
                  return { ...msg, reactions: data.reactions || {}, timestamp: data.timestamp };
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
                messages: state.messages.map((msg) =>
                  msg.timestamp === data.timestamp || msg.timestamp === data.original_timestamp
                    ? { ...msg, read_by: [...new Set([...(msg.read_by || []), data.username])] }
                    : msg
                )
              }));
            }
            } else if (data.type === "history") {

              set((state) => {
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
              console.warn("[Chat] Server error:", data.message, data.action || "");
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

      disconnect: () => {
        const { socket } = get();
        if (socket) {
          socket.close();
          set({
            socket: null,
            isConnected: false,
            // Do NOT clear messages on disconnect to preserve state for UI
            shouldReconnect: false,
            typingUsers: [],
            pinnedMessage: null,
          });
        }
      },

      _send: (payload) => {
        const { socket, isConnected, currentRoom } = get();
        if (socket && isConnected && socket.readyState === WebSocket.OPEN) {
          const msg = JSON.stringify({ ...payload, room: currentRoom });
          socket.send(msg);
        } else {
          console.warn(
            "[Chat] Message dropped — socket not ready:",
            { connected: isConnected, readyState: socket?.readyState, action: payload.action }
          );
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
          const url = `/chat/history/${currentRoom}?limit=100&last_timestamp=${lastTimestamp}`;
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

      autoLoadAllHistory: async () => {
        const currentRoom = get().currentRoom;
        if (!currentRoom) return;

        try {
          const { default: api } = await import("../services/api");
          let allMessages = [];
          let lastTimestamp = null;
          let hasMore = true;
          let pageCount = 0;
          const maxPages = 50; 

          while (hasMore && pageCount < maxPages) {
            const url = lastTimestamp
              ? `/chat/history/${currentRoom}?limit=100&last_timestamp=${lastTimestamp}`
              : `/chat/history/${currentRoom}?limit=100`;

            const response = await api.get(url);
            const data = response.data;

            if (!data.messages || data.messages.length === 0) {
              hasMore = false;
              break;
            }

            allMessages = [...data.messages, ...allMessages];
            lastTimestamp = data.last_timestamp;
            hasMore = data.has_more;
            pageCount++;

            if (pageCount % 5 === 0) {
              await new Promise((resolve) => setTimeout(resolve, 50));
            }
          }

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

        const filtered = messages.filter((msg) => {
          const messageText = msg.message?.toLowerCase() || "";
          const username = msg.username?.toLowerCase() || "";
          return messageText.includes(searchTerm) || username.includes(searchTerm);
        });

        set({ searchResults: filtered, isSearching: false });
      },

      clearSearch: () => set({ searchResults: [], isSearching: false }),
    }),
    {
      name: "clashcode-chat-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        messages: state.messages.slice(-500), // Keep only last 500 messages in localStorage
        currentRoom: state.currentRoom,
      }),
    },
  ),
);

export default useChatStore;
