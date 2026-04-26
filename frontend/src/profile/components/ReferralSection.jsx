import React from "react";
import { Gift, Check, Copy, Send } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";

const ReferralSection = ({
  currentUser,
  copied,
  handleCopyReferral,
  referralCodeInput,
  setReferralCodeInput,
  handleRedeemReferral,
  isRedeeming,
}) => {
  const handleShare = () => {
    const text = `Join me on CLASHCODE! Use my referral code ${currentUser?.profile?.referral_code} to get 50 bonus XP: ${window.location.origin}`;
    if (navigator.share) {
      navigator.share({
        title: "Join CLASHCODE",
        text: text,
        url: window.location.origin,
      });
    } else {
      handleCopyReferral();
    }
  };

  return (
    <Card className="bg-[#0d0d0d] border-[#1a1a1a] h-[12.5cm] flex flex-col overflow-hidden group hover:border-[#333] transition-all duration-300">
      {/* Icon/Preview Area - Similar to Theme Cards */}
      <div className="h-40 flex items-center justify-center bg-black border-b border-[#1a1a1a] relative group-hover:bg-[#080808] transition-colors shrink-0">
        <div className="text-neutral-600 group-hover:text-emerald-500 transition-colors duration-500">
          <Gift size={56} strokeWidth={1} />
        </div>

        {/* Referral Status Badge */}
        <div className="absolute top-3 left-3">
          <Badge className="bg-black/40 text-neutral-700 border-[#222]/20 text-[7px] px-1 py-0.5 rounded-sm border font-bold uppercase tracking-[0.2em] font-mono">
            Referral
          </Badge>
        </div>
      </div>

      <CardHeader className="p-4 border-b border-white/5 space-y-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[11px] uppercase tracking-wider font-bold font-mono text-neutral-300">
            Invite Friends
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleShare}
            className="h-7 px-2 text-[9px] font-bold uppercase tracking-wider text-neutral-500 hover:text-emerald-400 hover:bg-emerald-500/5 gap-1.5 transition-all"
          >
            <Send size={11} /> Send Invite
          </Button>
        </div>
        <p className="text-[9px] text-neutral-600 font-bold uppercase tracking-tight">
          Grow the community and earn rewards
        </p>
      </CardHeader>

      <CardContent className="p-4 space-y-4 flex-1">
        {/* Compact Steps */}
        <div className="flex items-center justify-between px-1">
          {[
            { label: "Share Code", color: "text-neutral-500" },
            { label: "Friend Joins", color: "text-neutral-500" },
            { label: "Earn 50 XP", color: "text-emerald-500" },
          ].map((step, i) => (
            <React.Fragment key={i}>
              <div className="text-[10px] font-bold uppercase tracking-tight whitespace-nowrap">
                <span className={step.color}>{step.label}</span>
              </div>
              {i < 2 && <div className="h-px w-4 bg-white/5 mx-1" />}
            </React.Fragment>
          ))}
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <h4 className="text-[10px] text-neutral-500 font-bold uppercase tracking-widest px-1">
              Your Code
            </h4>
            <div className="flex items-center justify-between bg-[#1a1a1a]/30 p-3 rounded-lg border border-white/5 group/code hover:border-white/10 transition-all">
              <code className="text-sm font-mono text-white px-1 tracking-wider">
                {currentUser?.profile?.referral_code}
              </code>
              <button
                onClick={handleCopyReferral}
                className="p-1.5 hover:bg-white/10 rounded transition-colors text-neutral-500 hover:text-white"
              >
                {copied ? (
                  <Check size={14} className="text-[#00af9b]" />
                ) : (
                  <Copy size={14} />
                )}
              </button>
            </div>
          </div>

          {!currentUser?.profile?.is_referred && (
            <div className="space-y-2">
              <h4 className="text-[10px] text-neutral-500 font-bold uppercase tracking-widest px-1">
                Redeem Code
              </h4>
              <form
                onSubmit={handleRedeemReferral}
                className="flex gap-2 w-full"
              >
                <input
                  type="text"
                  value={referralCodeInput}
                  onChange={(e) => setReferralCodeInput(e.target.value)}
                  placeholder="Enter friend's code"
                  className="flex-1 min-w-0 bg-[#1a1a1a]/30 border border-white/5 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/10 placeholder-slate-600 font-mono transition-all"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={isRedeeming || !referralCodeInput}
                  className="bg-white text-black hover:bg-neutral-200 shrink-0 font-bold uppercase text-[10px] px-4 rounded-md h-9"
                >
                  {isRedeeming ? "..." : "Go"}
                </Button>
              </form>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ReferralSection;
