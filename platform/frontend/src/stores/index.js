/**
 * Pinia状态管理主入口
 * 管理应用的全局状态
 */

import { createPinia } from 'pinia'

// 创建Pinia实例
const pinia = createPinia()

export default pinia

// 导出所有store
export { useAppStore } from './app'
export { useUserStore } from './user'
export { useBookStore } from './book'
export { useAnalysisStore } from './analysis'
export { useSynthesisStore } from './synthesis'
export { useWebSocketStore } from './websocket'
