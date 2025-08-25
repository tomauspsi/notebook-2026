import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Config base minimal: Vite cerca automaticamente vite.config.* alla root del progetto del browser
export default defineConfig({
  plugins: [react()],
  publicDir: "public"
});
