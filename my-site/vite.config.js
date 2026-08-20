import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// DocuMind React UI.
// - dev (`npm run dev`): served at '/', API routes proxied to the FastAPI
//   server (`./start-web.sh`, default :8000) so there's no CORS.
// - build (`npm run build`): emitted with a '/static/' base straight into the
//   FastAPI static dir, so the server serves this app at '/' in production.
//   emptyOutDir clears the old UI on every build.
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? '/static/' : '/',
  build: {
    outDir: '../src/documind/webapp/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/upload': { target: API_TARGET, changeOrigin: true },
      '/chat': { target: API_TARGET, changeOrigin: true },
      '/api': { target: API_TARGET, changeOrigin: true },
      '/healthz': { target: API_TARGET, changeOrigin: true },
    },
  },
}))
