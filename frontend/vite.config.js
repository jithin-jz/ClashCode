import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";
import { sentryVitePlugin } from "@sentry/vite-plugin";

function getPackageName(id) {
  const match = id.split(/node_modules[\\/]/)[1];
  if (!match) return null;
  const parts = match.split(/[\\/]/);
  if (parts[0]?.startsWith("@")) {
    return `${parts[0]}/${parts[1]}`;
  }
  return parts[0];
}

import { boneyardPlugin } from "boneyard-js/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    boneyardPlugin({
      routes: ["/login", "/home", "/profile", "/achievements", "/store"],
      debug: true,
    }),
    sentryVitePlugin({
      org: "clashcode",
      project: "frontend",
    }),
  ],
  resolve: {
    alias: {
      "lucide-react": fileURLToPath(
        new URL("./src/icons/lucide-react.jsx", import.meta.url),
      ),
    },
  },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          const pkg = getPackageName(id);
          if (!pkg) return "vendor";

          if (pkg === "react" || pkg === "react-dom" || pkg === "scheduler") {
            return "vendor-react-core";
          }
          if (pkg.startsWith("react-router")) return "vendor-router";
          if (pkg === "firebase" || pkg.startsWith("@firebase/")) {
            return "vendor-firebase";
          }
          if (pkg === "monaco-editor" || pkg === "@monaco-editor/react") {
            return "vendor-monaco";
          }
          if (pkg === "framer-motion" || pkg === "motion")
            return "vendor-motion";
          if (pkg.startsWith("@radix-ui/")) return "vendor-radix";
          if (pkg === "emoji-picker-react") return "vendor-emoji";
          if (pkg === "react-markdown" || pkg.startsWith("remark-") || pkg.startsWith("rehype-")) {
            return "vendor-markdown";
          }
          if (pkg === "@sentry/react" || pkg.startsWith("@sentry/")) {
            return "vendor-sentry";
          }
          return "vendor";
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    strictPort: false,
    hmr: {
      clientPort: 80,
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1",
        changeOrigin: true,
      },
      "/ai": {
        target: "http://127.0.0.1",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://127.0.0.1",
        ws: true,
        changeOrigin: true,
      },
      "/chat": {
        target: "http://127.0.0.1",
        changeOrigin: true,
      },
      "/media": {
        target: "http://127.0.0.1",
        changeOrigin: true,
      },
    },
  },
});
