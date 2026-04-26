import React, { useState } from "react";
import { X, Settings, FileText, Code, ChevronRight, Info } from "lucide-react";
import Editor from "@monaco-editor/react";
import { Button } from "../../components/ui/button";
import { challengesApi } from "../../services/challengesApi";
import { notify } from "../../services/notification";
import { getErrorMessage } from "../../utils/errorUtils";

/**
 * TaskForm Component
 * 
 * A redesigned, beginner-friendly editor for coding challenges.
 * Uses a tabbed interface to separate configuration, instructions, and code.
 */
const TaskForm = ({ task, onSave, onCancel, tasksCount }) => {
  const [activeTab, setActiveTab] = useState("general");
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

  const tabs = [
    { id: "general", label: "General", icon: Settings },
    { id: "content", label: "Instructions", icon: FileText },
    { id: "code", label: "Code & Logic", icon: Code },
  ];

  return (
    <div className="admin-panel overflow-hidden border-white/5 bg-[#080808]/90 backdrop-blur-3xl shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-white/5">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            {task ? "Edit Challenge" : "Forge New Challenge"}
            <span className="text-[10px] font-medium uppercase tracking-[0.2em] bg-white/5 text-neutral-500 px-2 py-0.5 rounded-full border border-white/5">
              Protocol: {formData.slug || "UNNAMED"}
            </span>
          </h2>
          <p className="text-xs text-neutral-500 font-medium">Configure coding environments and validation logic.</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="h-9 w-9 p-0 rounded-xl text-neutral-500 hover:text-white hover:bg-white/10 transition-all"
        >
          <X size={20} />
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex px-6 pt-4 border-b border-white/5 gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-widest transition-all relative ${
                isActive ? "text-white" : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              <Icon size={14} className={isActive ? "text-blue-400" : "text-neutral-600"} />
              {tab.label}
              {isActive && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
              )}
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-8">
        {/* General Settings Tab */}
        {activeTab === "general" && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Challenge Title</label>
                    <span className="text-[10px] text-neutral-600">Required</span>
                  </div>
                  <input
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="admin-control w-full rounded-xl px-4 py-3 text-sm text-white bg-white/[0.03] border-white/10 hover:border-white/20 transition-all focus:ring-1 focus:ring-blue-500/30"
                    placeholder="e.g. Matrix Rotation"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">URL Slug</label>
                    <Info size={12} className="text-neutral-600" />
                  </div>
                  <input
                    name="slug"
                    value={formData.slug}
                    onChange={handleChange}
                    className="admin-control w-full rounded-xl px-4 py-3 text-sm text-white font-mono bg-white/[0.03] border-white/10 hover:border-white/20 transition-all"
                    placeholder="matrix-rotation"
                    required
                  />
                  <p className="text-[10px] text-neutral-600">This is the unique ID used in the URL. Keep it lowercase with hyphens.</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Forge Order</label>
                  <input
                    type="number"
                    name="order"
                    value={formData.order}
                    onChange={handleChange}
                    className="admin-control w-full rounded-xl px-4 py-3 text-sm text-white bg-white/[0.03] border-white/10"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">XP Yield</label>
                  <input
                    type="number"
                    name="xp_reward"
                    value={formData.xp_reward}
                    onChange={handleChange}
                    className="admin-control w-full rounded-xl px-4 py-3 text-sm text-white bg-white/[0.03] border-white/10"
                  />
                </div>
                <div className="col-span-2 space-y-1.5">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Time Limit (Seconds)</label>
                  <input
                    type="number"
                    name="time_limit"
                    value={formData.time_limit}
                    onChange={handleChange}
                    className="admin-control w-full rounded-xl px-4 py-3 text-sm text-white bg-white/[0.03] border-white/10"
                  />
                  <p className="text-[10px] text-neutral-600 text-right">Standard: 300s (5m)</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Instructions Tab */}
        {activeTab === "content" && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Description (Markdown)</label>
                <div className="flex gap-4">
                    <span className="text-[10px] text-neutral-500 italic">Supports HTML & Rich Code Blocks</span>
                </div>
              </div>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                className="admin-control h-[400px] w-full rounded-2xl px-4 py-4 text-sm text-neutral-300 font-mono bg-white/[0.02] border-white/10 hover:border-white/20 transition-all outline-none resize-none ds-scrollbar"
                placeholder="### Problem Statement\nDescribe the challenge here..."
                required
              />
            </div>
          </div>
        )}

        {/* Code Tab */}
        {activeTab === "code" && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[500px]">
              <div className="flex flex-col space-y-3">
                <div className="flex items-center justify-between px-1">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Initial Sandbox</label>
                    <span className="text-[10px] text-neutral-600">The code user starts with</span>
                </div>
                <div className="flex-1 overflow-hidden rounded-2xl border border-white/10 bg-[#050505] relative group">
                  <Editor
                    height="100%"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={formData.initial_code}
                    onChange={(val) => setFormData((prev) => ({ ...prev, initial_code: val }))}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 13,
                      padding: { top: 16 },
                      background: "#050505",
                      lineNumbers: "on",
                      scrollBeyondLastLine: false,
                    }}
                  />
                </div>
              </div>
              <div className="flex flex-col space-y-3">
                <div className="flex items-center justify-between px-1">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-neutral-500">Validation Logic</label>
                    <span className="text-[10px] text-neutral-600">Internal test suite (Hidden)</span>
                </div>
                <div className="flex-1 overflow-hidden rounded-2xl border border-white/10 bg-[#050505] relative group">
                  <Editor
                    height="100%"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={formData.test_code}
                    onChange={(val) => setFormData((prev) => ({ ...prev, test_code: val }))}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 13,
                      padding: { top: 16 },
                      background: "#050505",
                      lineNumbers: "on",
                      scrollBeyondLastLine: false,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Bar */}
        <div className="flex items-center justify-between pt-8 border-t border-white/5">
          <div className="flex items-center gap-4">
            {activeTab !== "code" && (
                <button
                    type="button"
                    onClick={() => {
                        const idx = tabs.findIndex(t => t.id === activeTab);
                        setActiveTab(tabs[idx + 1].id);
                    }}
                    className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.2em] text-neutral-500 hover:text-white transition-colors"
                >
                    Next Phase <ChevronRight size={14} />
                </button>
            )}
          </div>
          <div className="flex gap-3">
            <Button
              type="button"
              variant="ghost"
              onClick={onCancel}
              className="text-neutral-500 hover:text-white hover:bg-white/10 px-6 h-11 rounded-xl transition-all"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-white text-black hover:bg-neutral-200 px-8 h-11 rounded-xl font-bold shadow-xl shadow-white/5 transition-all active:scale-95"
            >
              {task ? "Update Challenge" : "Forge Challenge"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default TaskForm;
