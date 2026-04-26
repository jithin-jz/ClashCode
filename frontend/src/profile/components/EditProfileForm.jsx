import React, { useRef } from "react";
import { Camera } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";

const EditProfileForm = ({
  editForm,
  setEditForm,
  setIsEditing,
  uploadingBanner,
  handleImageUpload,
  setDeleteDialogOpen,
  handleSaveProfile,
  savingProfile,
}) => {
  const bannerInputRef = useRef(null);

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-xl font-black italic tracking-tighter text-white flex items-center gap-3">
          <span className="w-2 h-6 bg-emerald-500 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
          EDIT PROFILE
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsEditing(false)}
          className="text-neutral-500 hover:text-white text-[10px] font-bold uppercase tracking-widest"
        >
          Discard Changes
        </Button>
      </div>

      <Card className="bg-[#141414]/70 border-[#404040]/20 shadow-[0_0_100px_rgba(16,185,129,0.05)] relative group">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />

        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500 ml-1">
                First Name
              </label>
              <input
                type="text"
                value={editForm.first_name}
                onChange={(e) =>
                  setEditForm({ ...editForm, first_name: e.target.value })
                }
                placeholder="First Name"
                className="w-full bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder:text-neutral-700"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500 ml-1">
                Last Name
              </label>
              <input
                type="text"
                value={editForm.last_name}
                onChange={(e) =>
                  setEditForm({ ...editForm, last_name: e.target.value })
                }
                placeholder="Last Name"
                className="w-full bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/20 transition-all placeholder:text-neutral-700"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500 ml-1">
              Display Username
            </label>
            <div className="relative">
              <input
                type="text"
                value={editForm.username}
                onChange={(e) =>
                  setEditForm({ ...editForm, username: e.target.value })
                }
                className="w-full bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/20 transition-all font-mono"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] text-neutral-600 font-mono">
                @handle
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500 ml-1">
              Bio / Status
            </label>
            <textarea
              value={editForm.bio}
              onChange={(e) =>
                setEditForm({ ...editForm, bio: e.target.value })
              }
              className="w-full bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/30 focus:ring-1 focus:ring-emerald-500/20 transition-all min-h-[100px] resize-none placeholder:text-neutral-700"
              placeholder="Tell the world your coding story..."
            />
          </div>

          <div className="pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-6 pb-2">
            <button
              onClick={() => setDeleteDialogOpen(true)}
              className="text-red-500/50 hover:text-red-500 text-[10px] font-bold uppercase tracking-widest transition-colors"
            >
              Terminate Account
            </button>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Button
                variant="ghost"
                onClick={() => setIsEditing(false)}
                className="flex-1 sm:flex-none text-neutral-400 hover:text-white hover:bg-white/5 h-10 px-6 rounded-xl font-bold text-[11px]"
              >
                CANCEL
              </Button>
              <Button
                size="sm"
                onClick={handleSaveProfile}
                disabled={savingProfile}
                className="flex-1 sm:flex-none bg-emerald-500 text-black hover:bg-emerald-400 h-10 px-6 rounded-xl font-black text-[11px] shadow-[0_0_20px_rgba(16,185,129,0.2)] transition-all active:scale-95 whitespace-nowrap"
              >
                {savingProfile ? (
                  <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                ) : (
                  "DEPLOY CHANGES"
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EditProfileForm;
