import { useState } from "react";
import useAuthStore from "../stores/useAuthStore";
import useUserStore from "../stores/useUserStore";
import { notify } from "../services/notification";

export const useReferral = () => {
  const { user: currentUser } = useAuthStore();
  const { redeemReferral } = useUserStore();

  const [copied, setCopied] = useState(false);
  const [referralCodeInput, setReferralCodeInput] = useState("");
  const [isRedeeming, setIsRedeeming] = useState(false);

  const handleCopyReferral = () => {
    if (currentUser?.profile?.referral_code) {
      navigator.clipboard.writeText(currentUser.profile.referral_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRedeemReferral = async (e) => {
    if (e) e.preventDefault();
    if (!referralCodeInput.trim()) return;

    setIsRedeeming(true);
    try {
      const result = await redeemReferral(referralCodeInput);
      const redeemerXp = result.redeemer_xp_awarded ?? result.xp_awarded;
      const referrerXp = result.referrer_xp_awarded ?? 100;
      notify.success(
        `Referral redeemed! You got +${redeemerXp} and your referrer got +${referrerXp}.`,
      );
      setReferralCodeInput("");
    } catch (error) {
      notify.error("Failed to redeem: " + error.message);
    } finally {
      setIsRedeeming(false);
    }
  };

  return {
    currentUser,
    copied,
    referralCodeInput,
    setReferralCodeInput,
    isRedeeming,
    handleCopyReferral,
    handleRedeemReferral,
  };
};
