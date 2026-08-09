import React from "react";

const ContributionGraph = ({ data, loading }) => {
  const contributionMap = React.useMemo(() => {
    const map = {};
    if (!Array.isArray(data)) return map;
    data.forEach((item) => {
      if (!item.date) return;
      const dateStr = new Date(item.date).toISOString().split("T")[0];
      map[dateStr] = (map[dateStr] || 0) + (item.count || 0);
    });
    return map;
  }, [data]);

  const getLevel = (count) => {
    if (count === 0) return 0;
    if (count <= 2) return 1;
    if (count <= 5) return 2;
    if (count <= 10) return 3;
    return 4;
  };

  const gridData = React.useMemo(() => {
    const weeks = [];
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 364);
    const startDay = startDate.getDay();
    startDate.setDate(startDate.getDate() - startDay);

    let currentDate = new Date(startDate);

    for (let w = 0; w < 53; w++) {
      const days = [];
      for (let d = 0; d < 7; d++) {
        const dateStr = currentDate.toISOString().split("T")[0];
        const count = contributionMap[dateStr] || 0;
        days.push({ date: dateStr, count, level: getLevel(count) });
        currentDate.setDate(currentDate.getDate() + 1);
      }
      weeks.push(days);
      if (currentDate > today) break;
    }
    return weeks;
  }, [contributionMap]);

  const totalContributions = React.useMemo(() => {
    if (!Array.isArray(data)) return 0;
    return data.reduce((acc, curr) => acc + (curr.count || 0), 0);
  }, [data]);

  const colors = [
    "bg-neutral-800/50",
    "bg-emerald-900/50",
    "bg-emerald-700/60",
    "bg-emerald-500/70",
    "bg-emerald-400",
  ];

  if (loading) {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 animate-pulse">
        <div className="h-3 w-32 bg-neutral-800 rounded mb-4" />
        <div className="h-[88px] bg-neutral-900/50 rounded" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-[12px] text-neutral-500">
          {totalContributions} contributions in the last year
        </span>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-neutral-700">Less</span>
          {colors.map((c, i) => (
            <div key={i} className={`w-2 h-2 rounded-sm ${c}`} />
          ))}
          <span className="text-[10px] text-neutral-700">More</span>
        </div>
      </div>

      {/* Heatmap — responsive: scrollable on mobile, fills width on desktop */}
      <div className="w-full overflow-x-auto">
        <div
          className="grid gap-[3px] min-w-[600px] lg:min-w-0 lg:w-full"
          style={{
            gridTemplateRows: "repeat(7, 1fr)",
            gridAutoFlow: "column",
            gridAutoColumns: "1fr",
          }}
        >
          {gridData.flat().map((day, i) => (
            <div
              key={i}
              title={`${day.date}: ${day.count} contributions`}
              className={`aspect-square rounded-sm ${colors[day.level]} transition-colors`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ContributionGraph;
