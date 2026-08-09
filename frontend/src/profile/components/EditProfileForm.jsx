import React from "react";
import { Camera } from "lucide-react";

const EditProfileForm = ({
  editForm,
  setEditForm,
  setIsEditing,
  setDeleteDialogOpen,
  handleSaveProfile,
  savingProfile,
}) => {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-[15px] font-medium text-white">
          Edit Profile
        </h2>
        <button
          onClick={() => setIsEditing(false)}
          className="text-[12px] text-neutral-500 hover:text-white transition-colors"
        >
          Cancel
        </button>
      </div>

      {/* Form */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-6 space-y-5">
        {/* Name Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-[11px] font-medium text-neutral-500">
              First Name
            </label>
            <input
              type="text"
              value={editForm.first_name}
              onChange={(e) =>
                setEditForm({ ...editForm, first_name: e.target.value })
              }
              placeholder="First Name"
              className="w-full bg-black border border-neutral-800 rounded-lg px-3.5 py-2.5 text-[13px] text-white focus:outline-none focus:border-neutral-600 transition-colors placeholder:text-neutral-700"
            />
          </div>
          <div className="space-y-2">
            <label className="text-[11px] font-medium text-neutral-500">
              Last Name
            </label>
            <input
              type="text"
              value={editForm.last_name}
              onChange={(e) =>
                setEditForm({ ...editForm, last_name: e.target.value })
              }
              placeholder="Last Name"
              className="w-full bg-black border border-neutral-800 rounded-lg px-3.5 py-2.5 text-[13px] text-white focus:outline-none focus:border-neutral-600 transition-colors placeholder:text-neutral-700"
            />
          </div>
        </div>

        {/* Username */}
        <div className="space-y-2">
          <label className="text-[11px] font-medium text-neutral-500">
            Username
          </label>
          <input
            type="text"
            value={editForm.username}
            onChange={(e) =>
              setEditForm({ ...editForm, username: e.target.value })
            }
            className="w-full bg-black border border-neutral-800 rounded-lg px-3.5 py-2.5 text-[13px] text-white font-mono focus:outline-none focus:border-neutral-600 transition-colors"
          />
        </div>

        {/* Bio */}
        <div className="space-y-2">
          <label className="text-[11px] font-medium text-neutral-500">
            Bio
          </label>
          <textarea
            value={editForm.bio}
            onChange={(e) =>
              setEditForm({ ...editForm, bio: e.target.value })
            }
            className="w-full bg-black border border-neutral-800 rounded-lg px-3.5 py-2.5 text-[13px] text-white focus:outline-none focus:border-neutral-600 transition-colors min-h-[100px] resize-none placeholder:text-neutral-700"
            placeholder="Write a short bio..."
          />
        </div>

        {/* Actions */}
        <div className="pt-4 border-t border-neutral-900 flex items-center justify-between">
          <button
            onClick={() => setDeleteDialogOpen(true)}
            className="text-[11px] text-neutral-600 hover:text-red-400 transition-colors"
          >
            Delete account
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 rounded-lg text-[12px] font-medium text-neutral-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveProfile}
              disabled={savingProfile}
              className="px-5 py-2 rounded-lg bg-white text-black text-[12px] font-medium hover:bg-neutral-200 transition-colors active:scale-[0.97] disabled:opacity-50"
            >
              {savingProfile ? (
                <div className="w-3.5 h-3.5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
              ) : (
                "Save changes"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditProfileForm;
