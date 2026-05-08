import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { HomeSkeleton } from "../bones/PageSkeletons";

const GameRedirectPage = () => {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/home");
  }, [navigate]);
  return <HomeSkeleton />;
};

export default GameRedirectPage;
