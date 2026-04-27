import React, { useState, useEffect, useRef, memo, useCallback } from "react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import useChatStore from "../../stores/useChatStore";
import ChatInput from "../components/ChatInput";
import MessageList from "../components/MessageList";
import ChatHeader from "../components/ChatHeader";
import ChatSearch from "../components/ChatSearch";
import ChatPinnedBanner from "../components/ChatPinnedBanner";
import ChatTypingIndicator from "../components/ChatTypingIndicator";

/**
 * ChatDrawer Component
 * 
 * Orchestrates the global chat system, including:
 * - WebSocket connectivity
 * - Message searching and pinning
 * - Typing indicators
 * - Responsive viewport height handling for mobile keyboards
 */
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

  // Close emoji picker on outside click
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

  // Visual Viewport API for flexible mobile keyboard support
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

  // Lifecycle: Connect to WebSocket when drawer opens
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

  const otherTyping = typingUsers.filter((t) => t.username !== user?.username);
  const isGlobal = currentRoom === "global";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop Overlay */}
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

          {/* Side Drawer Container */}
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
            {/* Ambient Lighting FX */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
              <div className="absolute top-[-10%] right-[-10%] w-[300px] h-[300px] bg-emerald-500/10 blur-[100px] rounded-full" />
              <div className="absolute bottom-[-5%] left-[-10%] w-[250px] h-[250px] bg-purple-500/10 blur-[80px] rounded-full" />
            </div>

            <ChatHeader
              onlineCount={onlineCount}
              showSearch={showSearch}
              setShowSearch={setShowSearch}
              setSearchQuery={setSearchQuery}
              clearSearch={clearSearch}
              searchTimeoutRef={searchTimeoutRef}
              setOpen={setOpen}
            />

            <ChatSearch
              showSearch={showSearch}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              searchMessages={searchMessages}
              clearSearch={clearSearch}
              isSearching={isSearching}
              searchTimeoutRef={searchTimeoutRef}
            />

            <ChatPinnedBanner
              pinnedMessage={pinnedMessage}
              isGlobal={isGlobal}
              user={user}
              unpinMessage={unpinMessage}
            />

            {/* Messages Feed */}
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
                  isSearchMode={showSearch && searchQuery.length > 0}
                />
              </div>
            </main>

            <ChatTypingIndicator otherTyping={otherTyping} />

            {/* Input Bar */}
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
                placeholder="Global chat... (Ctrl+B)"
              />
            </div>

            {/* Bottom Padding for Non-Keyboard states */}
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
