import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";

const SuggestionsSidebar = ({ users, onUserClick }) => {
  if (!users || users.length === 0) return null;

  return (
    <Card className="bg-[#0a0a0a]/60 border-[#404040]/20 backdrop-blur-sm">
      <CardHeader className="p-3 border-b border-white/5">
        <CardTitle className="text-[10px] font-black uppercase tracking-[0.2em] text-neutral-500/80">
          Suggested For You
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 space-y-3">
        {users.slice(0, 5).map((u) => (
          <div
            key={u.username}
            className="flex items-center justify-between gap-3 group cursor-pointer"
            onClick={() => onUserClick(u.username)}
          >
            <div className="flex items-center gap-3 min-w-0">
              <Avatar className="h-9 w-9 border border-white/5">
                <AvatarImage src={u.avatar_url || u.profile?.avatar_url} alt={u.username} className="object-cover" />
                <AvatarFallback className="bg-zinc-800 text-[10px] font-bold text-white">
                  {u.username?.[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <div className="text-xs font-bold text-white truncate">{u.username}</div>
                <div className="text-[10px] text-neutral-500 truncate">Suggested for you</div>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default SuggestionsSidebar;
