import { useState } from "react";
import { userService } from "../../services/api/userService";
import useUserStore from "../../stores/useUserStore";
import { notify } from "../../services/notification";

export const useSocialConnections = (profileUser, setProfileUser) => {
  const { followUser } = useUserStore();
  
  const [listType, setListType] = useState(null);
  const [userList, setUserList] = useState([]);
  const [listLoading, setListLoading] = useState(false);

  const fetchUserList = async (type) => {
    setListLoading(true);
    setUserList([]);
    setListType(type);
    try {
      const apiCall = type === "followers" ? userService.getFollowers : userService.getFollowing;
      const response = await apiCall(profileUser.username);
      setUserList(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setListLoading(false);
    }
  };

  const handleListFollowToggle = async (targetUsername) => {
    const previousList = userList;
    const previousProfile = profileUser;
    
    // Optimistic Update
    setUserList((prev) =>
      prev.map((u) => (u.username === targetUsername ? { ...u, is_following: !u.is_following } : u))
    );

    if (targetUsername === profileUser?.username) {
      setProfileUser((prev) => ({
        ...prev,
        is_following: !prev.is_following,
        followers_count: Math.max(0, (prev.followers_count || 0) + (prev.is_following ? -1 : 1)),
      }));
    }

    try {
      const data = await followUser(targetUsername);
      setUserList((prev) =>
        prev.map((u) => (u.username === targetUsername ? { ...u, is_following: data.is_following } : u))
      );
      
      if (targetUsername === profileUser?.username) {
        setProfileUser((prev) => ({
          ...prev,
          is_following: data.is_following,
          followers_count: data.follower_count,
        }));
      }
    } catch (error) {
      console.error("Failed to toggle follow in list", error);
      setUserList(previousList);
      if (targetUsername === previousProfile?.username) setProfileUser(previousProfile);
      notify.error("Failed to update follow status.");
    }
  };

  return {
    listType,
    setListType,
    userList,
    listLoading,
    fetchUserList,
    handleListFollowToggle,
  };
};
