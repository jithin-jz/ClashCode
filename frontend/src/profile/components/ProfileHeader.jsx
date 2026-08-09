import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, ArrowLeft, Settings, LogOut } from "lucide-react";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "../../components/ui/avatar";

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
      {/* Banner */}
      <div className="h-36 bg-neutral-900 relative overflow-hidden rounded-t-xl">
        {profileUser?.profile?.banner_url ? (
          <img
            src={profileUser.profile.banner_url}
            alt="Banner"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-neutral-900 via-neutral-950 to-black" />
        )}

        {/* Banner upload overlay (edit mode) */}
        {isOwnProfile && isEditing && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
            <button
              onClick={() => bannerInputRef.current?.click()}
              disabled={uploadingBanner}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white text-[11px] font-medium hover:bg-white/20 transition-colors"
            >
              {uploadingBanner ? (
                <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <><Camera size={13} /> Change banner</>
              )}
            </button>
          </div>
        )}

        {/* Top controls */}
        <div className="absolute top-3 px-3 w-full flex items-center justify-between z-20">
          <button
            onClick={() => navigate(-1)}
            className="h-8 w-8 flex items-center justify-center rounded-md text-white/80 hover:text-white bg-black/40 backdrop-blur-sm transition-colors"
          >
            <ArrowLeft size={15} />
          </button>

          <div className="flex items-center gap-1.5">
            {isOwnProfile && (
              <>
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className={`h-8 w-8 flex items-center justify-center rounded-md backdrop-blur-sm transition-all ${
                    isEditing
                      ? "bg-white text-black"
                      : "text-white/80 hover:text-white bg-black/40"
                  }`}
                >
                  <Settings size={14} />
                </button>
                <button
                  onClick={handleLogout}
                  className="h-8 w-8 flex items-center justify-center rounded-md text-white/80 hover:text-red-400 bg-black/40 backdrop-blur-sm transition-colors"
                >
                  <LogOut size={14} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Centered Avatar */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 z-30">
        <div className="relative">
          <div className="p-1 rounded-full bg-black border border-neutral-800">
            <Avatar className="w-20 h-20">
              <AvatarImage
                src={profileUser?.profile?.avatar_url}
                alt={profileUser?.username}
                className="object-cover"
              />
              <AvatarFallback className="bg-neutral-900 text-white text-2xl font-semibold">
                {profileUser?.username?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </div>

          {isOwnProfile && (
            <button
              onClick={() => avatarInputRef.current?.click()}
              disabled={uploadingAvatar}
              className="absolute bottom-0 right-0 w-7 h-7 bg-white text-black border-[3px] border-black rounded-full flex items-center justify-center hover:scale-110 active:scale-95 transition-transform"
            >
              {uploadingAvatar ? (
                <div className="w-3 h-3 border-2 border-black/20 border-t-black rounded-full animate-spin" />
              ) : (
                <Camera size={12} strokeWidth={2.5} />
              )}
            </button>
          )}
        </div>

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
