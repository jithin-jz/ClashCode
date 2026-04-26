import React, { useState, useEffect, useRef, memo, useCallback } from "react";
import { X, Pin, Map, Search } from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import useChatStore from "../../stores/useChatStore";
import ChatInput from "../components/ChatInput";
import MessageList from "../components/MessageList";

const ChatDrawer = ({ isOpen, setOpen, user }) => {
  const {
    messages,
    sendMessage,
    onlineCount,
    connect,
    editMessage,
    deleteMessage,
    sendTyping,
    toggleReaction,
    pinMessage,
    unpinMessage,
    typingUsers,
    pinnedMessage,
    currentRoom,
    loadMore,
    hasMore,
    isLoadingMore,
    markAsRead,
    searchMessages,
    clearSearch,
    searchResults,
    isSearching,
  } = useChatStore();

  const [showPicker, setShowPicker] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const searchTimeoutRef = useRef(null);

  const pickerRef = useRef(null);
  const emojiButtonRef = useRef(null);
  const inputRef = useRef(null);
  const drawerRef = useRef(null);

  // Close picker on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (
        showPicker &&
        pickerRef.current &&
        !pickerRef.current.contains(e.target) &&
        !emojiButtonRef.current.contains(e.target)
      ) {
        setShowPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showPicker]);

  // Cleanup search timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // Visual Viewport API for flexible mobile heights
  useEffect(() => {
    if (!window.visualViewport) return;

    const handleResize = () => {
      const vh = window.visualViewport.height;
      setViewportHeight(vh);
      const isVisible = vh < window.innerHeight * 0.85;
      setIsKeyboardVisible(isVisible);
    };

    window.visualViewport.addEventListener("resize", handleResize);
    window.visualViewport.addEventListener("scroll", handleResize);
    return () => {
      window.visualViewport.removeEventListener("resize", handleResize);
      window.visualViewport.removeEventListener("scroll", handleResize);
    };
  }, []);

  // Connect to websocket when drawer is open
  useEffect(() => {
    if (isOpen) {
      connect("global");
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus();
      }, 200);
    }
  }, [isOpen, connect]);

  const handleSendMessage = useCallback(
    (content) => {
      sendMessage(content);
      setShowPicker(false);
    },
    [sendMessage],
  );

  // Filter out own typing indicator
  const otherTyping = typingUsers.filter((t) => t.username !== user?.username);

  const isGlobal = currentRoom === "global";
  const chatPlaceholder = "Message global chat...";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <Motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {
              setOpen(false);
              setShowPicker(false);
            }}
            className="fixed inset-0 z-50 bg-black/20"
          />

          {/* Drawer */}
          <Motion.div
            ref={drawerRef}
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            style={{
              height: isKeyboardVisible ? `${viewportHeight}px` : "100dvh",
              bottom: 0,
            }}
            className="fixed left-0 z-[60] w-full md:max-w-[360px] bg-[#050505] shadow-2xl flex flex-col md:border-r border-white/5 overflow-hidden"
          >
            {/* Ambient Background Glow */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
              <div className="absolute top-[-10%] right-[-10%] w-[300px] h-[300px] bg-emerald-500/10 blur-[100px] rounded-full" />
              <div className="absolute bottom-[-5%] left-[-10%] w-[250px] h-[250px] bg-purple-500/10 blur-[80px] rounded-full" />
            </div>

            {/* Header */}
            <header className="shrink-0 h-16 flex items-center justify-between px-5 border-b border-white/5 bg-black/40 backdrop-blur-xl relative z-10">
              <div className="flex items-center gap-3.5">
                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-tr from-emerald-500 to-cyan-500 rounded-full blur opacity-25 group-hover:opacity-50 transition-all duration-500" />
                  <div className="relative h-9 w-9 rounded-full bg-black/60 border border-white/10 flex items-center justify-center text-emerald-400 shadow-inner overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 to-transparent" />
                    <Map
                      size={16}
                      className="relative z-10 drop-shadow-[0_0_8px_rgba(52,211,153,0.5)]"
                    />
                  </div>
                </div>

                <div className="flex flex-col">
                  <span className="text-[11px] font-black tracking-[0.25em] text-neutral-100 uppercase font-mono drop-shadow-sm">
                    Global Chat
                  </span>
                  <div className="flex items-center gap-1.5 leading-none mt-0.5">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                    </span>
                    <span className="text-[9px] font-black text-neutral-500 uppercase tracking-wider">
                      {onlineCount || 0} active in forge
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    setShowSearch(!showSearch);
                    if (showSearch) {
                      setSearchQuery("");
                      clearSearch();
                      if (searchTimeoutRef.current) {
                        clearTimeout(searchTimeoutRef.current);
                      }
                    }
                  }}
                  className={`h-8 w-8 rounded-xl flex items-center justify-center transition-all duration-300 ${showSearch ? "bg-emerald-500/20 text-emerald-400" : "text-neutral-500 hover:text-white hover:bg-white/5"}`}
                >
                  <Search size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="h-8 w-8 rounded-xl flex items-center justify-center text-neutral-500 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-300"
                >
                  <X size={16} />
                </button>
              </div>
            </header>

            {/* Search Bar */}
            <AnimatePresence>
              {showSearch && (
                <Motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="shrink-0 border-b border-[#1a1a1a] bg-[#0d0d0d] overflow-hidden"
                >
                  <div className="px-4 py-3">
                    <div className="relative group">
                      <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
                      <input
                        type="text"
                        autoFocus
                        placeholder="Search transmissions..."
                        value={searchQuery}
                        onChange={(e) => {
                          setSearchQuery(e.target.value);
                          
                          // Debounce search
                          if (searchTimeoutRef.current) {
                            clearTimeout(searchTimeoutRef.current);
                          }
                          
                          searchTimeoutRef.current = setTimeout(() => {
                            searchMessages(e.target.value);
                          }, 300);
                        }}
                        className="w-full bg-white/[0.03] border-white/5 focus:border-emerald-500/30 rounded-xl pl-9 pr-10 py-2 text-[11px] text-white transition-all placeholder:text-neutral-600 outline-none"
                      />
                      {searchQuery && (
                        <button
                          onClick={() => {
                            setSearchQuery("");
                            clearSearch();
                          }}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white transition-colors"
                        >
                          <X size={12} />
                        </button>
                      )}
                    </div>
                    {isSearching && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-1 h-1 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        <span className="text-[9px] text-neutral-500 ml-1">Searching...</span>
                      </div>
                    )}
                  </div>
                </Motion.div>
              )}
            </AnimatePresence>

            {/* Pinned Message Banner */}
            <AnimatePresence>
              {isGlobal && pinnedMessage && (
                <Motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="shrink-0 border-b border-[#1a1a1a] bg-[#0d0d0d] overflow-hidden"
                >
                  <div className="flex items-center gap-2 px-3 py-2">
                    <Pin size={12} className="text-amber-400 shrink-0" />
                    <p className="text-[11px] text-neutral-400 truncate flex-1">
                      {pinnedMessage.message}
                    </p>
                    {user?.is_admin && (
                      <button
                        onClick={() => unpinMessage(pinnedMessage.timestamp)}
                        className="text-[9px] text-neutral-600 hover:text-red-400 transition-colors shrink-0"
                      >
                        Unpin
                      </button>
                    )}
                  </div>
                </Motion.div>
              )}
            </AnimatePresence>

            {/* Messages Area */}
            <main className="flex-1 min-h-0 relative flex flex-col bg-[#050505]">
              <div className="relative z-10 flex-1 min-h-0 h-full">
                <MessageList
                  user={user}
                  messages={messages}
                  viewportHeight={viewportHeight}
                  editMessage={editMessage}
                  deleteMessage={deleteMessage}
                  toggleReaction={toggleReaction}
                  pinMessage={pinMessage}
                  loadMore={loadMore}
                  hasMore={hasMore}
                  isLoadingMore={isLoadingMore}
                  markAsRead={markAsRead}
                  searchResults={searchResults}
                  isSearching={isSearching}
                />
              </div>
            </main>

            {/* Typing Indicator */}
            <AnimatePresence>
              {otherTyping.length > 0 && (
                <Motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="shrink-0 px-4 py-1 bg-[#050505]"
                >
                  <span className="text-[10px] text-neutral-500 italic">
                    {otherTyping.length === 1
                      ? `${otherTyping[0].username} is typing...`
                      : otherTyping.length === 2
                        ? `${otherTyping[0].username} and ${otherTyping[1].username} are typing...`
                        : `${otherTyping[0].username} and ${otherTyping.length - 1} others are typing...`}
                  </span>
                </Motion.div>
              )}
            </AnimatePresence>

            {/* Input */}
            <div className="shrink-0 relative z-20">
              <ChatInput
                user={user}
                sendMessage={handleSendMessage}
                showPicker={showPicker}
                setShowPicker={setShowPicker}
                inputRef={inputRef}
                pickerRef={pickerRef}
                emojiButtonRef={emojiButtonRef}
                sendTyping={sendTyping}
                placeholder={chatPlaceholder}
              />
            </div>

            {/* Safety padding for non-keyboard mobile states */}
            {!isKeyboardVisible && (
              <div className="h-safe sm:h-0 bg-[#050505]" />
            )}
          </Motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default memo(ChatDrawer);
