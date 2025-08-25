import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tipi minimi per evitare di aggiungere @types/node
declare const process: { env?: Record<string, string | undefined> };

// Nota: il file di config gira in Node. Usiamo BASE_URL (impostata dal workflow)
const env = (process?.env ?? {}) as Record<string, string | undefined>;
const base = env.BASE_URL || "/";

export default defineConfig({
  plugins: [react()],
  base
});