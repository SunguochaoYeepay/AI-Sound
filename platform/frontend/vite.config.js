import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // 根据环境选择API目标 - 使用8000端口（后端实际端口）
  const API_TARGET = 'http://localhost:8000'
  
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
      strictPort: true,
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
        },
        '/ws': {
          target: API_TARGET.replace('http:', 'ws:'),
          ws: true,
          changeOrigin: true,
          secure: false,
          onError: (err, req, res) => {
            console.log('[Vite WS Proxy] WebSocket代理错误:', err.message)
          },
          onProxyReqWs: (proxyReq, req, socket) => {
            socket.on('error', (err) => {
              console.log('[Vite WS Proxy] Socket错误:', err.message)
            })
          },
          onOpen: (proxySocket) => {
            console.log('[Vite WS Proxy] WebSocket代理连接已建立')
            proxySocket.on('error', (err) => {
              console.log('[Vite WS Proxy] ProxySocket错误:', err.message)
            })
          },
          onClose: (res, socket, head) => {
            console.log('[Vite WS Proxy] WebSocket代理连接已关闭')
          }
        }
      }
    }
  }
})