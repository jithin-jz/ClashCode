import React, { useState } from "react";
import { X } from "lucide-react";
import Editor from "@monaco-editor/react";
import { Button } from "../../components/ui/button";
import { challengesApi } from "../../services/challengesApi";
import { notify } from "../../services/notification";
import { getErrorMessage } from "../../utils/errorUtils";

/**
 * TaskForm Component
 * 
 * A detailed editor for creating or updating coding challenges.
 * Includes Monaco Editor for initial and validation code.
 */
const TaskForm = ({ task, onSave, onCancel, tasksCount }) => {
  const [formData, setFormData] = useState(
    task || {
      title: "",
      slug: "",
      description: "",
      order: tasksCount + 1,
      xp_reward: 50,
      initial_code: "# Write your code here\n",
      test_code: "# assert something\n",
      time_limit: 300,
    }
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (task && task.slug) {
        await challengesApi.update(task.slug, formData);
        notify.success("Challenge updated");
      } else {
        await challengesApi.create(formData);
        notify.success("Challenge created");
      }
      onSave();
    } catch (error) {
      console.error("Failed to save challenge:", error);
      notify.error(getErrorMessage(error, "Failed to save challenge"));
    }
  };

  return (
    <div className="admin-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-neutral-100">
          {task ? "Edit Challenge" : "New Challenge"}
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="h-8 w-8 p-0 text-neutral-400 hover:text-white hover:bg-white/10"
        >
          <X size={18} />
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Title</label>
            <input
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="admin-control w-full rounded-md px-3 py-2 text-sm text-white outline-none"
              placeholder="FizzBuzz"
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Slug</label>
            <input
              name="slug"
              value={formData.slug}
              onChange={handleChange}
              className="admin-control w-full rounded-md px-3 py-2 text-sm text-white font-mono outline-none"
              placeholder="fizz-buzz"
              required
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-neutral-500">Description (Markdown)</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            className="admin-control h-32 w-full rounded-md px-3 py-2 text-sm text-white font-mono outline-none resize-none"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Order</label>
            <input
              type="number"
              name="order"
              value={formData.order}
              onChange={handleChange}
              className="admin-control w-full rounded-md px-3 py-2 text-sm text-white outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">XP Reward</label>
            <input
              type="number"
              name="xp_reward"
              value={formData.xp_reward}
              onChange={handleChange}
              className="admin-control w-full rounded-md px-3 py-2 text-sm text-white outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Time Limit (s)</label>
            <input
              type="number"
              name="time_limit"
              value={formData.time_limit}
              onChange={handleChange}
              className="admin-control w-full rounded-md px-3 py-2 text-sm text-white outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:h-[300px]">
          <div className="flex flex-col space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Initial Code</label>
            <div className="h-56 overflow-hidden rounded-md border border-white/10 bg-[#050505] lg:h-full">
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={formData.initial_code}
                onChange={(val) => setFormData((prev) => ({ ...prev, initial_code: val }))}
                options={{
                  minimap: { enabled: false },
                  fontSize: 12,
                  padding: { top: 10 },
                  background: "#050505",
                }}
              />
            </div>
          </div>
          <div className="flex flex-col space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Validation Code</label>
            <div className="h-56 overflow-hidden rounded-md border border-white/10 bg-[#050505] lg:h-full">
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={formData.test_code}
                onChange={(val) => setFormData((prev) => ({ ...prev, test_code: val }))}
                options={{
                  minimap: { enabled: false },
                  fontSize: 12,
                  padding: { top: 10 },
                  background: "#050505",
                }}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t border-white/10">
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            className="text-neutral-400 hover:text-white hover:bg-white/10 px-4 h-9"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            className="bg-white text-black hover:bg-zinc-200 px-4 h-9 font-medium"
          >
            Save Challenge
          </Button>
        </div>
      </form>
    </div>
  );
};

export default TaskForm;
