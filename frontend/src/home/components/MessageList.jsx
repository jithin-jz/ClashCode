import React, { memo, useState, useMemo, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  Lock,
  MessageCircle,
  User,
  Trash2,
  Edit,
  Pin,
  Smile,
  CheckCheck,
  X,
  Check,
} from "lucide-react";
import { motion as Motion, AnimatePresence } from "framer-motion";

const REACTION_EMOJIS = ["👍", "🔥", "😂", "❤️", "🎉", "💯"];

const ChatAvatar = ({ isOwn, avatarUrl, username }) => {
  const [hasError, setHasError] = useState(false);
  const showPlaceholder = !avatarUrl || hasError;

  return (
    <div className="w-full h-full relative group">
      {avatarUrl && !hasError && (
        <img
          src={avatarUrl}
          alt={username}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          onError={() => setHasError(true)}
        />
      )}
      {showPlaceholder && (
        <div
          className={`w-full h-full flex items-center justify-center text-[10px] font-black tracking-tighter ${
            isOwn
              ? "bg-gradient-to-br from-emerald-500/30 via-emerald-500/20 to-emerald-500/40 text-emerald-400"
              : "bg-gradient-to-br from-purple-500/30 via-purple-500/20 to-purple-500/40 text-purple-400"
          } animate-pulse`}
          style={{ animationDuration: "3s" }}
        >
          {username?.charAt(0).toUpperCase() || <User size={12} />}
        </div>
      )}
      <div className="absolute inset-0 ring-1 ring-inset ring-white/10 rounded-full" />
    </div>
  );
};

