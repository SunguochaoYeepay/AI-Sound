/**
 * 全局轮询管理工具
 * 用于统一管理和清理轮询定时器，防止内存泄漏
 */

class PollingManager {
  constructor() {
    this.timers = new Map()
    this.setupGlobalCleanup()
  }

  /**
   * 创建一个新的轮询
   * @param {string} id - 轮询的唯一标识
   * @param {Function} callback - 轮询回调函数
   * @param {number} interval - 轮询间隔（毫秒）
   * @param {Object} options - 选项配置
   */
  createPolling(id, callback, interval = 2000, options = {}) {
    // 清除已存在的同名轮询
    this.clearPolling(id)

    const {
      maxErrors = 5,
      maxDuration = 30 * 60 * 1000, // 30分钟
      onError = () => {},
      onStop = () => {},
      immediate = false
    } = options

    let errorCount = 0
    const startTime = Date.now()

    const execute = async () => {
      try {
        // 检查是否超时
        if (Date.now() - startTime > maxDuration) {
          console.warn(`轮询 ${id} 超时，自动停止`)
          this.clearPolling(id)
          onStop('timeout')
          return
        }

        // 执行回调
        const result = await callback()
        
        // 重置错误计数
        errorCount = 0

        // 检查是否需要停止
        if (result === false) {
          this.clearPolling(id)
          onStop('manual')
        }
      } catch (error) {
        console.error(`轮询 ${id} 出错:`, error)
        errorCount++
        onError(error, errorCount)

        // 错误次数过多时停止
        if (errorCount >= maxErrors) {
          console.error(`轮询 ${id} 连续${maxErrors}次失败，自动停止`)
          this.clearPolling(id)
          onStop('error')
        }
      }
    }

    // 立即执行一次（可选）
    if (immediate) {
      execute()
    }

    // 创建定时器
    const timer = setInterval(execute, interval)
    
    // 存储定时器信息
    this.timers.set(id, {
      timer,
      startTime,
      interval,
      callback,
      options
    })

    console.log(`创建轮询 ${id}，间隔 ${interval}ms`)
    return timer
  }

  /**
   * 清除指定轮询
   * @param {string} id - 轮询标识
   */
  clearPolling(id) {
    const polling = this.timers.get(id)
    if (polling) {
      clearInterval(polling.timer)
      this.timers.delete(id)
      console.log(`清除轮询 ${id}`)
      return true
    }
    return false
  }

  /**
   * 清除所有轮询
   */
  clearAllPolling() {
    const count = this.timers.size
    this.timers.forEach((polling, id) => {
      clearInterval(polling.timer)
    })
    this.timers.clear()
    console.log(`清除了 ${count} 个轮询`)
  }

  /**
   * 获取当前活跃的轮询列表
   */
  getActivePolling() {
    return Array.from(this.timers.keys())
  }

  /**
   * 检查轮询是否存在
   * @param {string} id - 轮询标识
   */
  hasPolling(id) {
    return this.timers.has(id)
  }

  /**
   * 设置全局清理机制
   */
  setupGlobalCleanup() {
    // 页面卸载前清理
    window.addEventListener('beforeunload', () => {
      this.clearAllPolling()
    })

    // 页面隐藏时暂停（可选）
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('页面隐藏，考虑暂停轮询')
        // 这里可以添加暂停逻辑
      } else {
        console.log('页面显示，恢复轮询')
        // 这里可以添加恢复逻辑
      }
    })
  }
}

// 创建全局实例
const pollingManager = new PollingManager()

export default pollingManager

// 便捷方法
export const createPolling = (id, callback, interval, options) => {
  return pollingManager.createPolling(id, callback, interval, options)
}

export const clearPolling = (id) => {
  return pollingManager.clearPolling(id)
}

export const clearAllPolling = () => {
  return pollingManager.clearAllPolling()
} 