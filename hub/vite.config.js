import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 8088,
    proxy: {
      "/api/kanban": {
        target: "http://localhost:8090",
        rewrite: (path) => path.replace(/^\/api\/kanban/, ""),
      },
    },
  },
});
