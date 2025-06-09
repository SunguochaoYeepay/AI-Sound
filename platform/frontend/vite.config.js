import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // 根据环境选择API目标 - 开发环境直连本地后端
  const API_TARGET = mode === 'development' 
    ? 'http://localhost:8000'      // 开发环境：直连本地后端
    : 'http://localhost:3001'      // 生产环境：通过nginx代理
  
  console.log(`[Vite配置] 模式: ${mode}, API代理目标: ${API_TARGET}`)

  return {
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      'pinia': resolve(__dirname, 'node_modules/pinia/dist/pinia.mjs')
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
      '.cpolar.top',
      'aisound.cpolar.top'
    ],
    hmr: {
        host: mode === 'development' ? 'localhost' : 'aisound.cpolar.top',
        clientPort: mode === 'development' ? 3000 : 443,
        protocol: mode === 'development' ? 'ws' : 'wss'
    },
    proxy: {
      '/audio': {
          target: API_TARGET,
        changeOrigin: true,
        secure: false
      },
      '/voice_profiles': {
          target: API_TARGET,
        changeOrigin: true,
        secure: false
      },
      '/api': {
          target: API_TARGET,
        changeOrigin: true,
        secure: false
        }
      }
    }
  }
})
