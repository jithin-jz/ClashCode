import React from "react";
import { useNavigate } from "react-router-dom";
import AchievementBadges from "./AchievementBadges";

const ProfileInfo = ({
  profileUser,
  isOwnProfile,
  handleFollowToggle,
  fetchUserList,
}) => {
  const navigate = useNavigate();

  return (
    <div className="pt-2 pb-6 px-6 text-center">
      {/* Name */}
      <h2 className="text-lg font-semibold text-white tracking-tight">
        {[profileUser?.first_name, profileUser?.last_name]
          .filter(Boolean)
          .join(" ")
          .trim() || profileUser?.username}
      </h2>
      <p className="text-[12px] text-neutral-500 mt-0.5">
        @{profileUser?.username}
      </p>

      {/* Bio */}
      {profileUser?.profile?.bio && (
        <p className="text-[13px] text-neutral-400 mt-3 max-w-[280px] mx-auto leading-relaxed">
          {profileUser.profile.bio}
        </p>
      )}

      {/* Achievements */}
      <div className="mt-4 mb-3">
        <AchievementBadges username={profileUser?.username} />
        <button
          onClick={() => navigate("/achievements")}
          className="text-[11px] text-neutral-600 hover:text-white transition-colors mt-1.5"
        >
          All achievements →
        </button>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-center gap-8 py-4 border-t border-neutral-900">
        <button
          onClick={() => fetchUserList("followers")}
          className="text-center group"
        >
          <div className="text-base font-semibold text-white group-hover:text-neutral-300 transition-colors tabular-nums">
            {profileUser?.followers_count || 0}
          </div>
          <div className="text-[11px] text-neutral-600 mt-0.5">Followers</div>
        </button>
        <div className="w-px h-8 bg-neutral-900" />
        <button
          onClick={() => fetchUserList("following")}
          className="text-center group"
        >
          <div className="text-base font-semibold text-white group-hover:text-neutral-300 transition-colors tabular-nums">
            {profileUser?.following_count || 0}
          </div>
          <div className="text-[11px] text-neutral-600 mt-0.5">Following</div>
        </button>
      </div>

      {/* Follow Button */}
      {!isOwnProfile && (
        <div className="mt-3">
          <button
            onClick={handleFollowToggle}
            className={`w-full h-9 rounded-lg text-[12px] font-medium transition-all ${
              profileUser?.is_following
                ? "text-neutral-400 border border-neutral-800 hover:border-neutral-600"
                : "bg-white text-black hover:bg-neutral-200"
            }`}
          >
            {profileUser?.is_following ? "Following" : "Follow"}
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileInfo;
