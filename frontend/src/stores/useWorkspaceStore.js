import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Persisted store for user workspace preferences.
 */
const useWorkspaceStore = create(
  persist(
    (set) => ({
      // --- Layout & Editor Preferences ---
      fontSize: 14,
      fontFamily: "'Fira Code', 'JetBrains Mono', Consolas, monospace",
      theme: "vs-dark",
      showLineNumbers: true,
      minimapEnabled: false,
      mobileTab: "problem",

      // --- Console Preferences ---
      consoleOpen: true,
      consoleHeight: 250,

      // --- Actions ---
      setFontSize: (size) => set({ fontSize: size }),
      setFontFamily: (fontFamily) => set({ fontFamily }),
      setTheme: (theme) => set({ theme }),
      toggleLineNumbers: () =>
        set((state) => ({ showLineNumbers: !state.showLineNumbers })),
      setMobileTab: (tab) => set({ mobileTab: tab }),
      setConsoleOpen: (isOpen) => set({ consoleOpen: isOpen }),
      setConsoleHeight: (height) => set({ consoleHeight: height }),

      // Reset to defaults
      resetToDefaults: () =>
        set({
          fontSize: 14,
          fontFamily: "'Fira Code', 'JetBrains Mono', Consolas, monospace",
          theme: "vs-dark",
          showLineNumbers: true,
          minimapEnabled: false,
        }),
    }),
    {
      name: "clashcode-workspace-prefs",
    },
  ),
);

export default useWorkspaceStore;
