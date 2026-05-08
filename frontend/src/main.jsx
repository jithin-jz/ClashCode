import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { configureBoneyard } from "boneyard-js/react";
import "./index.css";
import "./bones/registry.js";
import App from "./App.jsx";
import { SLog } from "./services/logger";

configureBoneyard({
  color: "#101010",
  darkColor: "#101010",
  animate: "shimmer",
  shimmerColor: "#1c1c1c",
  darkShimmerColor: "#1c1c1c",
  speed: "1.7s",
  transition: 180,
});

// Initialize Centralized Logging
SLog.init();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>,
);
