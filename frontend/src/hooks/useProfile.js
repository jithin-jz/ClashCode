import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useShallow } from "zustand/react/shallow";
import useAuthStore from "../stores/useAuthStore";
import useUserStore from "../stores/useUserStore";
import { notify } from "../services/notification";
import { authAPI } from "../services/api";

export const useProfile = (username) => {
  const navigate = useNavigate();
  const { currentUser, logout, deleteAccount } = useAuthStore(
    useShallow((s) => ({
      currentUser: s.user,
      logout: s.logout,
      deleteAccount: s.deleteAccount,
    })),
  );
  const { updateProfile, followUser, redeemReferral } = useUserStore();

  const isOwnProfile =
    !username || (currentUser && username === currentUser.username);

  const [profileUser, setProfileUser] = useState(() => {
    if (isOwnProfile && currentUser) return currentUser;
    return null;
  });

  const [loading, setLoading] = useState(() => {
    if (isOwnProfile && currentUser) return false;
    return true;
  });

  const [userNotFound, setUserNotFound] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [editForm, setEditForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    bio: "",
  });

  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [contributionData, setContributionData] = useState([]);
  const [loadingContributions, setLoadingContributions] = useState(false);
  const [listType, setListType] = useState(null);
  const [userList, setUserList] = useState([]);
  const [listLoading, setListLoading] = useState(false);

  const { getUserProfile, getFollowers, getFollowing, getSuggestedUsers } =
    authAPI;

  const fetchProfile = useCallback(
    async (targetUsername) => {
      if (!targetUsername) return;
      if (profileUser?.username !== targetUsername && !isOwnProfile) {
        setLoading(true);
        setUserNotFound(false);
      }
      try {
        const response = await getUserProfile(targetUsername);
        setProfileUser(response.data);
      } catch (error) {
        console.error("Failed to fetch profile", error);
        if (profileUser?.username !== targetUsername) {
          setUserNotFound(true);
        }
      } finally {
        setLoading(false);
      }
    },
    [getUserProfile, profileUser?.username, isOwnProfile],
  );

  const fetchContributions = useCallback(
    async (targetUsername) => {
      if (!targetUsername) return;
      const hasData = contributionData.length > 0;
      if (!hasData) setLoadingContributions(true);

      try {
        const { authAPI: api } = await import("../services/api");
        const response = await api.getContributionHistory(targetUsername);
        setContributionData(response.data);
      } catch (error) {
        console.error("Failed to fetch contributions", error);
      } finally {
        setLoadingContributions(false);
      }
    },
    [contributionData.length],
  );

  const fetchSuggestions = useCallback(async () => {
    try {
      if (getSuggestedUsers) {
        const response = await getSuggestedUsers();
        setSuggestedUsers(response.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch suggestions", error);
    }
  }, [getSuggestedUsers]);

  const fetchUserList = async (type) => {
    setListLoading(true);
    setUserList([]);
    setListType(type);
    try {
      const apiCall = type === "followers" ? getFollowers : getFollowing;
      const response = await apiCall(profileUser.username);
      setUserList(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    if (!isOwnProfile && username) {
      fetchProfile(username);
      fetchContributions(username);
    }
  }, [username, isOwnProfile, fetchProfile, fetchContributions]);

  useEffect(() => {
    if (isOwnProfile && currentUser) {
      if (profileUser?.username !== currentUser.username) {
        setProfileUser(currentUser);
      }
      if (loading) setLoading(false);
    }
  }, [isOwnProfile, currentUser, profileUser?.username, loading]);

  useEffect(() => {
    if (isOwnProfile && currentUser) {
      setEditForm((prev) => {
        const next = {
          username: currentUser?.username || "",
          first_name: currentUser?.first_name || "",
          last_name: currentUser?.last_name || "",
          bio: currentUser?.profile?.bio || "",
        };
        if (JSON.stringify(prev) === JSON.stringify(next)) return prev;
        return next;
      });
    }
  }, [isOwnProfile, currentUser]);

  useEffect(() => {
    if (isOwnProfile && currentUser?.username) {
      fetchSuggestions();
      fetchContributions(currentUser.username);
    }
  }, [
    isOwnProfile,
    currentUser?.username,
    fetchSuggestions,
    fetchContributions,
  ]);

  const handleImageUpload = async (event, type) => {
    const file = event.target.files[0];
    if (!file) return;

    if (type === "avatar") setUploadingAvatar(true);
    if (type === "banner") setUploadingBanner(true);

    try {
      const updatedUser = await updateProfile({ type, file }, true);
      if (isOwnProfile) setProfileUser(updatedUser);
      notify.success(
        `${type === "avatar" ? "Profile picture" : "Banner"} updated!`,
      );
    } catch (error) {
      console.error(error);
      notify.error(`Failed to upload ${type}`);
    } finally {
      if (type === "avatar") setUploadingAvatar(false);
      if (type === "banner") setUploadingBanner(false);
    }
  };

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      const updatedUser = await updateProfile(editForm);
      setProfileUser(updatedUser);
      setIsEditing(false);
      notify.success("Profile updated!");
    } catch (error) {
      console.error(error);
      const apiError =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to update profile";
      notify.error(apiError);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleFollowToggle = async () => {
    if (!currentUser) return navigate("/login");
    const targetUsername = profileUser?.username;
    if (!targetUsername) return;

    const previousProfile = profileUser;
    const nextIsFollowing = !previousProfile?.is_following;
    const nextFollowerCount = Math.max(
      0,
      (previousProfile?.followers_count || 0) + (nextIsFollowing ? 1 : -1),
    );

    setProfileUser((prev) =>
      prev
        ? {
            ...prev,
            is_following: nextIsFollowing,
            followers_count: nextFollowerCount,
          }
        : prev,
    );

    try {
      const data = await followUser(targetUsername);
      setProfileUser((prev) =>
        prev
          ? {
              ...prev,
              is_following: data.is_following,
              followers_count: data.follower_count,
            }
          : prev,
      );
    } catch (error) {
      console.error("Failed to toggle follow", error);
      setProfileUser(previousProfile);
      notify.error("Failed to update follow status.");
    }
  };

  const handleListFollowToggle = async (targetUsername) => {
    if (!currentUser) return;
    const previousList = userList;
    const previousProfile = profileUser;
    const targetUser = previousList.find((u) => u.username === targetUsername);
    const optimisticFollowState = targetUser ? !targetUser.is_following : null;

    if (optimisticFollowState !== null) {
      setUserList((prev) =>
        prev.map((u) =>
          u.username === targetUsername
            ? { ...u, is_following: optimisticFollowState }
            : u,
        ),
      );
    }

    if (targetUsername === previousProfile?.username) {
      setProfileUser((prev) =>
        prev
          ? {
              ...prev,
              is_following: !previousProfile?.is_following,
              followers_count: Math.max(
                0,
                (previousProfile?.followers_count || 0) +
                  (previousProfile?.is_following ? -1 : 1),
              ),
            }
          : prev,
      );
    }

    try {
      const data = await followUser(targetUsername);
      setUserList((prev) =>
        prev.map((u) =>
          u.username === targetUsername
            ? { ...u, is_following: data.is_following }
            : u,
        ),
      );
      if (targetUsername === profileUser?.username) {
        setProfileUser((prev) =>
          prev
            ? {
                ...prev,
                is_following: data.is_following,
                followers_count: data.follower_count,
              }
            : prev,
        );
      }
    } catch (error) {
      console.error("Failed to toggle follow in list", error);
      setUserList(previousList);
      if (targetUsername === previousProfile?.username)
        setProfileUser(previousProfile);
      notify.error("Failed to update follow status.");
    }
  };

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
    handleSaveProfile,
    handleFollowToggle,
    handleListFollowToggle,
    handleLogout,
    confirmDeleteAccount,
    fetchUserList,
  };
};
