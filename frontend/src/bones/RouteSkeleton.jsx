import React from "react";
import {
  AchievementsSkeleton,
  AdminSkeleton,
  BuyXpSkeleton,
  CertificateVerifySkeleton,
  GenericSkeleton,
  HomeSkeleton,
  LandingSkeleton,
  LoginSkeleton,
  MarketplaceSkeleton,
  OAuthCallbackSkeleton,
  ProfileSkeleton,
} from "./PageSkeletons";
import ChallengeWorkspaceSkeleton from "../game/ChallengeWorkspaceSkeleton";

export const PageSkeletonForPath = ({ pathname = "/" }) => {
  if (pathname.startsWith("/level")) return <ChallengeWorkspaceSkeleton />;
  if (pathname.startsWith("/admin")) return <AdminSkeleton />;
  if (pathname.startsWith("/store")) return <MarketplaceSkeleton />;
  if (pathname.startsWith("/shop") || pathname.startsWith("/buy-xp")) {
    return <BuyXpSkeleton />;
  }
  if (pathname.startsWith("/profile")) return <ProfileSkeleton />;
  if (pathname.startsWith("/achievements")) return <AchievementsSkeleton />;
  if (pathname.startsWith("/auth/")) return <OAuthCallbackSkeleton />;
  if (pathname.startsWith("/verify/")) return <CertificateVerifySkeleton />;
  if (pathname === "/home" || pathname === "/game") return <HomeSkeleton />;
  if (pathname === "/login") return <LoginSkeleton />;
  if (pathname === "/") return <LandingSkeleton />;
  return <GenericSkeleton />;
};
