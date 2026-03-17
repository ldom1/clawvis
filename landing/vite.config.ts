import { defineConfig } from 'vite'

export default defineConfig({
  base: '/',
  build: {
    // ⚠️ VPS-specific path — cloned at /home/lgiron/Lab/dombot-labos/
    // Adjust outDir on another machine
    outDir: '../../hub/public',  // resolves to /home/lgiron/Lab/hub/public/ (nginx VPS)
    assetsDir: 'assets',
    emptyOutDir: false, // ⚠️ hub/public/ contains other apps — do NOT empty
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
