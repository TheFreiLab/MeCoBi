import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build output goes straight into the package's static dir so FastAPI serves it
// (the backend serves the static React build). Dev server proxies
// /api to the running backend.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "../src/mecobi/web/static",
    emptyOutDir: true,
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
