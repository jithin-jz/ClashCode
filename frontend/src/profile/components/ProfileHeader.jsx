import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, ArrowLeft, Settings, LogOut } from "lucide-react";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "../../components/ui/avatar";
import { Button } from "../../components/ui/button";

const ProfileHeader = ({
  profileUser,
  isOwnProfile,
  uploadingAvatar,
  uploadingBanner,
  handleImageUpload,
  setIsEditing,
  isEditing,
  handleLogout,
}) => {
  const navigate = useNavigate();
  const avatarInputRef = useRef(null);
  const bannerInputRef = useRef(null);

  return (
    <div className="relative">
      <div className="h-40 bg-[#1a1a1a]/40 relative overflow-hidden rounded-t-xl">
        {profileUser?.profile?.banner_url ? (
          <img
            src={profileUser.profile.banner_url}
            alt="Banner"
            className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
          />
        ) : (
          <div className="w-full h-full bg-linear-to-r from-[#1a1a1a] via-[#111111] to-[#1a1a1a]" />
        )}

        {/* Banner Upload Trigger (Visible only in Edit Mode) */}
        {isOwnProfile && isEditing && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px] transition-all z-10 group/banner">
            <Button
              onClick={() => bannerInputRef.current?.click()}
              disabled={uploadingBanner}
              className="bg-white/10 hover:bg-white/20 text-white border border-white/20 gap-2 px-6 py-2 rounded-xl font-bold text-xs backdrop-blur-md transition-all active:scale-95 cursor-pointer"
            >
              {uploadingBanner ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Camera size={14} />
                  CHANGE BANNER
                </>
              )}
            </Button>
          </div>
        )}

        {/* Profile Controls Overlay on Banner */}
        <div className="absolute top-3 px-3 w-full flex items-center justify-between pointer-events-none z-20">
          <div className="pointer-events-auto">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(-1)}
              className="h-8 w-8 text-white/80 hover:text-white bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-lg transition-all"
            >
              <ArrowLeft size={16} />
            </Button>
          </div>
          <div className="flex items-center gap-2 pointer-events-auto">
            {isOwnProfile && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsEditing(!isEditing)}
                  className={`h-8 w-8 backdrop-blur-md rounded-lg transition-all ${
                    isEditing
                      ? "bg-emerald-500 text-black shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                      : "text-white/80 hover:text-white bg-black/40 hover:bg-black/60"
                  }`}
                >
                  <Settings
                    size={16}
                    className={isEditing ? "animate-spin-slow" : ""}
                  />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  className="h-8 w-8 text-white/80 hover:text-red-400 bg-black/40 hover:bg-red-500/20 backdrop-blur-md rounded-lg transition-all"
                >
                  <LogOut size={16} />
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Banner Overlay Gradient */}
        <div className="absolute inset-0 bg-linear-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
      </div>

      {/* Avatar (Positioned relative to the outer container to avoid overflow-hidden clipping) */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 group/avatar z-30">
        <div className="relative">
          {/* Main Avatar Container */}
          <div className="relative p-1.5 rounded-full bg-[#050505] shadow-[0_10px_40px_rgba(0,0,0,0.9)] border border-white/10 transition-all duration-500 group-hover/avatar:scale-105">
            <Avatar className="w-24 h-24 border-2 border-white/5">
              <AvatarImage
                src={profileUser?.profile?.avatar_url}
                alt={profileUser?.username}
                className="object-cover"
              />
              <AvatarFallback className="bg-gradient-to-br from-zinc-800 to-black text-white text-3xl font-black">
                {profileUser?.username?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </div>

          {/* Animated Ring */}
          <div className="absolute -inset-1 rounded-full bg-gradient-to-tr from-emerald-500/30 via-transparent to-purple-500/30 animate-spin-slow opacity-0 group-hover/avatar:opacity-100 transition-opacity pointer-events-none" />
        </div>

        {isOwnProfile && (
          <div className="absolute bottom-1 right-1 z-10">
            <button
              onClick={() => avatarInputRef.current?.click()}
              disabled={uploadingAvatar}
              className="w-8 h-8 bg-white text-black border-4 border-[#050505] rounded-xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all cursor-pointer shadow-xl"
              title="Change Profile Picture"
            >
              {uploadingAvatar ? (
                <div className="w-3 h-3 border-2 border-black/20 border-t-black rounded-full animate-spin" />
              ) : (
                <Camera size={14} strokeWidth={3} />
              )}
            </button>
          </div>
        )}
        {isOwnProfile && (
          <input
            type="file"
            ref={avatarInputRef}
            className="hidden"
            accept="image/*"
            onChange={(e) => handleImageUpload(e, "avatar")}
          />
        )}
      </div>
      {/* Banner Upload Trigger for Edit Mode */}
      {isOwnProfile && isEditing && (
        <input
          type="file"
          ref={bannerInputRef}
          className="hidden"
          accept="image/*"
          onChange={(e) => handleImageUpload(e, "banner")}
        />
      )}
    </div>
  );
};

export default ProfileHeader;
