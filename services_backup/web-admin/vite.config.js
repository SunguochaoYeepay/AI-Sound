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
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9930',
        changeOrigin: true,
        secure: false,
        ws: true,
        logLevel: 'debug',
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`[PROXY REQ] ${req.method} ${req.url} -> ${options.target}${req.url}`)
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log(`[PROXY RES] ${proxyRes.statusCode} for ${req.url}`)
          })
          proxy.on('error', (err, req, res) => {
            console.error(`[PROXY ERROR] ${err.message} for ${req.url}`)
          })
        }
      },
      '/health': {
        target: 'http://127.0.0.1:9930',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://127.0.0.1:9930',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: './dist',
    emptyOutDir: true
  }
})