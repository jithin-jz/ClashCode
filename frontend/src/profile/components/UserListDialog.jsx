import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "../../components/ui/avatar";
import { Button } from "../../components/ui/button";

const UserListDialog = ({
  listType,
  setListType,
  userList,
  listLoading,
  handleListFollowToggle,
  currentUser,
}) => {
  const navigate = useNavigate();

  return (
    <Dialog open={!!listType} onOpenChange={() => setListType(null)}>
      <DialogContent className="bg-[#141414] border-[#404040]/30 text-white max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-center capitalize">
            {listType}
          </DialogTitle>
        </DialogHeader>
        <div className="max-h-[400px] overflow-y-auto space-y-4 pr-2 custom-scrollbar">
          {listLoading ? (
            <div className="py-10 text-center text-neutral-500">Loading...</div>
          ) : userList.length === 0 ? (
            <div className="py-10 text-center text-neutral-500">
              No users found.
            </div>
          ) : (
            userList.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between gap-3 p-2 hover:bg-white/5 rounded-xl transition-colors group"
              >
                <div
                  className="flex items-center gap-3 cursor-pointer flex-1 min-w-0"
                  onClick={() => {
                    setListType(null);
                    navigate(`/profile/${user.username}`);
                  }}
                >
                  <Avatar className="h-10 w-10 border border-white/10 group-hover:border-white/20 transition-colors">
                    <AvatarImage src={user.profile?.avatar_url} />
                    <AvatarFallback className="bg-zinc-800 text-xs">
                      {user.username?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-white truncate">
                      {[user.first_name, user.last_name]
                        .filter(Boolean)
                        .join(" ") || user.username}
                    </div>
                    <div className="text-[10px] text-neutral-500 font-mono">
                      @{user.username}
                    </div>
                  </div>
                </div>
                {currentUser?.username !== user.username && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleListFollowToggle(user.username)}
                    className={`h-8 px-4 text-[11px] font-bold rounded-lg transition-all ${
                      user.is_following
                        ? "bg-white/10 text-white hover:bg-white/20"
                        : "bg-white text-black hover:bg-zinc-200"
                    }`}
                  >
                    {user.is_following ? "Unfollow" : "Follow"}
                  </Button>
                )}
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UserListDialog;
