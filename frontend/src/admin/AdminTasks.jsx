import React, { useEffect, useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";
import { challengesApi } from "../services/challengesApi";
import { notify } from "../services/notification";
import { getErrorMessage } from "../utils/errorUtils";

// Sub-components
import TaskForm from "./components/TaskForm";
import TaskTable from "./components/TaskTable";
import TaskMobileList from "./components/TaskMobileList";
import TaskPagination from "./components/TaskPagination";

/**
 * AdminTasks Component
 * 
 * The main container for Challenge Management in the Admin panel.
 * Orchestrates data fetching, deletions, and switching between list and form views.
 */
const AdminTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingTask, setEditingTask] = useState(null); // null = list, {} = new, {id...} = edit
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchTasks();
  }, []);

  const totalCount = tasks.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  
  const paginatedTasks = useMemo(() => {
    const start = (page - 1) * pageSize;
    return tasks.slice(start, start + pageSize);
  }, [tasks, page, pageSize]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const data = await challengesApi.getAll();
      setTasks(data.sort((a, b) => a.order - b.order));
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
      notify.error(getErrorMessage(error, "Failed to load challenges"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (slug) => {
    notify.warning("Delete Challenge", {
      description: "Are you sure you want to delete this challenge? This action cannot be undone.",
      action: {
        label: "Delete",
        onClick: async () => {
          try {
            await challengesApi.delete(slug);
            notify.success("Challenge deleted");
            fetchTasks();
          } catch (error) {
            notify.error(getErrorMessage(error, "Failed to delete challenge"));
          }
        },
      },
    });
  };

  return (
    <div className="space-y-4">
      {!editingTask ? (
        <>
          {/* Header Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h2 className="text-xl font-semibold text-neutral-100 tracking-tight">
              Challenge Management
            </h2>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchTasks}
                disabled={isLoading}
                className="h-8 w-full gap-2 rounded-md border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white sm:w-auto"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
                <span className="text-xs font-medium">
                  {isLoading ? "Refreshing..." : "Refresh"}
                </span>
              </Button>
              <Button
                size="sm"
                onClick={() => setEditingTask({})}
                className="h-8 w-full gap-2 rounded-md bg-white px-3 font-medium text-black transition-colors hover:bg-zinc-200 sm:w-auto"
              >
                <Plus className="h-3.5 w-3.5" />
                <span className="text-xs">Add Challenge</span>
              </Button>
            </div>
          </div>

          {/* Mobile View */}
          <TaskMobileList
            isLoading={isLoading}
            tasks={paginatedTasks}
            setEditingTask={setEditingTask}
            handleDelete={handleDelete}
          />

          {/* Desktop View */}
          <TaskTable
            isLoading={isLoading}
            tasks={paginatedTasks}
            setEditingTask={setEditingTask}
            handleDelete={handleDelete}
          />

          {/* Pagination Footer */}
          {!isLoading && (
            <TaskPagination
              page={page}
              setPage={setPage}
              totalPages={totalPages}
              pageSize={pageSize}
              setPageSize={setPageSize}
              totalCount={totalCount}
            />
          )}
        </>
      ) : (
        <TaskForm
          task={Object.keys(editingTask).length > 0 ? editingTask : null}
          tasksCount={tasks.length}
          onSave={() => {
            setEditingTask(null);
            fetchTasks();
          }}
          onCancel={() => setEditingTask(null)}
        />
      )}
    </div>
  );
};

export default AdminTasks;
