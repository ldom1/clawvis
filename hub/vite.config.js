import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, ["HUB_", "KANBAN_", "AGENT_"]);
  const port = Number(env.HUB_PORT || 8088);
  const kanbanPort = Number(env.KANBAN_API_PORT || 8090);
  const memoryPort = Number(env.HUB_MEMORY_API_PORT || 8091);
  const agentPort = Number(env.AGENT_PORT || 8092);
  const appsOrigin = (env.HUB_APPS_ORIGIN || "").trim();

  return {
    plugins: [react()],
    server: {
      host: true,
      port,
      strictPort: false,
      proxy: {
        "/api/hub/agent": {
          target: `http://127.0.0.1:${agentPort}`,
          rewrite: (p) => p.replace(/^\/api\/hub\/agent/, ""),
        },
        "/api/hub/chat": {
          target: `http://127.0.0.1:${kanbanPort}`,
          rewrite: (p) => p.replace(/^\/api\/hub\/chat/, "/hub/chat"),
        },
        "/api/hub/kanban": {
          target: `http://127.0.0.1:${kanbanPort}`,
          rewrite: (p) => p.replace(/^\/api\/hub\/kanban/, ""),
        },
        "/api/hub/setup": {
          target: `http://127.0.0.1:${kanbanPort}`,
          rewrite: (p) => p.replace(/^\/api\/hub\/setup/, "/setup"),
        },
        "/api/hub/memory": {
          target: `http://127.0.0.1:${memoryPort}`,
          rewrite: (p) => p.replace(/^\/api\/hub\/memory/, ""),
        },
        ...(appsOrigin
          ? {
              "/apps": {
                target: appsOrigin,
                changeOrigin: true,
              },
            }
          : {}),
      },
    },
    preview: {
      host: true,
      port,
      strictPort: false,
    },
  };
});
