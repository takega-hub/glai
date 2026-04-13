import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['admin-eva.midoma.ru', 'eva.midoma.ru', 'localhost'],
    cors: {
      origin: ['http://localhost:5173', 'http://eva.midoma.ru:5175', 'http://eva.midoma.ru:5176', 'http://5.101.179.47:5173', 'http://5.101.179.47:5176'],
      credentials: true
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
