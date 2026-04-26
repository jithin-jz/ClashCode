import { useState, useEffect, useCallback } from "react";
import { userService } from "../../services/api/userService";

export const useProfileData = (username, currentUser, isOwnProfile) => {
  const [profileUser, setProfileUser] = useState(() => {
    if (isOwnProfile && currentUser) return currentUser;
    return null;
  });

  const [loading, setLoading] = useState(() => {
    if (isOwnProfile && currentUser) return false;
    return true;
  });

  const [userNotFound, setUserNotFound] = useState(false);

  const fetchProfile = useCallback(
    async (targetUsername) => {
      if (!targetUsername) return;
      
      // Don't show loading if we already have the user and it's them
      if (profileUser?.username !== targetUsername && !isOwnProfile) {
        setLoading(true);
        setUserNotFound(false);
      }

      try {
        const response = await userService.getUserProfile(targetUsername);
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
    [profileUser?.username, isOwnProfile]
  );

  useEffect(() => {
    if (!isOwnProfile && username) {
      fetchProfile(username);
    }
  }, [username, isOwnProfile, fetchProfile]);

  useEffect(() => {
    if (isOwnProfile && currentUser) {
      if (profileUser?.username !== currentUser.username) {
        setProfileUser(currentUser);
      }
      setLoading(false);
    }
  }, [isOwnProfile, currentUser, profileUser?.username]);

  return { profileUser, setProfileUser, loading, userNotFound };
};
