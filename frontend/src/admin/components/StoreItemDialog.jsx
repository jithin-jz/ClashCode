import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import api from "../../services/api";
import { notify } from "../../services/notification";

/**
 * StoreItemDialog Component
 * 
 * A modal form for creating or editing store items (Themes, Fonts, etc.).
 * Handles image uploads and JSON validation.
 */
const StoreItemDialog = ({
  isOpen,
  setIsOpen,
  currentItem,
  formData,
  setFormData,
  saving,
  handleSubmit,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="border-white/10 bg-[#050505] text-white max-w-[calc(100vw-2rem)] sm:max-w-md shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold text-neutral-100">
            {currentItem ? "Edit Item" : "New Item"}
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-neutral-500">Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="admin-control h-9 text-sm"
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-neutral-500">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="admin-control h-9 w-full rounded-md px-3 text-sm text-white focus:outline-none"
              >
                <option value="THEME">Theme</option>
                <option value="FONT">Font</option>
                <option value="EFFECT">Effect</option>
                <option value="VICTORY">Victory</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Description</label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="admin-control h-20 text-sm resize-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-neutral-500">Cost (XP)</label>
              <Input
                type="number"
                value={formData.cost}
                onChange={(e) => setFormData({ ...formData, cost: parseInt(e.target.value) })}
                className="admin-control h-9 text-sm"
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-neutral-500">Icon Name</label>
              <Input
                value={formData.icon_name}
                onChange={(e) => setFormData({ ...formData, icon_name: e.target.value })}
                className="admin-control h-9 text-sm"
                placeholder="e.g. Palette"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Configuration (JSON)</label>
            <Textarea
              value={formData.item_data}
              onChange={(e) => setFormData({ ...formData, item_data: e.target.value })}
              className="admin-control h-24 font-mono text-[10px] resize-none"
              placeholder='{"theme_key": "dracula"}'
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-neutral-500">Asset URL</label>
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                value={formData.image}
                onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                className="admin-control h-9 flex-1 text-sm"
                placeholder="/assets/item.png"
              />
              <Input
                type="file"
                className="hidden"
                id="image-upload"
                accept="image/*"
                onChange={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;

                  const uploadData = new FormData();
                  uploadData.append("image", file);

                  const toastId = notify.loading("Uploading...");
                  try {
                    const res = await api.post("/store/upload/", uploadData, {
                      headers: { "Content-Type": "multipart/form-data" },
                    });
                    setFormData((prev) => ({ ...prev, image: res.data.url }));
                    notify.success("Uploaded");
                  } catch {
                    notify.error("Upload failed");
                  } finally {
                    notify.dismiss(toastId);
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-9 border-white/10 bg-white/[0.03] text-neutral-300 hover:bg-white/[0.06] hover:text-white"
                onClick={() => document.getElementById("image-upload").click()}
              >
                Upload
              </Button>
            </div>
          </div>

          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsOpen(false)}
              className="text-neutral-400 hover:text-white hover:bg-white/10 h-9"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={saving}
              className="bg-white text-black hover:bg-zinc-200 h-9 font-medium px-6"
            >
              {saving ? "Saving..." : "Save Asset"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default StoreItemDialog;
