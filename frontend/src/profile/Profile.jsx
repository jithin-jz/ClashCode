import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Users, Plus } from "lucide-react";
import { Skeleton } from "boneyard-js/react";
import { Button } from "../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";

// Components
import CreatePostDialog from "../posts/CreatePostDialog";
import PostGrid from "../posts/PostGrid";
import ContributionGraph from "./components/ContributionGraph";
import ProfileHeader from "./components/ProfileHeader";
import ProfileInfo from "./components/ProfileInfo";
import ReferralSection from "./components/ReferralSection";
import EditProfileForm from "./components/EditProfileForm";
import UserListDialog from "./components/UserListDialog";

// Hooks
import { useProfile } from "../hooks/useProfile";

const Profile = () => {
  const navigate = useNavigate();
  const { username } = useParams();

  const {
    currentUser,
    profileUser,
    isOwnProfile,
    loading,
    userNotFound,
    isEditing,
    setIsEditing,
    suggestedUsers,
    editForm,
    setEditForm,
    uploadingAvatar,
    uploadingBanner,
    savingProfile,
    deleteDialogOpen,
    setDeleteDialogOpen,
    handleImageUpload,
    handleSaveProfile,
    handleFollowToggle,
    handleListFollowToggle,
    handleLogout,
    confirmDeleteAccount,
    fetchUserList,
    contributionData,
    loadingContributions,
    listType,
    setListType,
    userList,
    listLoading,
  } = useProfile(username);

  const [createPostOpen, setCreatePostOpen] = useState(false);
  const [refreshPosts, setRefreshPosts] = useState(0);
  const editSectionRef = useRef(null);

  // Auto-scroll to edit form when opened
  useEffect(() => {
    if (isEditing && editSectionRef.current) {
      editSectionRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [isEditing]);

  if (userNotFound) {
    return (
      <div className="h-screen w-full bg-[#000000] text-white flex flex-col items-center justify-center gap-6">
        <div className="text-center">
          <div className="w-20 h-20 rounded-xl bg-[#1a1a1a] border border-white/10 flex items-center justify-center mx-auto mb-6">
            <Users size={40} className="text-neutral-500" />
          </div>
          <h1 className="text-2xl font-semibold mb-2">User Not Found</h1>
          <p className="text-neutral-400 mb-6 text-sm">
            This user may have changed their username or doesn't exist.
          </p>
          <Button
            onClick={() => navigate("/home")}
            className="bg-white text-black hover:bg-zinc-200"
          >
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Skeleton name="profile-page" loading={loading}>
      <div className="relative w-full pb-20 sm:pb-0 text-white flex flex-col">
        <main className="relative z-10 flex-1 px-4 sm:px-10 lg:px-14 py-4">
          <div className="w-full mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Column - Profile Section */}
              <div className="lg:col-span-4 space-y-6 min-w-0">
                <Card className="bg-[#0a0a0a]/80 border-[#404040]/20 overflow-visible shadow-[0_20px_50px_rgba(0,0,0,0.5)] backdrop-blur-md">
                  <ProfileHeader
                    profileUser={profileUser}
                    isOwnProfile={isOwnProfile}
                    uploadingAvatar={uploadingAvatar}
                    uploadingBanner={uploadingBanner}
                    handleImageUpload={handleImageUpload}
                    setIsEditing={setIsEditing}
                    isEditing={isEditing}
                    handleLogout={handleLogout}
                  />
                  <div className="pt-10 sm:pt-12">
                    <ProfileInfo
                      profileUser={profileUser}
                      isOwnProfile={isOwnProfile}
                      handleFollowToggle={handleFollowToggle}
                      fetchUserList={fetchUserList}
                    />
                  </div>
                </Card>
              </div>

              {/* Middle Column - Feed/Edit */}
              <div
                ref={editSectionRef}
                className="lg:col-span-6 space-y-6 min-w-0"
              >
                {isEditing && isOwnProfile ? (
                  <EditProfileForm
                    editForm={editForm}
                    setEditForm={setEditForm}
                    setIsEditing={setIsEditing}
                    uploadingBanner={uploadingBanner}
                    handleImageUpload={handleImageUpload}
                    setDeleteDialogOpen={setDeleteDialogOpen}
                    handleSaveProfile={handleSaveProfile}
                    savingProfile={savingProfile}
                  />
                ) : (
                  <>
                    <ContributionGraph
                      data={contributionData}
                      loading={loadingContributions}
                    />
                    <div className="flex items-center justify-between mb-4 mt-8">
                      <h3 className="text-xl font-black italic text-white flex items-center gap-3">
                        <span className="w-1.5 h-6 bg-emerald-500 rounded-full" />
                        BATTLE FEED
                        <span className="text-[10px] bg-white/5 border border-white/10 px-2 py-0.5 rounded-lg text-neutral-500 font-mono not-italic tracking-normal">
                          {profileUser?.username}
                        </span>
                      </h3>
                      {isOwnProfile && (
                        <Button
                          size="sm"
                          onClick={() => setCreatePostOpen(true)}
                          className="bg-white text-black hover:bg-zinc-200 h-9 gap-2 rounded-xl font-bold text-xs shadow-lg"
                        >
                          <Plus size={16} /> NEW POST
                        </Button>
                      )}
                    </div>
                    <PostGrid
                      username={profileUser?.username}
                      refreshTrigger={refreshPosts}
                    />
                  </>
                )}
              </div>

              {/* Right Column - Suggestions */}
              <div className="lg:col-span-2 space-y-6 hidden lg:block">
                {isOwnProfile && suggestedUsers.length > 0 && (
                  <Card className="bg-[#0a0a0a]/60 border-[#404040]/20 backdrop-blur-sm">
                    <CardHeader className="p-3 border-b border-white/5">
                      <CardTitle className="text-[10px] font-black uppercase tracking-[0.2em] text-neutral-500/80">
                        Suggested For You
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 space-y-3">
                      {suggestedUsers.slice(0, 5).map((u) => (
                        <div
                          key={u.username}
                          className="flex items-center justify-between gap-3 group cursor-pointer"
                          onClick={() => navigate(`/profile/${u.username}`)}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <Avatar className="h-9 w-9 border border-white/5">
                              <AvatarImage
                                src={u.avatar_url || u.profile?.avatar_url}
                                alt={u.username}
                                className="object-cover"
                              />
                              <AvatarFallback className="bg-zinc-800 text-[10px] font-bold text-white">
                                {u.username?.[0]?.toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white truncate">
                                {u.username}
                              </div>
                              <div className="text-[10px] text-neutral-500 truncate">
                                Suggested for you
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </main>

        {/* Dialogs */}
        <UserListDialog
          listType={listType}
          setListType={setListType}
          userList={userList}
          listLoading={listLoading}
          handleListFollowToggle={handleListFollowToggle}
          currentUser={currentUser}
        />

        <CreatePostDialog
          open={createPostOpen}
          onOpenChange={setCreatePostOpen}
          onSuccess={() => setRefreshPosts((prev) => prev + 1)}
        />

        {/* Delete Confirmation */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="bg-[#141414] border-[#404040]/30 text-white max-w-sm">
            <DialogHeader>
              <DialogTitle className="text-red-500">Delete Account</DialogTitle>
              <DialogDescription className="text-neutral-400">
                This action is permanent. All your battles, scores, and profile
                data will be purged.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2 mt-4">
              <Button
                variant="ghost"
                onClick={() => setDeleteDialogOpen(false)}
                className="text-neutral-400 hover:text-white"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmDeleteAccount}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Permanently Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Skeleton>
  );
};

export default Profile;
