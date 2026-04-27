import {
  BarChart,
  Users,
  LogOut,
  Shield,
  Layers,
  ShoppingBag,
  Flag,
  Home,
  Activity,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { useNavigate } from "react-router-dom";

const AdminSidebar = ({ user, activeTab, setActiveTab, handleLogout }) => {
  const navigate = useNavigate();
  const sidebarItems = [
    { id: "users", label: "Users", icon: <Users size={18} /> },
    { id: "analytics", label: "Analytics", icon: <BarChart size={18} /> },
    { id: "tasks", label: "Challenges", icon: <Layers size={18} /> },
    { id: "store", label: "Store", icon: <ShoppingBag size={18} /> },
    { id: "broadcast", label: "Announcements", icon: <Shield size={18} /> },
    { id: "audit", label: "Audit Logs", icon: <Layers size={18} /> },
    { id: "celery", label: "Worker Tasks", icon: <Activity size={18} /> },
    { id: "reports", label: "Reports", icon: <Flag size={18} /> },
  ];

  return (
    <aside className="w-full shrink-0 border-b border-white/8 bg-black/95 md:h-full md:w-64 md:border-b-0 md:border-r">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-white/8 bg-black px-4 md:px-6">
        <div className="flex items-center gap-2 min-w-0">
          <Shield className="text-slate-200" size={18} />
          <span className="truncate text-sm font-semibold tracking-tight text-slate-100">
            Admin Panel
          </span>
        </div>
        <Button
          onClick={() => navigate("/home")}
          variant="ghost"
          className="h-8 gap-2 rounded-md px-2 text-xs text-slate-300 hover:bg-white/5 hover:text-white md:hidden"
        >
          <Home size={14} />
          <span>User Side</span>
        </Button>
        <Button
          onClick={handleLogout}
          variant="ghost"
          className="h-8 gap-2 rounded-md px-2 text-xs text-slate-300 hover:bg-white/5 hover:text-white md:hidden"
        >
          <LogOut size={14} />
          <span>Logout</span>
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-x-auto p-2 md:overflow-y-auto md:p-3">
        <div className="hidden md:block px-3 mb-2">
          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">
            Main Menu
          </p>
        </div>
        <div className="flex md:block gap-1 md:space-y-1 min-w-max md:min-w-0">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`shrink-0 md:w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs md:text-sm transition-all duration-200 ${
                activeTab === item.id
                  ? "border border-white/12 bg-white/[0.045] text-white"
                  : "border border-transparent text-slate-300 hover:border-white/8 hover:bg-white/[0.03] hover:text-white"
              }`}
            >
              <span
                className={`${
                  activeTab === item.id ? "text-slate-100" : "text-slate-500"
                }`}
              >
                {item.icon}
              </span>
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Profile Section */}
      <div className="hidden border-t border-white/8 p-4 md:block">
        <div className="flex items-center gap-3 mb-4 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white">
            {user?.profile?.avatar_url ? (
              <img
                src={user.profile.avatar_url}
                alt=""
                className="w-full h-full object-cover rounded-full"
              />
            ) : (
              <span className="text-[10px] font-bold text-slate-100">
                {user?.username?.[0]?.toUpperCase()}
              </span>
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="truncate text-xs font-medium text-slate-100">
              {user?.username}
            </span>
            <span className="text-[10px] text-slate-500">Administrator</span>
          </div>
        </div>

        <Button
          onClick={() => navigate("/home")}
          variant="ghost"
          className="mb-2 h-9 w-full justify-start gap-2.5 rounded-md px-2 text-xs text-slate-300 hover:bg-white/5 hover:text-white"
        >
          <Home size={14} />
          <span>User Side</span>
        </Button>

        <Button
          onClick={handleLogout}
          variant="ghost"
          className="h-9 w-full justify-start gap-2.5 rounded-md px-2 text-xs text-slate-300 hover:bg-white/5 hover:text-white"
        >
          <LogOut size={14} />
          <span>Logout</span>
        </Button>
      </div>
    </aside>
  );
};

export default AdminSidebar;
