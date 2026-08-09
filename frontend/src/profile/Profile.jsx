import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Skeleton } from "boneyard-js/react";
import { toast } from "sonner";
import { ProfileSkeleton } from "../bones/PageSkeletons";

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
import GitHubSyncSection from "./components/GitHubSyncSection";

// Hooks
import { useProfile } from "../hooks/useProfile";

const Profile = () => {
  const navigate = useNavigate();
  const { username } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const githubStatus = searchParams.get("github");
    if (githubStatus === "connected") {
      toast.success("GitHub connected! Your solutions will auto-sync.");
      searchParams.delete("github");
      setSearchParams(searchParams, { replace: true });
    } else if (githubStatus === "error") {
      const reason = searchParams.get("reason") || "Unknown error";
      toast.error(`GitHub connection failed: ${reason.replace(/_/g, " ")}`);
      searchParams.delete("github");
      searchParams.delete("reason");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

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
      <div className="w-full min-h-[calc(100vh-3.5rem)] text-white">
        <div className="w-full px-3 sm:px-6 lg:px-10 xl:px-16 py-4 sm:py-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

            {/* ─── Left: Profile Card ─────────────────────────────── */}
            <div className="lg:col-span-3 min-w-0">
              <div className="lg:sticky lg:top-20 space-y-4">
                <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-visible">
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
                </div>
              </div>
            </div>

            {/* ─── Middle: Content ────────────────────────────────── */}
            <div
              ref={editSectionRef}
              className="lg:col-span-6 min-w-0 space-y-5"
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

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-[13px] font-medium text-neutral-400">
                        Posts
                      </h3>
                      {isOwnProfile && (
                        <button
                          onClick={() => setCreatePostOpen(true)}
                          className="text-[12px] text-neutral-600 hover:text-white transition-colors"
                        >
                          New post →
                        </button>
                      )}
                    </div>
                    <PostGrid
                      username={profileUser?.username}
                      refreshTrigger={refreshPosts}
                    />
                  </div>
                </>
              )}
            </div>

            {/* ─── Right: Suggestions + GitHub ────────────────────── */}
            <div className="lg:col-span-3 min-w-0">
              <div className="lg:sticky lg:top-20 space-y-4">
                {isOwnProfile && (
                  <SuggestionsSidebar
                    users={suggestedUsers}
                    onUserClick={(u) => navigate(`/profile/${u}`)}
                  />
                )}
                {isOwnProfile && <GitHubSyncSection />}
              </div>
            </div>

          </div>
        </div>

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
