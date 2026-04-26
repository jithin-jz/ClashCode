import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import { userService } from "../services/api/userService";
import { notify } from "../services/notification";

// Sub-hooks
import { useProfileData } from "./profile/useProfileData";
import { useProfileActions } from "./profile/useProfileActions";
import { useSocialConnections } from "./profile/useSocialConnections";
import { useContributions } from "./profile/useContributions";

export const useProfile = (username) => {
  const navigate = useNavigate();
  const { currentUser, logout, deleteAccount } = useAuthStore(
    useShallow((s) => ({
      currentUser: s.user,
      logout: s.logout,
      deleteAccount: s.deleteAccount,
    })),
  );

  const isOwnProfile = !username || (currentUser && username === currentUser.username);
  const targetUsername = username || currentUser?.username;

  // 1. Data Hook
  const { profileUser, setProfileUser, loading, userNotFound } = useProfileData(
    username,
    currentUser,
    isOwnProfile,
  );

  // 2. Actions Hook
  const {
    uploadingAvatar,
    uploadingBanner,
    savingProfile,
    handleImageUpload,
    handleSaveProfile,
    handleFollowToggle,
  } = useProfileActions(profileUser, setProfileUser, isOwnProfile);

  // 3. Social Hook
  const { listType, setListType, userList, listLoading, fetchUserList, handleListFollowToggle } =
    useSocialConnections(profileUser, setProfileUser);

  // 4. Contributions Hook
  const { contributionData, loadingContributions } = useContributions(targetUsername);

  // 5. Suggestions
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const fetchSuggestions = useCallback(async () => {
    try {
      const response = await userService.getSuggestedUsers();
      setSuggestedUsers(response.data || []);
    } catch (error) {
      console.error("Failed to fetch suggestions", error);
    }
  }, []);

  useEffect(() => {
    if (isOwnProfile && currentUser?.username) {
      fetchSuggestions();
    }
  }, [isOwnProfile, currentUser?.username, fetchSuggestions]);

  // 6. UI State (Editing / Deleting)
  const [isEditing, setIsEditing] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    bio: "",
  });

  useEffect(() => {
    if (isOwnProfile && currentUser) {
      setEditForm({
        username: currentUser.username || "",
        first_name: currentUser.first_name || "",
        last_name: currentUser.last_name || "",
        bio: currentUser.profile?.bio || "",
      });
    }
  }, [isOwnProfile, currentUser]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const confirmDeleteAccount = async () => {
    try {
      await deleteAccount();
      navigate("/login");
    } catch (err) {
      notify.error(err.message);
    } finally {
      setDeleteDialogOpen(false);
    }
  };

  return {
    currentUser,
    profileUser,
    isOwnProfile,
    loading,
    userNotFound,
    isEditing,
    setIsEditing,
    suggestedUsers,
    editForm,
    setEditForm,
    uploadingAvatar,
    uploadingBanner,
    savingProfile,
    deleteDialogOpen,
    setDeleteDialogOpen,
    contributionData,
    loadingContributions,
    listType,
    setListType,
    userList,
    listLoading,
    handleImageUpload,
    handleSaveProfile: (form) => handleSaveProfile(form, () => setIsEditing(false)),
    handleFollowToggle: () => {
      if (!currentUser) return navigate("/login");
      return handleFollowToggle();
    },
    handleListFollowToggle: (u) => {
      if (!currentUser) return navigate("/login");
      return handleListFollowToggle(u);
    },
    handleLogout,
    confirmDeleteAccount,
    fetchUserList,
  };
};
