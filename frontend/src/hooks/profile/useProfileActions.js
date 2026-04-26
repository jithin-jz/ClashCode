import { useState } from "react";
import { notify } from "../../services/notification";
import { userService } from "../../services/api/userService";
import useUserStore from "../../stores/useUserStore";

export const useProfileActions = (profileUser, setProfileUser, isOwnProfile) => {
  const { updateProfile, followUser } = useUserStore();
  
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const handleImageUpload = async (event, type) => {
    const file = event.target.files[0];
    if (!file) return;

    if (type === "avatar") setUploadingAvatar(true);
    if (type === "banner") setUploadingBanner(true);

    try {
      const updatedUser = await updateProfile({ type, file }, true);
      if (isOwnProfile) setProfileUser(updatedUser);
      notify.success(`${type === "avatar" ? "Profile picture" : "Banner"} updated!`);
    } catch (error) {
      console.error(error);
      notify.error(`Failed to upload ${type}`);
    } finally {
      if (type === "avatar") setUploadingAvatar(false);
      if (type === "banner") setUploadingBanner(false);
    }
  };

  const handleSaveProfile = async (editForm, onSuccess) => {
    setSavingProfile(true);
    try {
      const updatedUser = await updateProfile(editForm);
      setProfileUser(updatedUser);
      notify.success("Profile updated!");
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error(error);
      const apiError = error?.response?.data?.error || error?.response?.data?.detail || "Failed to update profile";
      notify.error(apiError);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleFollowToggle = async () => {
    const targetUsername = profileUser?.username;
    if (!targetUsername) return;

    const previousProfile = profileUser;
    const nextIsFollowing = !previousProfile?.is_following;
    const nextFollowerCount = Math.max(0, (previousProfile?.followers_count || 0) + (nextIsFollowing ? 1 : -1));

    setProfileUser((prev) => ({
      ...prev,
      is_following: nextIsFollowing,
      followers_count: nextFollowerCount,
    }));

    try {
      const data = await followUser(targetUsername);
      setProfileUser((prev) => ({
        ...prev,
        is_following: data.is_following,
        followers_count: data.follower_count,
      }));
    } catch (error) {
      console.error("Failed to toggle follow", error);
      setProfileUser(previousProfile);
      notify.error("Failed to update follow status.");
    }
  };

  return {
    uploadingAvatar,
    uploadingBanner,
    savingProfile,
    handleImageUpload,
    handleSaveProfile,
    handleFollowToggle,
  };
};
