import { useMemo, useCallback, memo } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Lock,
  Check,
  Sparkles,
  Type,
  Palette,
  Package,
  PartyPopper,
  Gem,
  ShoppingBag,
} from "lucide-react";
import * as LucideIcons from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { motion as Motion, AnimatePresence } from "framer-motion";
import { Skeleton } from "boneyard-js/react";
import { MarketplaceSkeleton } from "../bones/PageSkeletons";
import { useMarketplace } from "../hooks/useMarketplace";
import { useReferral } from "../hooks/useReferral";
import ReferralSection from "../profile/components/ReferralSection";

const CATEGORIES = [
  {
    id: "THEME",
    label: "Themes",
    icon: Palette,
    color: "text-indigo-500",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/20",
  },
  {
    id: "FONT",
    label: "Fonts",
    icon: Type,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    id: "EFFECT",
    label: "Effects",
    icon: Sparkles,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  {
    id: "VICTORY",
    label: "Victory",
    icon: PartyPopper,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
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
    return <Icon size={32} />;
  }, []);

  return (
    <Skeleton
      name="marketplace-page"
      loading={isLoading && items.length === 0}
      fallback={<MarketplaceSkeleton />}
    >
      <div className="relative w-full pb-20 sm:pb-0 text-white flex flex-col pt-0 mt-0">
        {/* Controls & Category Tabs */}
        <div className="sticky top-14 z-20 border-b border-[#1e1e1e] bg-[#0a0a0a]/92 backdrop-blur-xl">
          <div className="w-full px-4 sm:px-8 lg:px-10 min-w-0">
            <div className="flex items-center gap-2 sm:gap-4 py-2 sm:py-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
                className="h-8 w-8 text-neutral-600 hover:text-white hover:bg-[#1c1c1c] shrink-0 -ml-1"
              >
                <ArrowLeft size={16} />
              </Button>

              <div className="w-px h-4 bg-[#222] shrink-0 hidden sm:block" />

              <div className="flex items-center gap-1 sm:gap-1.5 flex-1 overflow-x-auto scrollbar-hide">
                {CATEGORIES.map((cat) => {
                  const isActive = activeCategory === cat.id;
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setActiveCategory(cat.id)}
                      className={`
                      flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all border font-mono flex-1 sm:flex-none sm:whitespace-nowrap
                      ${
                        isActive
                          ? "bg-[#161616] text-white border-[#333]"
                          : "text-neutral-500 border-transparent hover:text-neutral-300 hover:bg-[#111] hover:border-[#1a1a1a]"
                      }
                    `}
                    >
                      <Icon size={12} />
                      <span className="hidden sm:inline">{cat.label}</span>
                    </button>
                  );
                })}
              </div>

              <div className="shrink-0 ml-1">
                <button
                  onClick={() => navigate("/buy-xp")}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0d0d0d] rounded-md border border-white/10 hover:bg-[#141414] hover:border-white/20 transition-colors"
                >
                  <Gem size={13} className="text-red-500 fill-red-500/20" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Layout with Sidebar */}
        <main className="relative z-10 w-full px-4 sm:px-8 lg:px-10 py-0">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch min-h-[calc(100vh-8rem)]">
            {/* Main Items Grid */}
            <div className="lg:col-span-9 order-2 lg:order-1 py-4">
              {filteredItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border border-dashed border-white/5 rounded-2xl bg-white/[0.01]">
                  <ShoppingBag size={48} className="text-neutral-700 mb-4" />
                  <p className="text-neutral-500 font-medium">No items found</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
                          initial={{ opacity: 0, scale: 0.98 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.98 }}
                          transition={{ duration: 0.2 }}
                        >
                          <Card
                            className={`rounded-lg overflow-hidden transition-all duration-300 group flex flex-col h-full bg-[#0d0d0d] border border-[#1a1a1a] ${
                              isActive
                                ? "border-emerald-500/30"
                                : "hover:border-[#333]"
                            }`}
                          >
                            <div
                              className={`h-28 flex items-center justify-center border-b transition-all duration-500 relative shrink-0 ${
                                isActive
                                  ? "bg-emerald-500/[0.03] border-emerald-500/10"
                                  : "bg-black border-[#1a1a1a] group-hover:bg-[#050505]"
                              }`}
                            >
                              <div
                                className={`transition-all duration-500 transform group-hover:scale-110 ${
                                  isActive
                                    ? "text-emerald-500"
                                    : CATEGORIES.find(
                                        (c) => c.id === item.category,
                                      )?.color || "text-neutral-600"
                                }`}
                              >
                                {renderIcon(item.icon_name)}
                              </div>

                              <div className="absolute top-2 right-2 flex gap-1.5">
                                {isOwned && (
                                  <Badge
                                    className={`text-[8px] px-1.5 py-0.5 rounded-sm border font-bold uppercase tracking-[0.1em] font-mono ${isActive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-[#1a1a1a] text-neutral-500 border-[#222]"}`}
                                  >
                                    {isActive ? "Active" : "Owned"}
                                  </Badge>
                                )}
                              </div>

                              <Badge
                                className={`absolute top-2 left-2 text-[7px] px-1.5 py-0.5 rounded-sm border font-bold uppercase tracking-[0.2em] font-mono transition-colors ${
                                  isActive
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                    : `${CATEGORIES.find((c) => c.id === item.category)?.bg} ${CATEGORIES.find((c) => c.id === item.category)?.color} ${CATEGORIES.find((c) => c.id === item.category)?.border}`
                                }`}
                              >
                                {item.category}
                              </Badge>
                            </div>

                            <div className="flex flex-col flex-1 p-3">
                              <h3
                                className={`text-[11px] uppercase tracking-wider font-bold truncate font-mono ${isActive ? "text-emerald-400" : "text-neutral-300"}`}
                              >
                                {item.name}
                              </h3>
                              <p className="text-[9px] mt-1 line-clamp-2 leading-snug text-neutral-500 font-bold uppercase tracking-tight">
                                {item.description}
                              </p>
                            </div>

                            <div className="p-3.5 pt-0 mt-auto">
                              {isOwned ? (
                                <Button
                                  className={`w-full h-8 text-[9px] font-bold uppercase tracking-widest transition-all rounded-md font-mono ${
                                    isActive
                                      ? "bg-transparent border border-emerald-500/20 text-emerald-500 hover:bg-emerald-500/5 shadow-none"
                                      : "bg-[#111] border border-[#222] text-neutral-500 hover:bg-[#161616] hover:text-neutral-200"
                                  }`}
                                  disabled={isMutatingThis}
                                  onClick={() =>
                                    isActive
                                      ? handleStickyUnequip(item.category)
                                      : handleEquip(item)
                                  }
                                >
                                  {isMutatingThis
                                    ? "..."
                                    : isActive
                                      ? "Unequip"
                                      : "Equip"}
                                </Button>
                              ) : (
                                <Button
                                  className={`w-full h-8 text-[10px] font-bold tracking-widest transition-all border rounded-md font-mono shadow-sm ${
                                    canAfford
                                      ? "bg-white text-black border-transparent hover:bg-neutral-200 active:scale-95"
                                      : "bg-[#0d0d0d] text-neutral-200 border-[#1a1a1a] cursor-not-allowed"
                                  }`}
                                  disabled={!canAfford || isMutatingThis}
                                  onClick={() => handleBuy(item)}
                                >
                                  {isMutatingThis ? (
                                    "..."
                                  ) : (
                                    <span className="flex items-center gap-1.5">
                                      <Gem
                                        size={10}
                                        className={
                                          canAfford
                                            ? "text-red-500 fill-red-500/20"
                                            : "text-red-500/50"
                                        }
                                      />
                                      {item.cost.toLocaleString()}
                                    </span>
                                  )}
                                </Button>
                              )}
                            </div>
                          </Card>
                        </Motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-3 order-1 lg:order-2 py-4">
              <ReferralSection {...referral} />
            </div>
          </div>
        </main>
      </div>
    </Skeleton>
  );
});

MarketplacePage.displayName = "MarketplacePage";

export default MarketplacePage;
