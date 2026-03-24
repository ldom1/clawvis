import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, ["HUB_", "KANBAN_"]);
  const port = Number(env.HUB_PORT || 8088);
  const kanbanPort = Number(env.KANBAN_API_PORT || 8090);

  return {
    server: {
      host: true,
      port,
      strictPort: true,
      proxy: {
        "/api/kanban": {
          target: `http://127.0.0.1:${kanbanPort}`,
          rewrite: (p) => p.replace(/^\/api\/kanban/, ""),
        },
      },
    },
    preview: {
      host: true,
      port,
    },
  };
});