// Render message text with @mentions highlighted
const RenderMessage = ({ text }) => {
  if (!text) return null;
  const parts = text.split(/(@\w+)/g);
  return (
    <p className="break-words font-medium">
      {parts.map((part, i) =>
        part.startsWith("@") ? (
          <Link
            key={i}
            to={`/profile/${part.slice(1)}`}
            className="text-amber-400 hover:text-amber-300 font-bold transition-colors"
          >
            {part}
          </Link>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </p>
  );
};

// Reaction display & picker
const ReactionBar = ({ reactions, onReact, username }) => {
  const [showPicker, setShowPicker] = useState(false);
  const pickerRef = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setShowPicker(false);
      }
    };
    if (showPicker) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showPicker]);

  const hasReactions = reactions && Object.keys(reactions).length > 0;

  return (
    <div className="flex items-center gap-1.5 flex-wrap relative">
      {hasReactions &&
        Object.entries(reactions).map(([emoji, users]) => (
          <button
            key={emoji}
            onClick={() => onReact(emoji)}
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-[11px] border transition-all shadow-sm ${
              users.includes(username)
                ? "bg-emerald-500/25 border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/35"
                : "bg-white/10 border-white/20 text-neutral-300 hover:bg-white/20 hover:border-white/30"
            }`}
            title={users.join(", ")}
          >
            <span className="text-sm">{emoji}</span>
            <span className="font-mono text-[10px] font-semibold">{users.length}</span>
          </button>
        ))}
      <div className="relative" ref={pickerRef}>
        <button
          onClick={() => setShowPicker(!showPicker)}
          className="w-6 h-6 rounded-full flex items-center justify-center text-neutral-500 hover:text-emerald-400 hover:bg-emerald-500/10 border border-transparent hover:border-emerald-500/30 transition-all"
          title="Add reaction"
        >
          <Smile size={14} />
        </button>
        <AnimatePresence>
          {showPicker && (
            <Motion.div
              initial={{ opacity: 0, scale: 0.8, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 10 }}
              className="absolute bottom-8 left-0 z-50 flex gap-1.5 p-2 bg-[#0a0a0a] border border-white/20 rounded-xl shadow-2xl backdrop-blur-xl"
            >
              {REACTION_EMOJIS.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => {
                    onReact(emoji);
                    setShowPicker(false);
                  }}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/15 hover:scale-110 transition-all text-base"
                >
                  {emoji}
                </button>
              ))}
            </Motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

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
}) => {
  const scrollRef = React.useRef(null);
  
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
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);
  const [editingMsgId, setEditingMsgId] = useState(null);
  const [editContent, setEditContent] = useState("");

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

  const displayedMessages = searchResults.length > 0 ? searchResults : messages;

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

      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center py-20 px-6">
          <div className="relative mb-8">
            <div className="absolute -inset-4 bg-gradient-to-tr from-emerald-500/20 to-purple-500/20 rounded-full blur-2xl opacity-50" />
            <div className="w-20 h-20 bg-white/[0.02] backdrop-blur-sm rounded-[2.5rem] flex items-center justify-center border border-white/[0.05] shadow-2xl relative z-10">
              <MessageCircle size={32} className="text-neutral-800" />
            </div>
          </div>
          <p className="text-neutral-400 text-xs font-black uppercase tracking-[0.4em] mb-3">
            Silence in Transmission
          </p>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-neutral-600 text-[10px] font-bold uppercase tracking-widest">
              Awaiting signal...
            </p>
          </div>
        </div>
      )}

      {displayedMessages.map((msg, index) => {
        // Compare using user_id or username as fallback
        const isOwn = msg.user_id === user?.user_id || 
                     (msg.user_id && user?.user_id && String(msg.user_id) === String(user.user_id)) ||
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

        // Debug: Log first message to check structure
        if (index === 0) {
          console.log('Message debug:', { 
            msgUserId: msg.user_id, 
            userUserId: user?.user_id, 
            msgUsername: msg.username, 
            userUsername: user?.username, 
            isOwn 
          });
        }

        return (
          <Motion.div
            key={msg.timestamp || index}
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className={`flex gap-2 ${isOwn ? "justify-end" : "justify-start"} group`}
          >
            {/* Other users' avatar (left side) */}
            {!isOwn && (
              <Link
                to={`/profile/${metadata.username}`}
                className="relative shrink-0 w-8 h-8 rounded-full overflow-hidden border border-white/10 hover:border-white/30 transition-all duration-300 shadow-sm"
              >
                <ChatAvatar
                  isOwn={false}
                  avatarUrl={formattedAvatar}
                  username={metadata.username}
                />
              </Link>
            )}

            {/* Message Content */}
            <div
              className={`flex flex-col gap-1 max-w-[70%] ${isOwn ? "items-end" : "items-start"}`}
            >
              {/* Username (only for others) */}
              {!isOwn && (
                <Link
                  to={`/profile/${metadata.username}`}
                  className="text-[10px] font-bold text-neutral-400 hover:text-neutral-300 transition-colors ml-1"
                >
                  {metadata.username}
                </Link>
              )}

              {/* Message Bubble */}
              <div
                className={`
                  relative px-4 py-2.5 text-[13px] leading-relaxed transition-all duration-300 rounded-2xl shadow-md
                  ${
                    isOwn
                      ? "bg-gradient-to-br from-emerald-600/30 via-emerald-500/20 to-emerald-600/25 border border-emerald-500/40 text-emerald-50 rounded-br-none"
                      : "bg-white/[0.05] backdrop-blur-md border border-white/[0.1] text-neutral-200 rounded-bl-none hover:bg-white/[0.07]"
                  }
                  ${msg.message?.startsWith("IMAGE:") ? "p-2 !rounded-xl" : ""}
                `}
              >
                  {msg.message?.startsWith("IMAGE:") ? (
                    (() => {
                      const [imageUrl, ownerUsername] = msg.message
                        .replace("IMAGE:", "")
                        .split("|");
                      return (
                        <div className="space-y-2">
                          <Link
                            to={`/profile/${ownerUsername}`}
                            className="block overflow-hidden rounded-lg border border-white/5 shadow-lg"
                          >
                            <img
                              src={imageUrl}
                              alt=""
                              className="w-full h-auto"
                            />
                          </Link>
                          <div className="flex items-center justify-between px-1 py-0.5">
                            <p className="text-[8px] font-bold uppercase tracking-widest text-neutral-600">
                              Transmission
                            </p>
                            <Link
                              to={`/profile/${ownerUsername}`}
                              className="text-[8px] font-bold uppercase tracking-widest text-emerald-500 hover:underline"
                            >
                              Verify
                            </Link>
                          </div>
                        </div>
                      );
                    })()
                  ) : editingMsgId === msg.timestamp ? (
                    <div className="flex flex-col gap-2 relative z-50">
                      <input
                        type="text"
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="bg-black/40 border border-emerald-500/50 rounded px-2 py-1.5 text-emerald-100 outline-none w-full min-w-[200px]"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleEditSave(msg.timestamp);
                          if (e.key === "Escape") setEditingMsgId(null);
                        }}
                        autoFocus
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => setEditingMsgId(null)}
                          className="text-white/50 hover:text-white p-1 bg-black/50 rounded"
                        >
                          <X size={12} />
                        </button>
                        <button
                          onClick={() => handleEditSave(msg.timestamp)}
                          className="text-emerald-500 hover:text-emerald-400 p-1 bg-black/50 rounded"
                        >
                          <Check size={12} />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <RenderMessage text={msg.message} />
                  )}

                  {/* Time stamp inside bubble */}
                  <div className="flex items-center justify-end gap-1 mt-1">
                    <span className="text-[9px] font-mono text-neutral-400/60 tracking-tighter">
                      {new Date(msg.timestamp).toLocaleTimeString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                        hour12: false,
                      })}
                    </span>
                    {isOwn && (
                      <CheckCheck 
                        size={10} 
                        className={`${(msg.read_by?.length > 0) ? "text-emerald-400" : "text-neutral-400/40"}`} 
                      />
                    )}
                  </div>
                </div>

                {/* Action Buttons (visible on hover) */}
                {editingMsgId !== msg.timestamp && (
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shrink-0 pt-0.5">
                    {isOwn && (
                      <>
                        <button
                          onClick={() => handleEditInit(msg)}
                          className="text-neutral-600 hover:text-emerald-500 transition-colors p-1 rounded hover:bg-white/5"
                          title="Edit"
                        >
                          <Edit size={11} />
                        </button>
                        <button
                          onClick={() => handleDelete(msg.timestamp)}
                          className="text-neutral-600 hover:text-red-500 transition-colors p-1 rounded hover:bg-white/5"
                          title="Delete"
                        >
                          <Trash2 size={11} />
                        </button>
                      </>
                    )}
                    {user?.is_admin && (
                      <button
                        onClick={() => pinMessage(msg.timestamp, msg.message)}
                        className="text-neutral-600 hover:text-amber-400 transition-colors p-1 rounded hover:bg-white/5"
                        title="Pin message"
                      >
                        <Pin size={11} />
                      </button>
                    )}
                  </div>
                )}

              {/* Reaction Bar - positioned below message */}
              <div className={`flex items-center gap-1 mt-1.5 ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <ReactionBar
                  reactions={msg.reactions}
                  onReact={(emoji) => toggleReaction(msg.timestamp, emoji)}
                  username={user?.username}
                />
              </div>
            </div>
          </Motion.div>
        );
      })}
      <div className="h-4 w-full shrink-0" />
    </div>
  );
};

export default memo(MessageList);
