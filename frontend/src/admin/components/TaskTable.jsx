import React from "react";
import { Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { AdminTableLoadingRow } from "../AdminSkeletons";

/**
 * TaskTable Component
 * 
 * Desktop-optimized table for managing coding challenges.
 */
const TaskTable = ({
  isLoading,
  tasks,
  setEditingTask,
  handleDelete,
}) => {
  return (
    <div className="hidden overflow-hidden md:block admin-panel">
      <Table className="min-w-[760px]">
        <TableHeader>
          <TableRow className="border-white/10 hover:bg-transparent bg-white/[0.02]">
            <TableHead className="w-[80px] py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              #
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Challenge
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              XP Reward
            </TableHead>
            <TableHead className="py-3 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Time Limit
            </TableHead>
            <TableHead className="py-3 text-right text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-500">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            [...Array(6)].map((_, i) => (
              <AdminTableLoadingRow key={i} colSpan={5} />
            ))
          ) : tasks.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="h-24 text-center text-neutral-500 text-sm italic"
              >
                No challenges found.
              </TableCell>
            </TableRow>
          ) : (
            tasks.map((task) => (
              <TableRow
                key={task.id}
                className="border-white/10 hover:bg-white/5 transition-colors group"
              >
                <TableCell className="py-3">
                  <span className="text-xs font-mono text-neutral-500">
                    {task.order.toString().padStart(2, "0")}
                  </span>
                </TableCell>
                <TableCell className="py-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-neutral-100 tracking-tight flex items-center gap-2">
                      {task.title}
                    </span>
                    <span className="text-[11px] text-neutral-500 font-mono">
                      /{task.slug}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="py-3 font-mono text-xs">
                  <span className="text-neutral-300">{task.xp_reward} XP</span>
                </TableCell>
                <TableCell className="py-3">
                  <span className="text-neutral-500 text-xs">{task.time_limit}s</span>
                </TableCell>
                <TableCell className="text-right py-3">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingTask(task)}
                      className="h-8 w-8 p-0 text-neutral-400 hover:text-white hover:bg-white/10 rounded-md"
                    >
                      <Edit className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(task.slug)}
                      className="h-8 w-8 p-0 text-neutral-400 hover:text-red-400 hover:bg-red-500/10 rounded-md"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default TaskTable;
