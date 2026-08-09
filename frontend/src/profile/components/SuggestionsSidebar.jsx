import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";

const SuggestionsSidebar = ({ users, onUserClick }) => {
  if (!users || users.length === 0) return null;

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden">
      <div className="px-4 py-3 border-b border-neutral-900">
        <p className="text-[11px] font-medium text-neutral-500">Suggested</p>
      </div>
      {/* Horizontal scroll on mobile, vertical list on desktop */}
      <div className="p-3 flex lg:flex-col gap-2 overflow-x-auto lg:overflow-x-visible">
        {users.slice(0, 5).map((u) => (
          <button
            key={u.username}
            className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-neutral-900 transition-colors text-left shrink-0 lg:shrink lg:w-full"
            onClick={() => onUserClick(u.username)}
          >
            <Avatar className="h-7 w-7 border border-neutral-800 shrink-0">
              <AvatarImage src={u.avatar_url || u.profile?.avatar_url} alt={u.username} className="object-cover" />
              <AvatarFallback className="bg-neutral-900 text-[9px] font-medium text-neutral-400">
                {u.username?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <span className="text-[12px] font-medium text-neutral-300 truncate">
              {u.username}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestionsSidebar;
