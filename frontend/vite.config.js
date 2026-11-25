import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En local, l'API tourne sur localhost:8000 ; dans Docker Compose, sur http://api:8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.API_URL || 'http://localhost:8000',
    },
  },
})
