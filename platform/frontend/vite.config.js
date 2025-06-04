import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: false,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '4924bf6a.r35.cpolar.top',
      '.cpolar.top'
    ],
    hmr: {
      host: 'localhost'
    }
  }
})