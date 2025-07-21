import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // 根据环境选择API目标
  // 开发模式：代理到本地开发服务器 8001 端口
  // 生产模式：代理到 Docker 服务 8000 端口
  const API_TARGET = mode === 'development' 
    ? 'http://localhost:8001'  // 本地开发端口
    : 'http://localhost:8000'  // Docker 生产端口
  
  console.log(`[Vite配置] 模式: ${mode}, API代理目标: ${API_TARGET}`)

  return {
    root: resolve(__dirname, '.'),  // 明确指定项目根目录
    build: {
      outDir: resolve(__dirname, 'dist'),  // 明确指定输出目录
    },
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
        // API路由（包含音频）- 最高优先级
        '/api': {
          target: API_TARGET,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('[Vite API Proxy] 代理错误:', err.message)
            })
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('[Vite API Proxy] 代理请求:', req.method, req.url)
            })
          }
        },
        // 向后兼容的音频代理（重定向到/api/v1/audio）
        '/audio': {
          target: API_TARGET,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/audio/, '/api/v1/audio')
        },
        '/voice_profiles': {
          target: API_TARGET,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/voice_profiles/, '/api/v1/voice_profiles')
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