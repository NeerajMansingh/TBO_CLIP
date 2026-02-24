import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/match': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/confirm': 'http://127.0.0.1:8000',
      '/destinations': 'http://127.0.0.1:8000'
    }
  }
})
