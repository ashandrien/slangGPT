import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      // Proxy API calls to the backend to avoid CORS during development
      '/slang': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/chat': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
        // Support OpenAI-backed endpoint and dev helpers
        '/openai_slang': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
        '/reload_slang': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
    },
  },
}))
