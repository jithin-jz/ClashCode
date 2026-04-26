import React, { memo, useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import { Lock, MessageCircle, Search } from "lucide-react";
import { motion as Motion } from "framer-motion";
import MessageItem from "./MessageItem";

/**
 * MessageList Component
 * Handles the scrollable list of messages, infinite scroll logic, and search results.
 */
const MessageList = ({
  user,
  messages,
  viewportHeight,
  editMessage,
  deleteMessage,
  toggleReaction,
  pinMessage,
  loadMore,
  hasMore,
  isLoadingMore,
  markAsRead,
  searchResults = [],
  isSearching = false,
  isSearchMode = false,
}) => {
  const scrollRef = React.useRef(null);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);
  const [editingMsgId, setEditingMsgId] = useState(null);
  const [editContent, setEditContent] = useState("");

  // Mark last message as read if it's from others
  useEffect(() => {
    if (!user || !messages.length) return;
    const lastMsg = messages[messages.length - 1];
    const isOwn = lastMsg.user_id === user.user_id;
    const alreadyRead = lastMsg.read_by?.includes(user.username);

    if (!isOwn && !alreadyRead) {
      markAsRead(lastMsg.timestamp);
    }
  }, [messages, user, markAsRead]);

  const handleEditInit = (msg) => {
    setEditingMsgId(msg.timestamp);
    setEditContent(msg.message);
  };

  const handleEditSave = (timestamp) => {
    if (editContent.trim()) {
      editMessage(timestamp, editContent);
    }
    setEditingMsgId(null);
  };

  const handleDelete = (timestamp) => {
    deleteMessage(timestamp);
  };

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    if (shouldScrollToBottom) {
      scrollToBottom();
    }
  }, [messages, shouldScrollToBottom, viewportHeight]);

  useEffect(() => {
    scrollToBottom();
    const timer = setTimeout(scrollToBottom, 150);
    return () => clearTimeout(timer);
  }, [user]);

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShouldScrollToBottom(isAtBottom);
  };

  const userMetadata = useMemo(() => {
    const map = {};
    messages.forEach((msg) => {
      if (msg.user_id) {
        map[msg.user_id] = {
          username: msg.username,
          avatar_url: msg.avatar_url,
        };
      }
    });
    return map;
  }, [messages]);

  if (!user) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-transparent">
        <Motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="relative mb-8"
        >
          <div className="w-24 h-24 bg-gradient-to-br from-white/5 to-white/[0.02] backdrop-blur-md rounded-[2rem] flex items-center justify-center border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative z-10 group overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/10 via-transparent to-purple-500/10 opacity-50" />
            <Lock
              size={36}
              className="text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] group-hover:scale-110 transition-transform duration-500"
            />
          </div>
          <div className="absolute -inset-8 bg-emerald-500/20 rounded-full blur-[60px] opacity-30 animate-pulse" />
          <div className="absolute -inset-8 bg-purple-500/20 rounded-full blur-[60px] opacity-20 left-10 top-10" />
        </Motion.div>

        <h3 className="text-2xl font-black text-white mb-3 uppercase tracking-[0.3em] font-mono drop-shadow-md">
          Forge Link
        </h3>
        <p className="text-neutral-500 text-[11px] mb-10 max-w-[220px] leading-relaxed font-bold uppercase tracking-wider opacity-80">
          Neural connection required. <br />
          Join the inner circle to access transmission.
        </p>

        <Link
          to="/login"
          className="group relative px-10 py-4 overflow-hidden rounded-2xl transition-all active:scale-95"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500 to-cyan-600 transition-all group-hover:scale-110" />
          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          <span className="relative text-black font-black text-xs uppercase tracking-[0.25em] flex items-center gap-2">
            Initiate Link
            <MessageCircle size={14} />
          </span>
        </Link>
      </div>
    );
  }

  const displayedMessages = isSearchMode ? searchResults : messages;

  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="h-full overflow-y-auto px-4 py-6 scrollbar-hide space-y-8 flex flex-col"
    >
      {searchResults.length > 0 && (
        <div className="shrink-0 pb-4 border-b border-white/5">
          <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500/60 mb-1">
            Search Results
          </h4>
          <p className="text-[9px] text-neutral-600 font-mono">
            {searchResults.length} transmissions found matching query
          </p>
        </div>
      )}

      {hasMore && !searchResults.length && (
        <div className="flex justify-center pb-4">
          <button
            onClick={loadMore}
            disabled={isLoadingMore}
            className="text-[10px] font-black uppercase tracking-widest text-neutral-500 hover:text-emerald-400 disabled:opacity-50 transition-colors"
          >
            {isLoadingMore ? "Loading signal..." : "Load older transmissions"}
          </button>
        </div>
      )}

      {displayedMessages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center py-20 px-6">
          <div className="relative mb-8">
            <div className="absolute -inset-4 bg-gradient-to-tr from-emerald-500/20 to-purple-500/20 rounded-full blur-2xl opacity-50" />
            <div className="w-20 h-20 bg-white/[0.02] backdrop-blur-sm rounded-[2.5rem] flex items-center justify-center border border-white/[0.05] shadow-2xl relative z-10">
              <Search size={32} className="text-neutral-800" />
            </div>
          </div>
          <p className="text-neutral-400 text-xs font-black uppercase tracking-[0.4em] mb-3">
            {isSearchMode ? "No matches found" : "Silence in Transmission"}
          </p>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-neutral-600 text-[10px] font-bold uppercase tracking-widest">
              {isSearchMode ? "Try a different query" : "Awaiting signal..."}
            </p>
          </div>
        </div>
      )}

      {displayedMessages.map((msg, index) => {
        const isOwn =
          msg.user_id === user?.user_id ||
          (msg.user_id &&
            user?.user_id &&
            String(msg.user_id) === String(user.user_id)) ||
          msg.username === user?.username;
        const metadata = userMetadata[msg.user_id] || {
          username: msg.username,
          avatar_url: msg.avatar_url,
        };

        const apiURL = import.meta.env.VITE_API_URL || "http://localhost/api";
        const baseUrl = apiURL.replace("/api", "");
        const formattedAvatar = (() => {
          const rawUrl = isOwn
            ? user?.profile?.avatar_url
            : metadata.avatar_url;
          if (!rawUrl) return null;
          if (rawUrl.startsWith("http")) return rawUrl;
          return `${baseUrl}${rawUrl}`;
        })();

        return (
          <MessageItem
            key={msg.timestamp || index}
            msg={msg}
            user={user}
            isOwn={isOwn}
            metadata={metadata}
            formattedAvatar={formattedAvatar}
            editingMsgId={editingMsgId}
            editContent={editContent}
            setEditingMsgId={setEditingMsgId}
            setEditContent={setEditContent}
            handleEditInit={handleEditInit}
            handleEditSave={handleEditSave}
            handleDelete={handleDelete}
            toggleReaction={toggleReaction}
            pinMessage={pinMessage}
          />
        );
      })}
      <div className="h-4 w-full shrink-0" />
    </div>
  );
};

export default memo(MessageList);
