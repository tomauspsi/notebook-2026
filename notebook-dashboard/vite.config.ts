import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tipi minimi per evitare di aggiungere @types/node
declare const process: { env?: Record<string, string | undefined> };

// Usa VITE_BASE_URL, che arriva dal workflow!
const env = (process?.env ?? {}) as Record<string, string | undefined>;
const base = env.VITE_BASE_URL || "/";

export default defineConfig({
  plugins: [react()],
  base
});
