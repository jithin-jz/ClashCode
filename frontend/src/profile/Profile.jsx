import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Plus } from "lucide-react";
import { Skeleton } from "boneyard-js/react";
import { ProfileSkeleton } from "../bones/PageSkeletons";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";

// Components
import CreatePostDialog from "../posts/CreatePostDialog";
import PostGrid from "../posts/PostGrid";
import ContributionGraph from "./components/ContributionGraph";
import ProfileHeader from "./components/ProfileHeader";
import ProfileInfo from "./components/ProfileInfo";
import EditProfileForm from "./components/EditProfileForm";
import UserListDialog from "./components/UserListDialog";
import UserNotFound from "./components/UserNotFound";
import DeleteAccountDialog from "./components/DeleteAccountDialog";
import SuggestionsSidebar from "./components/SuggestionsSidebar";

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
    return <UserNotFound onBackHome={() => navigate("/home")} />;
  }

  return (
    <Skeleton
      name="profile-page"
      loading={loading}
      fallback={<ProfileSkeleton />}
    >
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
                    handleSaveProfile={() => handleSaveProfile(editForm)}
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
                {isOwnProfile && (
                  <SuggestionsSidebar
                    users={suggestedUsers}
                    onUserClick={(u) => navigate(`/profile/${u}`)}
                  />
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

        <DeleteAccountDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          onConfirm={confirmDeleteAccount}
        />
      </div>
    </Skeleton>
  );
};

export default Profile;
