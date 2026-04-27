import { useState, useCallback, useEffect, useRef } from "react";
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
  const [streamingHint, setStreamingHint] = useState("");
  const [hintLevel, setHintLevel] = useState(1);
  const [review, setReview] = useState("");
  const [isHintStreaming, setIsHintStreaming] = useState(false);

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

  const initializedChallengeId = useRef(null);

  // Sync initial code when challenge loads
  useEffect(() => {
    if (challenge && initializedChallengeId.current !== challenge.id) {
      setCode(challenge.user_code || challenge.initial_code || "");
      useChallengesStore.getState().upsertChallenge(challenge);

      // Reset workspace state for new challenge
      setHint("");
      setHintLevel(1);
      setReview("");
      setOutput([]);
      setLastRunPassed(false);
      setCompletionData(null);

      initializedChallengeId.current = challenge.id;
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
      setOutput([]);
    },
    onSuccess: (data) => {
      if (data.stdout)
        setOutput((prev) => [...prev, { type: "log", content: data.stdout }]);

      // Only show stderr if it's NOT a security error
      if (data.stderr) {
        const isSecurityError =
          data.stderr.includes("Security Error") ||
          data.stderr.includes("Security Violation");
        if (isSecurityError) {
          // Log security errors to console only, not in UI
          console.error("🔒 Code Security Error:", data.stderr);
          setOutput((prev) => [
            ...prev,
            {
              type: "error",
              content:
                "❌ Code execution blocked. Check browser console for details.",
            },
          ]);
        } else {
          setOutput((prev) => [
            ...prev,
            { type: "error", content: data.stderr },
          ]);
        }
      }

      if (!data.stdout && !data.stderr)
        setOutput((prev) => [
          ...prev,
          { type: "log", content: "Execution finished with no output." },
        ]);

      if (data.passed) {
        setLastRunPassed(true);
        setOutput((prev) => [
          ...prev,
          {
            type: "success",
            content: "✅ Local tests passed! Ready for submission.",
          },
        ]);
      } else {
        setLastRunPassed(false);
        setOutput((prev) => [
          ...prev,
          { type: "error", content: "⚠️ Local tests failed." },
        ]);
      }
    },
    onError: (err) => {
      const errorMsg =
        err.response?.data?.error || "Execution failed. Server might be down.";
      console.error("❌ Code Execution Error:", errorMsg);
      setOutput((prev) => [
        ...prev,
        {
          type: "error",
          content: "❌ Execution failed. Check browser console for details.",
        },
      ]);
    },
  });

  // Submit Code Mutation
  const submitMutation = useMutation({
    mutationFn: (userCode) => challengesApi.submit(id, userCode),
    onMutate: () => {
      // Don't reset passed status during submission to maintain UI feedback
      // setLastRunPassed(false); 
      setOutput([
        {
          type: "log",
          content: "🚀 Initiating CLASHCODE Secure Validation...",
        },
      ]);
    },
    onSuccess: (result) => {
      // Update XP in auth store with latest state to prevent reverting concurrent changes
      if (result.xp_earned > 0) {
        const latestUser = useAuthStore.getState().user;
        if (latestUser) {
          setUser({
            ...latestUser,
            profile: {
              ...latestUser.profile,
              xp: (latestUser.profile.xp || 0) + result.xp_earned,
            },
          });
        }
      }

      if (
        result.status === "completed" ||
        result.status === "already_completed"
      ) {
        useChallengesStore.getState().applySubmissionResult(id, result);
        void useChallengesStore.getState().ensureFreshChallenges(0);

        // Optimistically update local challenge data including the final code
        queryClient.setQueryData(["challenge", id], (old) =>
          old
            ? {
                ...old,
                status: "COMPLETED",
                stars: Math.max(old.stars || 0, result.stars || 0),
                user_code: code, // Persist the submitted code locally
                is_completed: true
              }
            : old,
        );

        const starText = "⭐".repeat(result.stars || 0);
        setOutput([
          { type: "success", content: `🎉 Challenge Completed! ${starText}` },
        ]);
        if (result.xp_earned > 0) {
          setOutput((prev) => [
            ...prev,
            { type: "success", content: `💪 Earned: +${result.xp_earned}` },
          ]);
        }
        setCompletionData(result);
      }
    },
    onError: (err) => {
      const errorData = err.response?.data;
      const errorMsg =
        errorData?.error || "Submission failed. Please try again.";
      setOutput((prev) => [
        ...prev,
        { type: "error", content: `❌ ${errorMsg}` },
      ]);
      if (errorData?.stderr)
        setOutput((prev) => [
          ...prev,
          { type: "error", content: errorData.stderr },
        ]);
      if (errorData?.stdout)
        setOutput((prev) => [
          ...prev,
          { type: "log", content: errorData.stdout },
        ]);
    },
  });

  // Get Hint Mutation
  const getHintMutation = useMutation({
    mutationFn: ({ level, code: customCode } = {}) =>
      challengesApi.getAIHint(id, {
        user_code: customCode || code,
        hint_level: level || hintLevel,
      }),
    onSuccess: (data) => {
      setHint(data.hint);
      setHintLevel((prev) => Math.min(prev + 1, 3));
    },
    onError: (err) => {
      const errorMsg = getAiErrorMessage(
        err,
        "AI Assistant is currently unavailable.",
      );
      setOutput((prev) => [
        ...prev,
        { type: "error", content: `🤖 AI Assistant: ${errorMsg}` },
      ]);
    },
  });

  // Purchase Hint Mutation
  const purchaseHintMutation = useMutation({
    mutationFn: () => challengesApi.purchaseAIHint(id),
    onSuccess: (data) => {
      // Update local XP with latest state to prevent race conditions
      const latestUser = useAuthStore.getState().user;
      if (data.remaining_xp !== undefined && latestUser) {
        setUser({
          ...latestUser,
          profile: { ...latestUser.profile, xp: data.remaining_xp },
        });
      }

      useChallengesStore
        .getState()
        .setChallengeHintsPurchased(id, data.hints_purchased);

      // Update local challenge query data
      queryClient.setQueryData(["challenge", id], (old) =>
        old
          ? {
              ...old,
              ai_hints_purchased: data.hints_purchased,
            }
          : old,
      );

      setOutput((prev) => [
        ...prev,
        {
          type: "success",
          content:
            data.message ||
            `🔓 AI Hint Level ${data.hints_purchased} Unlocked!`,
        },
      ]);
      toast.success("AI Hint Unlocked", {
        description: `Hint Level ${data.hints_purchased} is now available.`,
      });

      // Automatically fetch the hint after purchase
      if (code) {
        getHintMutation.mutate({ level: data.hints_purchased, code });
      } else {
        setHintLevel(Math.min(data.hints_purchased + 1, 3));
      }
    },
    onError: (err) => {
      const errorResponse = err.response?.data;
      const errorMessage = errorResponse?.error || "Failed to purchase assistance.";

      setOutput((prev) => [
        ...prev,
        {
          type: "error",
          content: `❌ ${errorMessage}`,
        },
      ]);

      if (err.response?.status === 402) {
        toast.error("Insufficient Balance", {
          description: errorMessage,
        });
      } else {
        toast.error("Error", {
          description: errorMessage,
        });
      }
    },
  });

  // Analyze Code Mutation
  const analyzeMutation = useMutation({
    mutationFn: () => challengesApi.aiAnalyze(id, code),
    onSuccess: (data) => {
      const reviewText =
        data?.review ||
        data?.analysis ||
        data?.feedback ||
        data?.result ||
        data?.message ||
        (typeof data === "string" ? data : "");
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
        toast.info("Using Local Review", {
          description: "Backend review endpoint is unavailable.",
        });
      } else {
        const errorMsg = getAiErrorMessage(
          err,
          "AI review is currently unavailable.",
        );
        toast.error("AI Review Failed", { description: errorMsg });
        setOutput((prev) => [
          ...prev,
          { type: "error", content: `🤖 AI Review: ${errorMsg}` },
        ]);
      }
    },
  });

  // Stop current execution
  const stopCode = useCallback(() => {
    runMutation.reset();
    submitMutation.reset();
    setOutput((prev) => [
      ...prev,
      { type: "error", content: "⛔ Connection Interrupted by User" },
    ]);
  }, [runMutation, submitMutation]);

  const handleGetHintStream = useCallback(async (level) => {
    const targetLevel = level || hintLevel;
    setIsHintStreaming(true);
    setStreamingHint("");
    
    try {
      const response = await fetch(`${import.meta.env.VITE_AI_SERVICE_URL}/hints/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Internal API keys would go here if not handled by a proxy
        },
        body: JSON.stringify({
          challenge_slug: id,
          user_code: code,
          hint_level: targetLevel,
          user_xp: user?.profile?.xp || 0
        })
      });

      if (!response.ok) throw new Error("Hint stream failed");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedHint = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.replace('data: ', '');
            if (content) {
              accumulatedHint += content;
              setStreamingHint(accumulatedHint);
            }
          }
        }
      }

      setHint(accumulatedHint);
      setHintLevel((prev) => Math.min(prev + 1, 3));
    } catch (err) {
      console.error("Hint streaming error:", err);
      toast.error("AI stream interrupted");
    } finally {
      setIsHintStreaming(false);
      setStreamingHint("");
    }
  }, [id, code, hintLevel, user?.profile?.xp]);

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
    streamingHint,
    hintLevel,
    review,
    runCode: () => runMutation.mutate(code),
    submitCode: () => submitMutation.mutate(code),
    handleGetHint: handleGetHintStream,
    handlePurchaseAIAssist: () => purchaseHintMutation.mutate(),
    handleAnalyzeCode: () => analyzeMutation.mutate(),
    stopCode,
    isRunning: runMutation.isPending,
    isSubmitting: submitMutation.isPending,
    isHintLoading: isHintStreaming || purchaseHintMutation.isPending,
    isReviewLoading: analyzeMutation.isPending,
  };
};
