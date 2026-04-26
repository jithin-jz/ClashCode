import React, { memo } from "react";
import { Link } from "react-router-dom";
import { Trash2, Edit, Pin, CheckCheck, X, Check } from "lucide-react";
import { motion as Motion } from "framer-motion";
import ChatAvatar from "./ChatAvatar";
import RenderMessage from "./RenderMessage";
import ReactionBar from "./ReactionBar";

/**
 * MessageItem component
 * Renders a single message transmission with all associated actions and metadata.
 */
const MessageItem = ({
  msg,
  user,
  isOwn,
  metadata,
  formattedAvatar,
  editingMsgId,
  editContent,
  setEditingMsgId,
  setEditContent,
  handleEditInit,
  handleEditSave,
  handleDelete,
  toggleReaction,
  pinMessage,
}) => {
  return (
    <Motion.div
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
        className={`relative flex flex-col gap-1 max-w-[70%] ${isOwn ? "items-end" : "items-start"}`}
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
                    <img src={imageUrl} alt="" className="w-full h-auto" />
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
                className={`${msg.read_by?.length > 0 ? "text-emerald-400" : "text-neutral-400/40"}`}
              />
            )}
          </div>
        </div>

        {/* Unified Toolbar (Actions + Reactions) */}
        <div
          className={`absolute bottom-0 ${isOwn ? "right-2" : "left-2"} translate-y-1/2 flex items-center gap-2 z-20`}
        >
          <ReactionBar
            reactions={msg.reactions}
            onReact={(emoji) => toggleReaction(msg.timestamp, emoji)}
            username={user?.username}
            isOwn={isOwn}
          />

          {editingMsgId !== msg.timestamp && (
            <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shrink-0 bg-black/40 backdrop-blur-sm rounded-full px-1.5 py-0.5 border border-white/5">
              {isOwn && (
                <>
                  <button
                    onClick={() => handleEditInit(msg)}
                    className="text-neutral-400 hover:text-emerald-400 transition-colors p-1"
                    title="Edit"
                  >
                    <Edit size={12} />
                  </button>
                  <button
                    onClick={() => handleDelete(msg.timestamp)}
                    className="text-neutral-400 hover:text-red-400 transition-colors p-1"
                    title="Delete"
                  >
                    <Trash2 size={12} />
                  </button>
                </>
              )}
              {user?.is_admin && (
                <button
                  onClick={() => pinMessage(msg.timestamp, msg.message)}
                  className="text-neutral-400 hover:text-amber-400 transition-colors p-1"
                  title="Pin message"
                >
                  <Pin size={12} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </Motion.div>
  );
};

export default memo(MessageItem);
