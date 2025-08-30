import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "", // percorsi relativi per hosting statico (es. GitHub Pages / sottocartelle)
  server: {
    port: 5173,
    open: false
  },
  build: {
    outDir: "dist",
    sourcemap: true
  }
});
