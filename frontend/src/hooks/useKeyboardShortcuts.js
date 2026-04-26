import { useEffect } from "react";

/**
 * Hook to manage global keyboard shortcuts for the application.
 */
export const useKeyboardShortcuts = (user, navigate, setChatOpen, setLeaderboardOpen) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      const key = typeof e?.key === "string" ? e.key.toLowerCase() : "";
      if (!key) return;
      if (!(e.ctrlKey || e.metaKey)) return;

      switch (key) {
        case "b":
          e.preventDefault();
          setChatOpen((prev) => !prev);
          break;
        case "l":
          e.preventDefault();
          setLeaderboardOpen((prev) => !prev);
          break;
        case "p":
          e.preventDefault();
          if (user) navigate("/profile");
          break;
        case "x":
          e.preventDefault();
          if (user) navigate("/shop");
          break;
        case "s":
          e.preventDefault();
          if (user) navigate("/store");
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [user, navigate, setChatOpen, setLeaderboardOpen]);
};
