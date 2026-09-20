import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "..", "");
  const backendPort = Number(env.BACKEND_PORT || "8000");
  if (!Number.isInteger(backendPort) || backendPort < 1 || backendPort > 65535) {
    throw new Error("BACKEND_PORT must be an integer between 1 and 65535");
  }
  const backendOrigin = `http://127.0.0.1:${backendPort}`;

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": backendOrigin,
        "/health": backendOrigin,
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      css: true,
      globals: true,
      pool: "threads",
      maxWorkers: 1,
      fileParallelism: false,
    },
  };
});
