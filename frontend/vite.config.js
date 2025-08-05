import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // This exposes the dev server to your network
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  // Configure for network access
  define: {
    // You can override this with environment variables if needed
    __API_URL__: JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000')
  }
})
