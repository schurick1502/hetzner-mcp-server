import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Erlaubt Health-Checks des Watchdog (via host.docker.internal); Vite blockt sonst mit 403
    allowedHosts: ['host.docker.internal'],
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
