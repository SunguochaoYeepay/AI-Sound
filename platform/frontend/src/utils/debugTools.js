/**
 * 调试工具
 * 用于检查和修复异常的轮询请求
 */

import { message } from 'ant-design-vue'

class DebugTools {
  constructor() {
    this.originalSetInterval = window.setInterval
    this.originalClearInterval = window.clearInterval
    this.activeTimers = new Map()
    this.setupInterceptors()
  }

  /**
   * 设置定时器拦截器
   */
  setupInterceptors() {
    // 拦截 setInterval
    window.setInterval = (callback, delay, ...args) => {
      const timer = this.originalSetInterval.call(window, callback, delay, ...args)
      
      // 记录定时器信息
      this.activeTimers.set(timer, {
        callback: callback.toString(),
        delay,
        createdAt: new Date(),
        stack: new Error().stack
      })
      
      return timer
    }

    // 拦截 clearInterval
    window.clearInterval = (timer) => {
      this.activeTimers.delete(timer)
      return this.originalClearInterval.call(window, timer)
    }
  }

  /**
   * 获取所有活跃的定时器
   */
  getActiveTimers() {
    return Array.from(this.activeTimers.entries()).map(([id, info]) => ({
      id,
      ...info,
      duration: Date.now() - info.createdAt.getTime()
    }))
  }

  /**
   * 查找可疑的轮询请求
   */
  findSuspiciousPolling() {
    const timers = this.getActiveTimers()
    
    return timers.filter(timer => {
      // 查找包含 progress、API 调用的定时器
      const hasProgress = timer.callback.includes('progress') || 
                         timer.callback.includes('getProgress') ||
                         timer.callback.includes('apiClient')
      
      // 运行时间超过5分钟的定时器
      const longRunning = timer.duration > 5 * 60 * 1000
      
      // 间隔时间在1-5秒之间的定时器（典型轮询间隔）
      const typicalPolling = timer.delay >= 1000 && timer.delay <= 5000
      
      return hasProgress || (longRunning && typicalPolling)
    })
  }

  /**
   * 清除所有可疑的轮询
   */
  clearSuspiciousPolling() {
    const suspicious = this.findSuspiciousPolling()
    
    if (suspicious.length === 0) {
      message.info('未发现可疑的轮询请求')
      return 0
    }

    suspicious.forEach(timer => {
      console.log('清除可疑轮询:', timer)
      this.originalClearInterval.call(window, timer.id)
      this.activeTimers.delete(timer.id)
    })

    message.success(`已清除 ${suspicious.length} 个可疑轮询请求`)
    return suspicious.length
  }

  /**
   * 清除所有定时器
   */
  clearAllTimers() {
    const count = this.activeTimers.size
    
    this.activeTimers.forEach((info, id) => {
      this.originalClearInterval.call(window, id)
    })
    
    this.activeTimers.clear()
    message.warning(`已清除所有 ${count} 个定时器`)
    return count
  }

  /**
   * 检查网络请求状态
   */
  checkNetworkRequests() {
    // 检查正在进行的网络请求
    if (window.performance && window.performance.getEntriesByType) {
      const requests = window.performance.getEntriesByType('navigation')
      const resources = window.performance.getEntriesByType('resource')
      
      // 查找最近的API请求
      const recentApiRequests = resources
        .filter(entry => {
          return entry.name.includes('/api/') && 
                 entry.name.includes('progress') &&
                 (Date.now() - entry.startTime) < 10000 // 最近10秒
        })
        .sort((a, b) => b.startTime - a.startTime)
        .slice(0, 10)

      console.log('最近的API请求:', recentApiRequests)
      return recentApiRequests
    }
    
    return []
  }

  /**
   * 生成诊断报告
   */
  generateDiagnosticReport() {
    const activeTimers = this.getActiveTimers()
    const suspiciousPolling = this.findSuspiciousPolling()
    const networkRequests = this.checkNetworkRequests()
    
    const report = {
      timestamp: new Date().toISOString(),
      activeTimers: activeTimers.length,
      suspiciousPolling: suspiciousPolling.length,
      recentNetworkRequests: networkRequests.length,
      details: {
        timers: activeTimers,
        suspicious: suspiciousPolling,
        network: networkRequests
      }
    }

    console.group('🔍 轮询诊断报告')
    console.log('活跃定时器数量:', activeTimers.length)
    console.log('可疑轮询数量:', suspiciousPolling.length)
    console.log('最近网络请求:', networkRequests.length)
    console.log('详细信息:', report.details)
    console.groupEnd()

    return report
  }

  /**
   * 一键修复
   */
  quickFix() {
    console.log('🔧 开始一键修复...')
    
    // 生成诊断报告
    const report = this.generateDiagnosticReport()
    
    // 清除可疑轮询
    const clearedCount = this.clearSuspiciousPolling()
    
    // 强制垃圾回收（如果支持）
    if (window.gc) {
      window.gc()
    }

    message.success(`修复完成！清除了 ${clearedCount} 个异常轮询`)
    
    return {
      report,
      clearedCount
    }
  }
}

// 创建全局实例
const debugTools = new DebugTools()

// 暴露到全局，方便调试
window.debugTools = debugTools

export default debugTools

// 暴露常用方法
export const clearSuspiciousPolling = () => debugTools.clearSuspiciousPolling()
export const quickFix = () => debugTools.quickFix()
export const getDiagnosticReport = () => debugTools.generateDiagnosticReport()

// 添加快捷键支持（Ctrl+Shift+F）
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && e.key === 'F') {
    e.preventDefault()
    debugTools.quickFix()
  }
}) 