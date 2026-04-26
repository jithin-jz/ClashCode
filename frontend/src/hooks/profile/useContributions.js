import { useState, useCallback, useEffect } from "react";
import { userService } from "../../services/api/userService";

export const useContributions = (username) => {
  const [contributionData, setContributionData] = useState([]);
  const [loadingContributions, setLoadingContributions] = useState(false);

  const fetchContributions = useCallback(async (targetUsername) => {
    if (!targetUsername) return;
    setLoadingContributions(true);

    try {
      const response = await userService.getContributionHistory(targetUsername);
      setContributionData(response.data);
    } catch (error) {
      console.error("Failed to fetch contributions", error);
    } finally {
      setLoadingContributions(false);
    }
  }, []);

  useEffect(() => {
    if (username) {
      fetchContributions(username);
    }
  }, [username, fetchContributions]);

  return { contributionData, loadingContributions };
};
