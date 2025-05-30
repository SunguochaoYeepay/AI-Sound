import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 8929,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:9930',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`[PROXY] ${req.method} ${req.url} -> ${options.target}${req.url}`)
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log(`[PROXY] Response ${proxyRes.statusCode} for ${req.url}`)
          })
        }
      },
      '/health': {
        target: 'http://localhost:9930',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: './dist',
    emptyOutDir: true
  }
})