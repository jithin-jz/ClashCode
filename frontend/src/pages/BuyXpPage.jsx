import React, { useState } from "react";
import { paymentAPI } from "../services/api";
import { loadRazorpay } from "../utils/loadRazorpay";
import useAuthStore from "../stores/useAuthStore";
import useUserStore from "../stores/useUserStore";
import { toast } from "sonner";
import { Check, Gem, Crown, Flame } from "lucide-react";
import { AnimatePresence, motion as Motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "boneyard-js/react";

const XP_PACKAGES = [
  { amount: 49, xp: 50, label: "Mini", icon: Gem },
  { amount: 99, xp: 100, label: "Starter", icon: Gem },
  { amount: 199, xp: 200, label: "Growth", icon: Gem },
  { amount: 249, xp: 250, label: "Booster", icon: Gem },
  { amount: 499, xp: 500, label: "Pro", icon: Gem, popular: true },
  { amount: 749, xp: 800, label: "Elite", icon: Gem },
  { amount: 999, xp: 1000, label: "Ultimate", icon: Gem, bestValue: true },
  { amount: 1999, xp: 2500, label: "Champion", icon: Gem },
];

const BuyXpPage = () => {
  const [purchasing, setPurchasing] = useState(null);
  const { user } = useAuthStore();
  const { fetchCurrentUser } = useUserStore();

  const handleBuy = async (pkg) => {
    setPurchasing(pkg.amount);

    const isLoaded = await loadRazorpay();
    if (!isLoaded) {
      toast.error("Razorpay SDK failed to load");
      setPurchasing(null);
      return;
    }

    try {
      const { data: orderData } = await paymentAPI.createOrder(pkg.amount);

      const options = {
        key: orderData.key,
        amount: orderData.amount,
        currency: "INR",
        name: "CLASHCODE",
        description: `Add ${pkg.xp} Points`,
        order_id: orderData.order_id,
        handler: async function (response) {
          try {
            await paymentAPI.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            toast.success(`+${pkg.xp} added!`);
            if (fetchCurrentUser) await fetchCurrentUser();
          } catch (verifyError) {
            console.error(verifyError);
            toast.error("Payment verification failed");
          }
        },
        prefill: {
          name: user?.username || "",
          email: user?.email || "",
        },
        theme: { color: "#18181b" },
      };

      const rzp1 = new window.Razorpay(options);
      rzp1.on("payment.failed", (response) => {
        toast.error(response.error.description);
      });
      rzp1.open();
    } catch (error) {
      console.error(error);
      const backendError =
        error?.response?.data?.error ||
        (typeof error?.response?.data === "string"
          ? error.response.data
          : null);
      const serializerError =
        error?.response?.data?.amount?.[0] || error?.response?.data?.detail;
      toast.error(
        backendError || serializerError || "Failed to initiate payment",
      );
    } finally {
      setPurchasing(null);
    }
  };

  return (
    <Skeleton name="buy-xp-page">
      <Motion.div
        key="content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="relative w-full pb-20 sm:pb-0 text-white flex flex-col pt-0 mt-0"
      >
        {/* Main Content */}
        <main className="relative z-10 flex-1 w-full px-4 sm:px-6 lg:px-8 py-6 min-w-0">
          <div className="w-full">
            {/* Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {XP_PACKAGES.map((pkg) => {
                const Icon = pkg.icon;
                const isPurchasing = purchasing === pkg.amount;

                return (
                  <Card
                    key={pkg.amount}
                    className={`
                          rounded-xl overflow-hidden backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] transition-all duration-300 group flex flex-col relative
                          ${
                            pkg.popular
                              ? "bg-gradient-to-br from-[#ffa116]/10 to-[#ffa116]/[0.02] border border-[#ffa116]/30 border-t-[#ffa116]/50 shadow-[0_8px_32px_rgba(255,161,22,0.12)] -translate-y-1"
                              : pkg.bestValue
                                ? "bg-gradient-to-br from-[#00af9b]/10 to-[#00af9b]/[0.02] border border-[#00af9b]/30 border-t-[#00af9b]/50 shadow-[0_8px_32px_rgba(0,175,155,0.08)]"
                                : "bg-[#141414]/70 border border-[#404040]/20 hover:border-[#404040]/50 hover:bg-[#1a1a1a]/80 hover:-translate-y-1 hover:shadow-[0_12px_40px_-15px_rgba(126,163,217,0.2)]"
                          }
                        `}
                  >
                    {/* Badge */}
                    {(pkg.popular || pkg.bestValue) && (
                      <div className="absolute top-3 right-3">
                        <Badge
                          className={`text-[9px] px-1.5 py-0 ${
                            pkg.popular
                              ? "bg-[#ffa116]/10 text-[#ffa116] border-[#ffa116]/20"
                              : "bg-[#00af9b]/10 text-[#00af9b] border-[#00af9b]/20"
                          }`}
                        >
                          {pkg.popular ? "Popular" : "Best Value"}
                        </Badge>
                      </div>
                    )}

                    <CardHeader className="p-5 pb-3">
                      {/* Icon */}
                      <div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${
                          pkg.popular
                            ? "bg-[#ffa116]/10"
                            : pkg.bestValue
                              ? "bg-[#00af9b]/10"
                              : "bg-white/10"
                        }`}
                      >
                        <Icon
                          size={20}
                          className={
                            pkg.popular
                              ? "text-[#ffa116]"
                              : pkg.bestValue
                                ? "text-[#00af9b]"
                                : "text-red-500 fill-red-500/20"
                          }
                        />
                      </div>

                      <CardTitle className="text-base font-medium text-white">
                        {pkg.label}
                      </CardTitle>

                      {/* XP Amount */}
                      <div className="flex items-baseline gap-1 mt-2">
                        <span className="text-3xl font-bold text-white">
                          {pkg.xp.toLocaleString()}
                        </span>
                        <span className="text-sm text-zinc-500 font-medium"></span>
                      </div>
                    </CardHeader>

                    <CardContent className="p-5 pt-2 mt-auto">
                      {/* Bonus indicator */}
                      {pkg.xp > pkg.amount && (
                        <div className="flex items-center gap-1.5 mb-4">
                          <Check size={14} className="text-[#00af9b]" />
                          <span className="text-xs font-medium text-[#00af9b] tracking-tight">
                            +{Math.round((pkg.xp / pkg.amount - 1) * 100)}%
                            bonus
                          </span>
                        </div>
                      )}

                      <Button
                        onClick={() => handleBuy(pkg)}
                        disabled={isPurchasing}
                        className={`
                              w-full h-10 text-sm font-bold tracking-wide transition-all border
                              ${
                                pkg.popular
                                  ? "bg-[#ffa116]/90 border-[#ffa116]/50 text-black hover:bg-[#e69114] hover:border-[#e69114] shadow-[0_4px_12px_rgba(255,161,22,0.2)] hover:shadow-[0_4px_16px_rgba(255,161,22,0.3)]"
                                  : pkg.bestValue
                                    ? "bg-[#00af9b]/90 border-[#00af9b]/50 text-black hover:bg-[#009483] hover:border-[#009483] shadow-[0_4px_12px_rgba(0,175,155,0.2)] hover:shadow-[0_4px_16px_rgba(0,175,155,0.3)]"
                                    : "bg-white text-black border-transparent hover:bg-neutral-200"
                              }
                            `}
                      >
                        {isPurchasing ? (
                          <span className="text-xs font-semibold">
                            Processing...
                          </span>
                        ) : (
                          <span>₹{pkg.amount}</span>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </main>
      </Motion.div>
    </Skeleton>
  );
};

export default BuyXpPage;
