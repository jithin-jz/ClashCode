import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../stores/useAuthStore";
import { useHomeData } from "../hooks/useHomeData";

import { Skeleton } from "boneyard-js/react";
import { HomeSkeleton } from "../bones/PageSkeletons";
// Components
import LevelModal from "../game/LevelModal";
import { ChallengeMap } from "../home";
import CertificateModal from "../components/CertificateModal";

const Home = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // Use centralized data hook
  const {
    levels,
    isLoading,
    certificateModalOpen,
    setCertificateModalOpen,
    userCertificate,
    isCertificateLoading,
    handleCertificateClick,
    CERTIFICATE_SLUG,
  } = useHomeData(user);

  // Scroll position persistence
  useEffect(() => {
    // 1. Restore scroll position ONLY after loading is finished and levels are ready
    if (!isLoading && levels?.length > 0) {
      const savedPosition = sessionStorage.getItem("homeScrollPos");
      if (savedPosition) {
        // Small delay to ensure the DOM has rendered the map fully
        setTimeout(() => {
          window.scrollTo({
            top: parseInt(savedPosition, 10),
            behavior: "instant",
          });
        }, 100);
      }
    }

    // 2. Save scroll position on scroll
    const handleScroll = () => {
      sessionStorage.setItem("homeScrollPos", window.scrollY.toString());
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [isLoading, levels]);

  // Local UI State
  const [selectedLevel, setSelectedLevel] = useState(null);

  const handleLevelClick = async (level) => {
    if (!user) {
      navigate("/login");
      return;
    }

    if (level.unlocked) {
      const isCertificate =
        level.slug === CERTIFICATE_SLUG || level.type === "CERTIFICATE";
      if (isCertificate) {
        handleCertificateClick();
      } else {
        setSelectedLevel(level);
      }
    }
  };

  return (
    <Skeleton name="home-page" loading={isLoading} fallback={<HomeSkeleton />}>
      <div className="w-full relative">
        <ChallengeMap
          user={user}
          levels={levels}
          handleLevelClick={handleLevelClick}
        />

        {selectedLevel && (
          <LevelModal
            selectedLevel={selectedLevel}
            onClose={() => setSelectedLevel(null)}
          />
        )}

        <CertificateModal
          isOpen={certificateModalOpen}
          onClose={() => setCertificateModalOpen(false)}
          certificate={userCertificate}
          isLoading={isCertificateLoading}
        />
      </div>
    </Skeleton>
  );
};

export default Home;
