import React from "react";
import { Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";

/**
 * TaskMobileList Component
 * 
 * Card-based view for managing coding challenges on mobile devices.
 */
const TaskMobileList = ({
  isLoading,
  tasks,
  setEditingTask,
  handleDelete,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-3 md:hidden">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="admin-panel h-32 animate-pulse bg-white/[0.02]"
          />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="admin-panel px-4 py-10 text-center text-sm italic text-neutral-500 md:hidden">
        No challenges found.
      </div>
    );
  }

  return (
    <div className="space-y-3 md:hidden">
      {tasks.map((task) => (
        <div key={task.id} className="admin-panel p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-neutral-500">
                #{task.order.toString().padStart(2, "0")}
              </div>
              <div className="mt-1 truncate text-sm font-medium text-neutral-100">
                {task.title}
              </div>
              <div className="truncate text-[11px] font-mono text-neutral-500">
                /{task.slug}
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs font-mono text-neutral-200">
                {task.xp_reward} XP
              </div>
              <div className="mt-1 text-[11px] text-neutral-500">
                {task.time_limit}s
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2 border-t border-white/8 pt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditingTask(task)}
              className="h-9 flex-1 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
            >
              <Edit className="h-3.5 w-3.5" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(task.slug)}
              className="h-9 flex-1 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-red-500/10 hover:text-red-400"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TaskMobileList;
