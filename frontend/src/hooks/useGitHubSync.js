import { useState, useEffect, useCallback } from "react";
import githubSyncService from "../services/api/githubSyncService";

/**
 * Hook to manage GitHub Sync connection state and actions.
 *
 * Usage:
 *   const { connection, isLoading, connect, disconnect, toggle, history } = useGitHubSync();
 */
export function useGitHubSync() {
  const [connection, setConnection] = useState(null);
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current connection status
  const fetchConnection = useCallback(async () => {
    try {
      setIsLoading(true);
      const { data } = await githubSyncService.getConnection();
      setConnected(data.connected);
      setConnection(data.connection);
      setError(null);
    } catch (err) {
      setError("Failed to fetch GitHub connection status.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch push history
  const fetchHistory = useCallback(async () => {
    try {
      const { data } = await githubSyncService.getHistory();
      setHistory(data.results || []);
    } catch {
      // Silently fail — history is non-critical
    }
  }, []);

  // Initialize OAuth flow
  const initiateConnect = useCallback(async () => {
    try {
      const { data } = await githubSyncService.getConnectUrl();
      // Redirect user to GitHub
      window.location.href = data.url;
    } catch (err) {
      setError("Failed to initiate GitHub connection.");
    }
  }, []);

  // Complete OAuth flow (call from callback page)
  const completeConnect = useCallback(async (code) => {
    try {
      setIsLoading(true);
      const { data } = await githubSyncService.connect(code);
      setConnected(true);
      setConnection(data.connection);
      setError(null);
      return data;
    } catch (err) {
      const msg = err?.response?.data?.error || "Failed to connect GitHub.";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Disconnect
  const disconnect = useCallback(async () => {
    try {
      await githubSyncService.disconnect();
      setConnected(false);
      setConnection(null);
      setHistory([]);
    } catch (err) {
      setError("Failed to disconnect GitHub.");
    }
  }, []);

  // Toggle enable/disable
  const toggle = useCallback(async () => {
    if (!connection) return;
    try {
      const { data } = await githubSyncService.updateConnection({
        is_enabled: !connection.is_enabled,
      });
      setConnection(data.connection);
    } catch (err) {
      setError("Failed to update sync setting.");
    }
  }, [connection]);

  // Update repo name
  const updateRepoName = useCallback(async (repoName) => {
    try {
      const { data } = await githubSyncService.updateConnection({
        repo_name: repoName,
      });
      setConnection(data.connection);
    } catch (err) {
      const msg = err?.response?.data?.repo_name?.[0] || "Invalid repo name.";
      setError(msg);
    }
  }, []);

  // Retry a failed push
  const retryPush = useCallback(async (logId) => {
    try {
      await githubSyncService.retryPush(logId);
      // Refresh history after retry
      await fetchHistory();
    } catch (err) {
      setError("Failed to retry push.");
    }
  }, [fetchHistory]);

  // Load on mount
  useEffect(() => {
    fetchConnection();
  }, [fetchConnection]);

  return {
    // State
    connection,
    connected,
    history,
    isLoading,
    error,

    // Actions
    initiateConnect,
    completeConnect,
    disconnect,
    toggle,
    updateRepoName,
    retryPush,
    fetchHistory,
    fetchConnection,
  };
}
