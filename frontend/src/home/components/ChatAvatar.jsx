import React, { useState } from "react";
import { User } from "lucide-react";

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

export default ChatAvatar;
