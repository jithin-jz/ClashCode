import { useState, useEffect, useCallback } from "react";
import { checkInApi } from "../services/checkInApi";

/**
 * Hook to manage daily check-in rewards status and modal state.
 */
export const useDailyReward = (userId) => {
  const [checkInOpen, setCheckInOpen] = useState(false);
  const [hasUnclaimedReward, setHasUnclaimedReward] = useState(false);

  const checkRewardStatus = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await checkInApi.getCheckInStatus();
      setHasUnclaimedReward(!data.checked_in_today);
    } catch (error) {
      console.error("Failed to check reward status:", error);
    }
  }, [userId]);

  useEffect(() => {
    checkRewardStatus();
  }, [checkRewardStatus]);

  const handleClaimReward = useCallback(() => {
    setHasUnclaimedReward(false);
  }, []);

  return {
    checkInOpen,
    setCheckInOpen,
    hasUnclaimedReward,
    handleClaimReward,
    checkRewardStatus
  };
};
