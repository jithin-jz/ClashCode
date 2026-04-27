import React, { useEffect, useState } from "react";
import { authAPI } from "../services/api";
import { notify } from "../services/notification";
import {
  Users,
  Box,
  ShoppingBag,
  Gem,
  Star,
  Trophy,
  CheckCircle,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { AnalyticsSkeleton } from "./AdminSkeletons";
import ClusterHealthMonitor from "./components/ClusterHealthMonitor";

// --- Helper Components ---

const StatCard = ({ title, value, sub, icon, color }) => (
  <div className="admin-panel cursor-default p-5 transition-colors hover:border-white/12">
    <div className="flex items-center justify-between mb-4">
      <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">
        {title}
      </span>
      <div className={`rounded bg-white/[0.04] p-1.5 ${color}`}>{icon}</div>
    </div>
    <div className="space-y-0.5">
      <h3 className="text-2xl font-bold text-neutral-100 tracking-tight">
        {value}
      </h3>
      <p className="text-[10px] font-medium text-neutral-500 uppercase tracking-wide">
        {sub}
      </p>
    </div>
  </div>
);

const CardSection = ({ title, icon, children }) => (
  <div className="admin-panel space-y-5 p-6">
    <div className="flex items-center gap-2.5">
      <div className="rounded bg-white/[0.04] p-1.5">{icon}</div>
      <h2 className="text-lg font-bold text-neutral-100 tracking-tight">
        {title}
      </h2>
    </div>
    {children}
  </div>
);

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await authAPI.getUltimateAnalytics();
        setData(response.data);
      } catch (error) {
        console.error("Failed to fetch ultimate analytics", error);
        notify.error("Failed to fetch ultimate analytics");
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return <AnalyticsSkeleton />;
  }

  if (!data) return null;

  const {
    overview,
    growth_trends,
    economy_pulse,
    top_challenges,
    top_items,
    community_leaders,
  } = data;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* 1. Command Center Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={overview.total_users}
          sub={`+${overview.active_24h} Active (24h)`}
          icon={<Users size={16} />}
          color="text-neutral-200"
        />
        <StatCard
          title="Revenue"
          value={`${economy_pulse.total_store_revenue.toLocaleString()} XP`}
          sub="Total Revenue"
          icon={<Gem size={16} />}
          color="text-neutral-200"
        />
        <StatCard
          title="Store Items"
          value={overview.store_catalog}
          sub="Active Items"
          icon={<ShoppingBag size={16} />}
          color="text-neutral-200"
        />
        <StatCard
          title="Challenges"
          value={overview.total_challenges}
          sub="Total Challenges"
          icon={<Trophy size={16} />}
          color="text-neutral-200"
        />
      </div>

      {/* 2. Growth Visualizer */}
      <div className="admin-panel p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-xl font-bold text-neutral-100 tracking-tight">
              User Growth
            </h2>
            <p className="text-xs text-neutral-500 mt-1">
              Player acquisition trends over the last 30 days
            </p>
          </div>
          <Badge
            variant="outline"
            className="admin-muted-badge px-3 py-1 text-[10px] font-bold uppercase tracking-widest"
          >
            New Users
          </Badge>
        </div>

        <div className="h-48 flex items-end gap-1 px-4 relative">
          {/* Background Grid Lines */}
          <div className="absolute inset-x-0 bottom-0 h-full flex justify-between pointer-events-none opacity-10">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="w-px h-full bg-neutral-500" />
            ))}
          </div>

          {growth_trends.map((item, idx) => {
            const maxCount = Math.max(...growth_trends.map((d) => d.count), 1);
            const height = (item.count / maxCount) * 100;
            const hasData = item.count > 0;

            return (
              <div
                key={idx}
                className="flex-1 group/bar relative h-full flex flex-col justify-end z-10"
              >
                <div
                  className={`w-full transition-all duration-300 rounded-t-sm ${
                    hasData
                      ? "bg-white/80"
                      : "bg-white/5 group-hover/bar:bg-white/10"
                  }`}
                  style={{
                    height: `${Math.max(height, 4)}%`,
                    opacity: hasData ? 1 : 0.5,
                  }}
                >
                  <div className="absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded border border-white/10 bg-[#121212] px-2.5 py-1.5 text-[10px] font-medium text-white opacity-0 shadow-xl transition-opacity pointer-events-none group-hover/bar:opacity-100">
                    {item.date}: {item.count} users
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-6 flex justify-between text-[10px] font-bold text-neutral-500 uppercase tracking-widest border-t border-white/5 pt-4">
          <span>{growth_trends[0]?.date}</span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-white/70 animate-pulse" />
            Active Growth
          </span>
          <span>Today</span>
        </div>
      </div>

      {/* Live Cluster Monitor */}
      <ClusterHealthMonitor />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 3. Competitive Performance */}
        <CardSection
          icon={<Trophy size={18} className="text-neutral-200" />}
          title="Popular Challenges"
        >
          <div className="overflow-hidden rounded-xl border border-white/8 bg-white/[0.02]">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 bg-white/[0.02]">
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 px-4">
                    Challenge
                  </TableHead>
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 text-right">
                    Attempts
                  </TableHead>
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 text-right">
                    Completions
                  </TableHead>
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 text-right px-4">
                    Avg Performance
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {top_challenges.map((c, idx) => (
                  <TableRow
                    key={idx}
                    className="border-white/5 hover:bg-white/[0.03]"
                  >
                    <TableCell className="py-3 px-4 text-sm font-medium text-neutral-200 truncate max-w-[180px]">
                      {c.title}
                    </TableCell>
                    <TableCell className="py-3 text-right text-xs text-neutral-400 font-mono">
                      {c.attempts}
                    </TableCell>
                    <TableCell className="py-3 text-right">
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/5 text-xs text-neutral-300 font-mono">
                        <CheckCircle size={10} className="text-neutral-500" />
                        {c.completions}
                      </div>
                    </TableCell>
                    <TableCell className="py-3 text-right px-4">
                      <div className="flex items-center justify-end gap-1 text-neutral-200 font-mono text-xs font-bold">
                        <Star size={10} fill="currentColor" />
                        {c.avg_stars.toFixed(1)}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardSection>

        {/* 4. Economy Champions */}
        <CardSection
          icon={<Box size={18} className="text-neutral-200" />}
          title="Top Selling Items"
        >
          <div className="overflow-hidden rounded-xl border border-white/8 bg-white/[0.02]">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 bg-white/[0.02]">
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 px-4">
                    Store Item
                  </TableHead>
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 text-right">
                    Sales
                  </TableHead>
                  <TableHead className="text-[10px] uppercase font-bold text-neutral-500 py-3 text-right px-4">
                    Gross Revenue
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {top_items.map((item, idx) => (
                  <TableRow
                    key={idx}
                    className="border-white/5 hover:bg-white/[0.03]"
                  >
                    <TableCell className="py-3 px-4 text-sm font-medium text-neutral-200">
                      {item.name}
                    </TableCell>
                    <TableCell className="py-3 text-right text-xs text-neutral-400 font-mono">
                      {item.sales} Units
                    </TableCell>
                    <TableCell className="py-3 text-right px-4 text-xs font-bold text-neutral-200 font-mono">
                      {item.revenue.toLocaleString()} XP
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardSection>
      </div>

      {/* 5. Population Leaders */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-white/[0.04] p-2 text-neutral-200">
              <Trophy size={18} />
            </div>
            <h2 className="text-xl font-bold text-neutral-100 tracking-tight">
              Top Ranking Users
            </h2>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
              In Circulation
            </span>
            <span className="text-sm font-bold text-white font-mono">
              {Math.floor(economy_pulse.total_circulation_xp / 1000)}K XP
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {community_leaders.map((user, idx) => (
            <div
              key={user.username}
              className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] p-4 transition-all group hover:border-white/12 hover:bg-white/[0.04]"
            >
              <div className="flex items-center gap-4">
                <span className="text-xs font-bold text-neutral-500 font-mono w-4">
                  {idx + 1}.
                </span>
                <div className="space-y-0.5">
                  <p className="text-sm font-bold text-neutral-100 group-hover:text-white transition-colors capitalize">
                    {user.username}
                  </p>
                  <p className="text-[10px] text-neutral-500 font-medium uppercase tracking-wider">
                    {user.followers} Followers
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-neutral-100 font-mono">
                  {user.xp.toLocaleString()}
                </div>
                <div className="text-[8px] font-bold text-neutral-600 uppercase tracking-widest">
                  Total XP Earned
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};


export default Analytics;
