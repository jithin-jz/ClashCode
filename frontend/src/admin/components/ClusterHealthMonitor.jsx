import React, { useEffect, useState } from "react";
import { Activity, Cpu, Database, HardDrive, Zap } from "lucide-react";
import { Badge } from "../../components/ui/badge";

const ClusterHealthMonitor = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    try {
      // Accessing the analytics service through the exposed /stats path
      const response = await fetch("/stats/cluster");
      if (!response.ok) throw new Error("Failed to fetch cluster metrics");
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      console.error("Cluster Monitor Error:", err);
      setError("Unable to connect to cluster metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <div className="admin-panel p-6 animate-pulse">
        <div className="h-4 w-48 bg-white/5 rounded mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-32 bg-white/5 rounded" />
          <div className="h-32 bg-white/5 rounded" />
        </div>
      </div>
    );
  }

  const nodeStats = metrics?.cluster_metrics || { cpu_usage: 0, memory_usage: 0 };
  const getStatusColor = (val) => {
    if (val > 80) return "text-red-500 bg-red-500/10 border-red-500/20";
    if (val > 50) return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
    return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-500">
            <Activity size={18} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-neutral-100 tracking-tight">EKS Cluster Health</h2>
            <p className="text-xs text-neutral-500 mt-0.5">Real-time AWS infrastructure metrics</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {error ? (
            <Badge variant="outline" className="text-red-500 border-red-500/20 bg-red-500/5">
              Metrics Offline
            </Badge>
          ) : (
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Live</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* CPU Usage */}
        <div className="admin-panel p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu size={14} className="text-neutral-500" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Node CPU</span>
            </div>
            <span className={`text-xs font-mono font-bold ${getStatusColor(nodeStats.cpu_usage).split(' ')[0]}`}>
              {nodeStats.cpu_usage.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 rounded-full ${nodeStats.cpu_usage > 80 ? 'bg-red-500' : 'bg-emerald-500'}`}
              style={{ width: `${nodeStats.cpu_usage}%` }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div className="admin-panel p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive size={14} className="text-neutral-500" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Node RAM</span>
            </div>
            <span className={`text-xs font-mono font-bold ${getStatusColor(nodeStats.memory_usage).split(' ')[0]}`}>
              {nodeStats.memory_usage.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 rounded-full ${nodeStats.memory_usage > 80 ? 'bg-red-500' : 'bg-emerald-500'}`}
              style={{ width: `${nodeStats.memory_usage}%` }}
            />
          </div>
        </div>

        {/* Pod Status */}
        <div className="admin-panel p-5 flex items-center justify-between">
           <div className="space-y-1">
             <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Total Pods</span>
             <h3 className="text-2xl font-bold text-white font-mono">{metrics?.pod_metrics?.length || 0}</h3>
           </div>
           <div className="rounded-full bg-blue-500/10 p-3 text-blue-500">
             <Database size={20} />
           </div>
        </div>
      </div>

      {/* Service Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {['ai', 'chat', 'core', 'executor'].map(service => {
          const sMetric = metrics?.pod_metrics?.find(m => m.pod_name.includes(service));
          return (
            <div key={service} className="admin-subpanel p-4 group hover:bg-white/[0.03] transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-white uppercase tracking-tighter">{service}</span>
                <Badge variant="outline" className="text-[8px] border-emerald-500/20 text-emerald-500 py-0 px-1.5">Stable</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-[10px]">
                  <span className="text-neutral-500">CPU</span>
                  <span className="text-neutral-300 font-mono">{(sMetric?.cpu || 0).toFixed(2)}m</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span className="text-neutral-500">RAM</span>
                  <span className="text-neutral-300 font-mono">{(sMetric?.memory || 0).toFixed(1)}MB</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ClusterHealthMonitor;
