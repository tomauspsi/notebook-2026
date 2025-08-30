import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: './', // percorso relativo per GitHub Pages o hosting statico
  plugins: [react()],
  server: {
    port: 5173,
    open: true, // apre il browser in dev
  },
  build: {
    outDir: 'dist',
    sourcemap: true, // utile per debug
    rollupOptions: {
      output: {
        manualChunks: undefined, // build compatta, un unico bundle
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src', // shortcut per import assoluti
    },
  },
  define: {
    'process.env': {},
  },
})
