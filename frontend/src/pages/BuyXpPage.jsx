import React, { useState } from "react";
import { paymentAPI } from "../services/api";
import { loadRazorpay } from "../utils/loadRazorpay";
import useAuthStore from "../stores/useAuthStore";
import useUserStore from "../stores/useUserStore";
import { toast } from "sonner";
import { Check, Gem } from "lucide-react";
import { motion as Motion } from "framer-motion";
import { Skeleton } from "boneyard-js/react";

const XP_PACKAGES = [
  { amount: 49, xp: 50, label: "Mini" },
  { amount: 99, xp: 100, label: "Starter" },
  { amount: 199, xp: 200, label: "Growth" },
  { amount: 249, xp: 250, label: "Booster" },
  { amount: 499, xp: 500, label: "Pro", popular: true },
  { amount: 749, xp: 800, label: "Elite" },
  { amount: 999, xp: 1000, label: "Ultimate", bestValue: true },
  { amount: 1999, xp: 2500, label: "Champion" },
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
          } catch {
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
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="min-h-screen bg-black text-white"
      >
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8">
          {/* Header */}
          <div className="pt-8 pb-8">
            <h1 className="text-[22px] sm:text-[28px] font-semibold text-white tracking-tight">
              Get Points
            </h1>
            <p className="text-[13px] sm:text-sm text-neutral-500 mt-1">
              Purchase points to unlock themes, fonts, and effects in the store.
            </p>
          </div>

          {/* Divider */}
          <div className="border-t border-neutral-900 mb-8" />

          {/* Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {XP_PACKAGES.map((pkg) => {
              const isPurchasing = purchasing === pkg.amount;
              const bonusPercent = pkg.xp > pkg.amount
                ? Math.round((pkg.xp / pkg.amount - 1) * 100)
                : 0;

              return (
                <Motion.div
                  key={pkg.amount}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: XP_PACKAGES.indexOf(pkg) * 0.04 }}
                >
                  <button
                    onClick={() => handleBuy(pkg)}
                    disabled={isPurchasing}
                    className={`
                      w-full text-left rounded-lg border p-5 min-h-[180px]
                      flex flex-col justify-between transition-all duration-200 group relative
                      ${pkg.popular
                        ? "bg-neutral-950 border-amber-500/30 hover:border-amber-500/50"
                        : pkg.bestValue
                          ? "bg-neutral-950 border-emerald-500/30 hover:border-emerald-500/50"
                          : "bg-neutral-950 border-neutral-700 hover:border-neutral-500"
                      }
                      ${isPurchasing ? "opacity-60 pointer-events-none" : "hover:bg-neutral-900 active:scale-[0.98]"}
                    `}
                  >
                    {/* Badge */}
                    {(pkg.popular || pkg.bestValue) && (
                      <span className={`absolute top-3 right-3 text-[9px] font-medium px-2 py-0.5 rounded ${
                        pkg.popular
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-emerald-500/10 text-emerald-400"
                      }`}>
                        {pkg.popular ? "Popular" : "Best Value"}
                      </span>
                    )}

                    {/* Top */}
                    <div>
                      <p className="text-[11px] font-medium text-neutral-500 mb-1">
                        {pkg.label}
                      </p>
                      <p className="text-[28px] font-semibold text-white leading-none tabular-nums">
                        {pkg.xp.toLocaleString()}
                      </p>
                      <p className="text-[11px] text-neutral-600 mt-1">points</p>
                    </div>

                    {/* Bottom */}
                    <div className="mt-4 space-y-2">
                      {bonusPercent > 0 && (
                        <div className="flex items-center gap-1.5">
                          <Check size={12} className="text-emerald-400" />
                          <span className="text-[11px] text-emerald-400 font-medium">
                            +{bonusPercent}% bonus
                          </span>
                        </div>
                      )}

                      <div className={`
                        w-full h-9 rounded-md flex items-center justify-center text-[13px] font-medium transition-colors
                        ${pkg.popular
                          ? "bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20"
                          : pkg.bestValue
                            ? "bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20"
                            : "bg-white/5 text-white group-hover:bg-white/10"
                        }
                      `}>
                        {isPurchasing ? "Processing..." : `₹${pkg.amount}`}
                      </div>
                    </div>
                  </button>
                </Motion.div>
              );
            })}
          </div>
        </div>
      </Motion.div>
    </Skeleton>
  );
};

export default BuyXpPage;
