/**
 * 虚拟滚动工具类
 * 用于处理大量数据的虚拟滚动、搜索和分页
 */

export class VirtualScrollHelper {
  constructor(options = {}) {
    this.pageSize = options.pageSize || 100
    this.totalItems = options.totalItems || 0
    this.dataSource = options.dataSource || []
    this.searchFields = options.searchFields || ['title', 'content']
    this.sortField = options.sortField || 'id'
    this.sortOrder = options.sortOrder || 'asc'

    this.currentPage = 1
    this.searchKeyword = ''
    this.filteredData = []
    this.cache = new Map()

    this.init()
  }

  /**
   * 初始化
   */
  init() {
    this.filteredData = [...this.dataSource]
  }

  /**
   * 搜索数据
   * @param {string} keyword - 搜索关键词
   * @param {Object} options - 搜索选项
   * @returns {Promise<Object>} 搜索结果
   */
  async search(keyword, options = {}) {
    this.searchKeyword = keyword.trim()
    this.currentPage = 1

    if (!this.searchKeyword) {
      this.filteredData = [...this.dataSource]
    } else {
      const cacheKey = `search_${keyword}`

      if (this.cache.has(cacheKey)) {
        this.filteredData = this.cache.get(cacheKey)
      } else {
        this.filteredData = this.performSearch(this.searchKeyword)
        this.cache.set(cacheKey, [...this.filteredData])
      }
    }

    return this.getPageData(1)
  }

  /**
   * 执行搜索
   * @param {string} keyword - 搜索关键词
   * @returns {Array} 过滤后的数据
   */
  performSearch(keyword) {
    const lowerKeyword = keyword.toLowerCase()

    return this.dataSource.filter((item) => {
      return this.searchFields.some((field) => {
        const value = this.getNestedValue(item, field)
        return value && value.toString().toLowerCase().includes(lowerKeyword)
      })
    })
  }

  /**
   * 获取嵌套对象的值
   * @param {Object} obj - 对象
   * @param {string} path - 路径，如 'user.name'
   * @returns {*} 值
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => {
      return current ? current[key] : undefined
    }, obj)
  }

  /**
   * 获取分页数据
   * @param {number} page - 页码
   * @returns {Promise<Object>} 分页数据
   */
  async getPageData(page = 1) {
    this.currentPage = page

    const startIndex = (page - 1) * this.pageSize
    const endIndex = startIndex + this.pageSize

    const pageData = this.filteredData.slice(startIndex, endIndex)

    return {
      data: pageData,
      total: this.filteredData.length,
      page: page,
      pageSize: this.pageSize,
      hasMore: endIndex < this.filteredData.length,
      totalPages: Math.ceil(this.filteredData.length / this.pageSize)
    }
  }

  /**
   * 加载更多数据
   * @returns {Promise<Object>} 下一页数据
   */
  async loadMore() {
    if (this.hasMore()) {
      return this.getPageData(this.currentPage + 1)
    }
    return { data: [], hasMore: false }
  }

  /**
   * 是否有更多数据
   * @returns {boolean}
   */
  hasMore() {
    const startIndex = this.currentPage * this.pageSize
    return startIndex < this.filteredData.length
  }

  /**
   * 更新数据源
   * @param {Array} newData - 新数据
   */
  updateDataSource(newData) {
    this.dataSource = [...newData]
    this.totalItems = newData.length
    this.cache.clear()

    // 重新应用当前搜索
    if (this.searchKeyword) {
      this.performSearch(this.searchKeyword)
    } else {
      this.filteredData = [...this.dataSource]
    }
  }

  /**
   * 添加新项目
   * @param {Object} newItem - 新项目
   */
  addItem(newItem) {
    this.dataSource.unshift(newItem)
    this.totalItems++
    this.cache.clear()

    // 重新应用当前搜索
    if (this.searchKeyword) {
      this.performSearch(this.searchKeyword)
    } else {
      this.filteredData = [...this.dataSource]
    }
  }

  /**
   * 更新项目
   * @param {string|number} id - 项目ID
   * @param {Object} updates - 更新内容
   */
  updateItem(id, updates) {
    const updateItem = (items) => {
      const index = items.findIndex((item) => item.id === id)
      if (index !== -1) {
        items[index] = { ...items[index], ...updates }
      }
    }

    updateItem(this.dataSource)
    updateItem(this.filteredData)
    this.cache.clear()
  }

  /**
   * 删除项目
   * @param {string|number} id - 项目ID
   */
  removeItem(id) {
    this.dataSource = this.dataSource.filter((item) => item.id !== id)
    this.filteredData = this.filteredData.filter((item) => item.id !== id)
    this.totalItems--
    this.cache.clear()
  }

  /**
   * 获取项目索引
   * @param {string|number} id - 项目ID
   * @returns {number} 索引
   */
  getItemIndex(id) {
    return this.filteredData.findIndex((item) => item.id === id)
  }

  /**
   * 清空缓存
   */
  clearCache() {
    this.cache.clear()
  }

  /**
   * 重置
   */
  reset() {
    this.currentPage = 1
    this.searchKeyword = ''
    this.filteredData = [...this.dataSource]
    this.cache.clear()
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, delay) {
  let timeoutId
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(this, args), delay)
  }
}

/**
 * 节流函数
 * @param {Function} func - 要执行的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, delay) {
  let lastCall = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      return func.apply(this, args)
    }
  }
}

/**
 * 计算虚拟滚动参数
 * @param {Object} params - 参数对象
 * @param {number} params.scrollTop - 滚动位置
 * @param {number} params.containerHeight - 容器高度
 * @param {number} params.itemHeight - 项目高度
 * @param {number} params.totalItems - 总项目数
 * @param {number} params.bufferSize - 缓冲区大小
 * @returns {Object} 虚拟滚动参数
 */
export function calculateVirtualScroll({
  scrollTop,
  containerHeight,
  itemHeight,
  totalItems,
  bufferSize = 5
}) {
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferSize)
  const endIndex = Math.min(
    totalItems,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + bufferSize
  )
  const offsetY = startIndex * itemHeight
  const visibleCount = Math.ceil(containerHeight / itemHeight) + bufferSize * 2

  return {
    startIndex,
    endIndex,
    offsetY,
    visibleCount
  }
}

/**
 * 性能监控工具
 */
export class PerformanceMonitor {
  constructor() {
    this.metrics = new Map()
    this.startTime = performance.now()
  }

  /**
   * 开始计时
   * @param {string} name - 计时器名称
   */
  start(name) {
    this.metrics.set(name, { start: performance.now() })
  }

  /**
   * 结束计时
   * @param {string} name - 计时器名称
   * @returns {number} 耗时（毫秒）
   */
  end(name) {
    const metric = this.metrics.get(name)
    if (metric && metric.start) {
      const duration = performance.now() - metric.start
      metric.duration = duration
      metric.end = performance.now()
      return duration
    }
    return 0
  }

  /**
   * 获取所有指标
   * @returns {Object} 性能指标
   */
  getMetrics() {
    const result = {}
    for (const [name, metric] of this.metrics) {
      result[name] = metric.duration || 0
    }
    return result
  }

  /**
   * 清除所有指标
   */
  clear() {
    this.metrics.clear()
  }

  /**
   * 获取总运行时间
   * @returns {number} 总运行时间（毫秒）
   */
  getTotalTime() {
    return performance.now() - this.startTime
  }
}

export default VirtualScrollHelper
