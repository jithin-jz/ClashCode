import { useMemo, useCallback, memo } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  Sparkles,
  Type,
  Palette,
  PartyPopper,
  Gem,
  ShoppingBag,
} from "lucide-react";
import * as LucideIcons from "lucide-react";
import { motion as Motion, AnimatePresence } from "framer-motion";
import { Skeleton } from "boneyard-js/react";
import { MarketplaceSkeleton } from "../bones/PageSkeletons";
import { useMarketplace } from "../hooks/useMarketplace";
import { useReferral } from "../hooks/useReferral";
import ReferralSection from "../profile/components/ReferralSection";

const CATEGORIES = [
  { id: "THEME", label: "Themes", icon: Palette },
  { id: "FONT", label: "Fonts", icon: Type },
  { id: "EFFECT", label: "Effects", icon: Sparkles },
  { id: "VICTORY", label: "Victory", icon: PartyPopper },
];

const MarketplacePage = memo(() => {
  const navigate = useNavigate();
  const {
    user,
    items,
    isLoading,
    isMutating,
    activeMutationItemId,
    activeCategory,
    setActiveCategory,
    handleBuy,
    handleEquip,
    handleStickyUnequip,
  } = useMarketplace();

  const referral = useReferral();

  const filteredItems = useMemo(() => {
    return items.filter((item) => item.category === activeCategory);
  }, [items, activeCategory]);

  const isItemActive = useCallback(
    (item) => {
      if (!user?.profile) return false;
      if (item.category === "THEME")
        return user.profile.active_theme === item.item_data?.theme_key;
      if (item.category === "FONT")
        return user.profile.active_font === item.item_data?.font_family;
      if (item.category === "EFFECT")
        return (
          user.profile.active_effect === item.item_data?.effect_key ||
          user.profile.active_effect === item.item_data?.effect_type
        );
      if (item.category === "VICTORY")
        return (
          user.profile.active_victory === item.item_data?.victory_key ||
          user.profile.active_victory === item.item_data?.animation_type
        );
      return false;
    },
    [user],
  );

  const renderIcon = useCallback((iconName) => {
    const Icon = LucideIcons[iconName] || LucideIcons.Package;
    return <Icon size={28} strokeWidth={1.5} />;
  }, []);

  return (
    <Skeleton
      name="marketplace-page"
      loading={isLoading && items.length === 0}
      fallback={<MarketplaceSkeleton />}
    >
      <div className="min-h-screen bg-black text-white">
        {/* Sticky Category Bar */}
        <div className="sticky top-14 z-20 border-b border-neutral-900 bg-black/95 backdrop-blur-md">
          <div className="max-w-[1200px] mx-auto px-6 sm:px-8">
            <div className="flex items-center gap-3 py-3">
              <button
                onClick={() => navigate(-1)}
                className="h-8 w-8 flex items-center justify-center rounded-md text-neutral-500 hover:text-white hover:bg-neutral-900 transition-colors shrink-0"
              >
                <ArrowLeft size={15} />
              </button>

              <div className="w-px h-4 bg-neutral-800 shrink-0" />

              <div className="flex items-center gap-1 flex-1 overflow-x-auto">
                {CATEGORIES.map((cat) => {
                  const isActive = activeCategory === cat.id;
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setActiveCategory(cat.id)}
                      className={`
                        flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium transition-all whitespace-nowrap
                        ${isActive
                          ? "bg-neutral-900 text-white"
                          : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900/50"
                        }
                      `}
                    >
                      <Icon size={13} />
                      <span>{cat.label}</span>
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => navigate("/buy-xp")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-neutral-800 text-neutral-400 hover:text-white hover:border-neutral-600 transition-colors shrink-0"
              >
                <Gem size={12} className="text-neutral-500" />
                <span className="text-[12px] font-medium tabular-nums">
                  {(user?.profile?.xp || 0).toLocaleString()}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-[1200px] mx-auto px-6 sm:px-8 pt-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Items Grid */}
            <div className="lg:col-span-9 order-2 lg:order-1">
              {filteredItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 border border-neutral-900 border-dashed rounded-xl">
                  <ShoppingBag size={36} className="text-neutral-700 mb-3" />
                  <p className="text-[13px] text-neutral-600">No items in this category</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  <AnimatePresence mode="popLayout">
                    {filteredItems.map((item) => {
                      const isActive = isItemActive(item);
                      const isOwned = item.is_owned;
                      const canAfford = user?.profile?.xp >= item.cost;
                      const isMutatingThis =
                        isMutating && activeMutationItemId === item.id;

                      return (
                        <Motion.div
                          key={item.id}
                          layout
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -6 }}
                          transition={{ duration: 0.2 }}
                          className="flex"
                        >
                          <div
                            className={`
                              w-full rounded-lg border flex flex-col transition-all duration-200 group
                              ${isActive
                                ? "bg-neutral-950 border-emerald-500/30"
                                : "bg-neutral-950 border-neutral-800 hover:border-neutral-600"
                              }
                            `}
                          >
                            {/* Icon Preview */}
                            <div className={`h-24 flex items-center justify-center border-b transition-colors ${
                              isActive
                                ? "border-emerald-500/10 bg-emerald-500/[0.02]"
                                : "border-neutral-900 group-hover:bg-neutral-900/30"
                            }`}>
                              <div className={`transition-transform duration-300 group-hover:scale-110 ${
                                isActive ? "text-emerald-400" : "text-neutral-500"
                              }`}>
                                {renderIcon(item.icon_name)}
                              </div>
                            </div>

                            {/* Info */}
                            <div className="p-3 flex-1 flex flex-col">
                              <div className="flex items-start justify-between gap-2">
                                <h3 className={`text-[12px] font-medium leading-snug ${
                                  isActive ? "text-emerald-400" : "text-white"
                                }`}>
                                  {item.name}
                                </h3>
                                {isOwned && (
                                  <span className={`text-[8px] font-medium px-1.5 py-0.5 rounded shrink-0 ${
                                    isActive
                                      ? "bg-emerald-500/10 text-emerald-400"
                                      : "bg-neutral-800 text-neutral-500"
                                  }`}>
                                    {isActive ? "Active" : "Owned"}
                                  </span>
                                )}
                              </div>
                              <p className="text-[10px] text-neutral-600 mt-1 line-clamp-2 leading-relaxed">
                                {item.description}
                              </p>
                            </div>

                            {/* Action */}
                            <div className="p-3 pt-0">
                              {isOwned ? (
                                <button
                                  onClick={() =>
                                    isActive
                                      ? handleStickyUnequip(item.category)
                                      : handleEquip(item)
                                  }
                                  disabled={isMutatingThis}
                                  className={`
                                    w-full h-8 rounded-md text-[11px] font-medium transition-colors
                                    ${isActive
                                      ? "border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/5"
                                      : "bg-neutral-900 text-neutral-400 hover:text-white hover:bg-neutral-800"
                                    }
                                  `}
                                >
                                  {isMutatingThis ? "..." : isActive ? "Unequip" : "Equip"}
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleBuy(item)}
                                  disabled={!canAfford || isMutatingThis}
                                  className={`
                                    w-full h-8 rounded-md text-[11px] font-medium flex items-center justify-center gap-1.5 transition-colors
                                    ${canAfford
                                      ? "bg-white text-black hover:bg-neutral-200 active:scale-[0.98]"
                                      : "bg-neutral-900 text-neutral-600 cursor-not-allowed"
                                    }
                                  `}
                                >
                                  {isMutatingThis ? "..." : (
                                    <>
                                      <Gem size={10} className="text-neutral-500" />
                                      {item.cost.toLocaleString()}
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                        </Motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-3 order-1 lg:order-2">
              <ReferralSection {...referral} />
            </div>
          </div>
        </div>
      </div>
    </Skeleton>
  );
});

MarketplacePage.displayName = "MarketplacePage";

export default MarketplacePage;
