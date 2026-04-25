import { useState, useCallback, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { challengesApi } from "../../services/challengesApi";
import useAuthStore from "../../stores/useAuthStore";
import useChallengesStore from "../../stores/useChallengesStore";
import useWorkspaceStore from "../../stores/useWorkspaceStore";
import { toast } from "sonner";
import { generateLocalCodeReview } from "../../utils/localCodeReview";

/**
 * Custom hook to manage the state and logic for a specific challenge.
 * Encapsulates data fetching, code execution, submission, and AI features.
 */
export const useChallenge = (id) => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const { setUser } = useAuthStore.getState();

  // --- Local UI State ---
  const [code, setCode] = useState("");
  const [output, setOutput] = useState([]);
  const [lastRunPassed, setLastRunPassed] = useState(false);
  const mobileTab = useWorkspaceStore((state) => state.mobileTab);
  const setMobileTab = useWorkspaceStore((state) => state.setMobileTab);
  const [completionData, setCompletionData] = useState(null);

  // AI Assistant State
  const [hint, setHint] = useState("");
  const [hintLevel, setHintLevel] = useState(1);
  const [review, setReview] = useState("");

  // --- Data Fetching ---
  const {
    data: challenge,
    isLoading: isLoadingChallenge,
    error: challengeError,
  } = useQuery({
    queryKey: ["challenge", id],
    queryFn: () => challengesApi.getBySlug(id),
    retry: 1,
    enabled: !!id,
  });

  // Sync initial code when challenge loads
  useEffect(() => {
    if (challenge) {
      setCode(challenge.initial_code || "");
      useChallengesStore.getState().upsertChallenge(challenge);
      
      // Reset workspace state for new challenge
      setHint("");
      setHintLevel(1);
      setReview("");
      setOutput([]);
      setLastRunPassed(false);
      setCompletionData(null);
    }
  }, [challenge]);

  // Helper for AI error messages
  const getAiErrorMessage = useCallback((err, fallbackMessage) => {
    if (err?.response?.status === 504) {
      return "AI processing is taking longer than expected. Please try again.";
    }
    return err?.response?.data?.error || fallbackMessage;
  }, []);

  // --- Mutations ---

  // Run Code Mutation
  const runMutation = useMutation({
    mutationFn: (userCode) => challengesApi.execute(id, userCode),
    onMutate: () => {
      setLastRunPassed(false);
      setOutput([{ type: "log", content: "⚙️ Initializing CLASHCODE Sandbox..." }]);
    },
    onSuccess: (data) => {
      if (data.stdout) setOutput((prev) => [...prev, { type: "log", content: data.stdout }]);
      if (data.stderr) setOutput((prev) => [...prev, { type: "error", content: data.stderr }]);
      if (!data.stdout && !data.stderr) setOutput((prev) => [...prev, { type: "log", content: "Execution finished with no output." }]);

      if (data.passed) {
        setLastRunPassed(true);
        setOutput((prev) => [...prev, { type: "success", content: "✅ Local tests passed! Ready for submission." }]);
      } else {
        setLastRunPassed(false);
        setOutput((prev) => [...prev, { type: "error", content: "⚠️ Local tests failed." }]);
      }
    },
    onError: (err) => {
      const errorMsg = err.response?.data?.error || "Execution failed. Server might be down.";
      setOutput((prev) => [...prev, { type: "error", content: `❌ ${errorMsg}` }]);
    }
  });

  // Submit Code Mutation
  const submitMutation = useMutation({
    mutationFn: (userCode) => challengesApi.submit(id, userCode),
    onMutate: () => {
      setLastRunPassed(false);
      setOutput([{ type: "log", content: "🚀 Initiating CLASHCODE Secure Validation..." }]);
    },
    onSuccess: (result) => {
      // Update XP in auth store
      if (result.xp_earned > 0 && user) {
        setUser({
          ...user,
          profile: {
            ...user.profile,
            xp: (user.profile.xp || 0) + result.xp_earned,
          },
        });
      }

      if (result.status === "completed" || result.status === "already_completed") {
        useChallengesStore.getState().applySubmissionResult(id, result);
        void useChallengesStore.getState().ensureFreshChallenges(0);
        
        // Optimistically update local challenge data
        queryClient.setQueryData(["challenge", id], (old) => old ? {
          ...old,
          status: "COMPLETED",
          stars: Math.max(old.stars || 0, result.stars || 0)
        } : old);

        const starText = "⭐".repeat(result.stars || 0);
        setOutput([{ type: "success", content: `🎉 Challenge Completed! ${starText}` }]);
        if (result.xp_earned > 0) {
          setOutput((prev) => [...prev, { type: "success", content: `💪 Earned: +${result.xp_earned}` }]);
        }
        setCompletionData(result);
      }
    },
    onError: (err) => {
      const errorData = err.response?.data;
      const errorMsg = errorData?.error || "Submission failed. Please try again.";
      setOutput((prev) => [...prev, { type: "error", content: `❌ ${errorMsg}` }]);
      if (errorData?.stderr) setOutput((prev) => [...prev, { type: "error", content: errorData.stderr }]);
      if (errorData?.stdout) setOutput((prev) => [...prev, { type: "log", content: errorData.stdout }]);
    }
  });

  // Get Hint Mutation
  const getHintMutation = useMutation({
    mutationFn: () => challengesApi.getAIHint(id, { user_code: code, hint_level: hintLevel }),
    onSuccess: (data) => {
      setHint(data.hint);
      setHintLevel((prev) => Math.min(prev + 1, 3));
    },
    onError: (err) => {
      const errorMsg = getAiErrorMessage(err, "AI Assistant is currently unavailable.");
      setOutput((prev) => [...prev, { type: "error", content: `🤖 AI Assistant: ${errorMsg}` }]);
    }
  });

  // Purchase Hint Mutation
  const purchaseHintMutation = useMutation({
    mutationFn: () => challengesApi.purchaseAIHint(id),
    onSuccess: async (data) => {
      // Update local XP
      if (data.remaining_xp !== undefined && user) {
        setUser({
          ...user,
          profile: { ...user.profile, xp: data.remaining_xp }
        });
      }

      useChallengesStore.getState().setChallengeHintsPurchased(id, data.hints_purchased);
      
      // Update local challenge query data
      queryClient.setQueryData(["challenge", id], (old) => old ? {
        ...old,
        ai_hints_purchased: data.hints_purchased
      } : old);

      setOutput((prev) => [...prev, { type: "success", content: data.message || `🔓 AI Hint Level ${data.hints_purchased} Unlocked!` }]);
      toast.success("AI Hint Unlocked", { description: `Hint Level ${data.hints_purchased} is now available.` });

      // Automatically fetch the hint after purchase
      if (code) {
        try {
          const hintData = await challengesApi.getAIHint(id, { user_code: code, hint_level: data.hints_purchased });
          setHint(hintData.hint);
          setHintLevel(Math.min(data.hints_purchased + 1, 3));
          setOutput((prev) => [...prev, { type: "success", content: "🤖 AI Hint Generated!" }]);
        } catch (err) {
          console.error("Auto-hint fetch failed:", err);
        }
      }
    },
    onError: (err) => {
      const errorResponse = err.response?.data;
      if (err.response?.status === 402 && errorResponse) {
        setOutput((prev) => [
          ...prev,
          { type: "error", content: `❌ ${errorResponse.error}: ${errorResponse.detail || "Insufficient Balance"}` },
          { type: "log", content: `💰 Balance: ${errorResponse.current_xp} | Required: ${errorResponse.required_xp} | Short by: ${errorResponse.shortage}` },
        ]);
        toast.error("Insufficient Balance", { description: `You need ${errorResponse.shortage} more points.` });
      } else {
        toast.error("Error", { description: errorResponse?.error || "Failed to purchase assistance." });
      }
    }
  });

  // Analyze Code Mutation
  const analyzeMutation = useMutation({
    mutationFn: () => challengesApi.aiAnalyze(id, code),
    onSuccess: (data) => {
      const reviewText = data?.review || data?.analysis || data?.feedback || data?.result || data?.message || (typeof data === "string" ? data : "");
      if (!reviewText) {
        setReview("AI review generated, but response was empty.");
      } else {
        setReview(reviewText);
        toast.success("AI Review Ready");
      }
    },
    onError: (err) => {
      if (err?.response?.status === 404) {
        const fallback = generateLocalCodeReview({ code, challenge });
        setReview(fallback);
        toast.info("Using Local Review", { description: "Backend review endpoint is unavailable." });
      } else {
        const errorMsg = getAiErrorMessage(err, "AI review is currently unavailable.");
        toast.error("AI Review Failed", { description: errorMsg });
        setOutput((prev) => [...prev, { type: "error", content: `🤖 AI Review: ${errorMsg}` }]);
      }
    }
  });

  // Stop current execution
  const stopCode = useCallback(() => {
    runMutation.reset();
    submitMutation.reset();
    setOutput((prev) => [...prev, { type: "error", content: "⛔ Connection Interrupted by User" }]);
  }, [runMutation, submitMutation]);

  return {
    challenge,
    isLoadingChallenge,
    challengeError,
    code,
    setCode,
    output,
    setOutput,
    lastRunPassed,
    mobileTab,
    setMobileTab,
    completionData,
    setCompletionData,
    hint,
    hintLevel,
    review,
    runCode: () => runMutation.mutate(code),
    submitCode: () => submitMutation.mutate(code),
    handleGetHint: () => getHintMutation.mutate(),
    handlePurchaseAIAssist: () => purchaseHintMutation.mutate(),
    handleAnalyzeCode: () => analyzeMutation.mutate(),
    stopCode,
    isRunning: runMutation.isPending,
    isSubmitting: submitMutation.isPending,
    isHintLoading: getHintMutation.isPending || purchaseHintMutation.isPending,
    isReviewLoading: analyzeMutation.isPending,
  };
};
