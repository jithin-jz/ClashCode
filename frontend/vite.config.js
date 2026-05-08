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
      routes: [
        "/",
        "/login",
        "/auth/github/callback",
        "/auth/google/callback",
        "/home",
        "/profile",
        "/profile/boneyard-bot",
        "/achievements",
        "/store",
        "/shop",
        "/buy-xp",
        "/verify/boneyard-certificate",
        "/level/1",
        "/admin/dashboard",
      ],
      debug: false,
      skipInitial: true,
    }),
    sentryVitePlugin({
      org: process.env.SENTRY_ORG || "clashcode",
      project: process.env.SENTRY_PROJECT || "frontend",
      authToken: process.env.SENTRY_AUTH_TOKEN,
      release: {
        name:
          process.env.SENTRY_RELEASE ||
          process.env.GITHUB_SHA ||
          process.env.VITE_APP_VERSION,
      },
      sourcemaps: { assets: "./dist/**" },
      disable: !process.env.SENTRY_AUTH_TOKEN,
      telemetry: false,
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
    sourcemap: true,
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
          if (pkg === "framer-motion") return "vendor-motion";
          if (pkg.startsWith("@radix-ui/")) return "vendor-radix";
          if (pkg === "emoji-picker-react") return "vendor-emoji";
          if (
            pkg === "react-markdown" ||
            pkg.startsWith("remark-") ||
            pkg.startsWith("rehype-")
          ) {
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
      clientPort: 5173,
    },
    proxy: {
      "/api": {
        target: "http://localhost",
        changeOrigin: true,
      },
      "/ai": {
        target: "http://localhost",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost",
        ws: true,
        changeOrigin: true,
      },
      "/chat": {
        target: "http://localhost",
        changeOrigin: true,
      },
      "/media": {
        target: "http://localhost",
        changeOrigin: true,
      },
    },
  },
});
