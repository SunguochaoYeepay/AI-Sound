import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'

/**
 * 缓存管理系统
 * 支持IndexedDB存储、LRU淘汰策略、智能预加载和内存管理
 */
export function useCacheManager(options = {}) {
  const {
    dbName = 'ai-sound-cache',
    dbVersion = 1,
    maxMemorySize = 100 * 1024 * 1024, // 100MB内存缓存
    maxDiskSize = 500 * 1024 * 1024, // 500MB磁盘缓存
    enablePreload = true, // 启用预加载
    enableCompression = true, // 启用压缩
    cacheExpiry = 7 * 24 * 60 * 60 * 1000 // 7天过期
  } = options

  // 状态管理
  const isInitialized = ref(false)
  const memoryCache = ref(new Map())
  const cacheStats = ref({
    memoryUsage: 0,
    diskUsage: 0,
    hitCount: 0,
    missCount: 0,
    totalRequests: 0
  })

  // IndexedDB相关
  let db = null
  const dbStores = {
    waveforms: 'waveforms',
    audioData: 'audioData',
    presets: 'presets',
    metadata: 'metadata'
  }

  // LRU缓存实现
  class LRUCache {
    constructor(maxSize) {
      this.maxSize = maxSize
      this.currentSize = 0
      this.cache = new Map()
      this.accessOrder = new Map() // 记录访问顺序
    }

    get(key) {
      if (this.cache.has(key)) {
        // 更新访问时间
        this.accessOrder.set(key, Date.now())
        return this.cache.get(key)
      }
      return null
    }

    set(key, value, size) {
      // 如果已存在，更新值
      if (this.cache.has(key)) {
        const oldItem = this.cache.get(key)
        this.currentSize -= oldItem.size
      }

      // 检查是否需要淘汰
      while (this.currentSize + size > this.maxSize && this.cache.size > 0) {
        this.evictLRU()
      }

      // 添加新项
      const item = { value, size, createdAt: Date.now() }
      this.cache.set(key, item)
      this.accessOrder.set(key, Date.now())
      this.currentSize += size
    }

    evictLRU() {
      // 找到最久未访问的项
      let oldestKey = null
      let oldestTime = Date.now()

      for (const [key, time] of this.accessOrder) {
        if (time < oldestTime) {
          oldestTime = time
          oldestKey = key
        }
      }

      if (oldestKey) {
        const item = this.cache.get(oldestKey)
        this.currentSize -= item.size
        this.cache.delete(oldestKey)
        this.accessOrder.delete(oldestKey)
      }
    }

    delete(key) {
      if (this.cache.has(key)) {
        const item = this.cache.get(key)
        this.currentSize -= item.size
        this.cache.delete(key)
        this.accessOrder.delete(key)
      }
    }

    clear() {
      this.cache.clear()
      this.accessOrder.clear()
      this.currentSize = 0
    }

    getStats() {
      return {
        size: this.cache.size,
        currentSize: this.currentSize,
        maxSize: this.maxSize,
        utilizationRate: (this.currentSize / this.maxSize) * 100
      }
    }
  }

  // 创建LRU缓存实例
  const lruCache = new LRUCache(maxMemorySize)

  // 初始化IndexedDB
  const initDB = () => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(dbName, dbVersion)

      request.onerror = () => {
        console.error('IndexedDB打开失败:', request.error)
        reject(request.error)
      }

      request.onsuccess = () => {
        db = request.result
        resolve(db)
      }

      request.onupgradeneeded = (event) => {
        const database = event.target.result

        // 创建对象存储
        Object.values(dbStores).forEach((storeName) => {
          if (!database.objectStoreNames.contains(storeName)) {
            const store = database.createObjectStore(storeName, { keyPath: 'key' })
            store.createIndex('createdAt', 'createdAt', { unique: false })
            store.createIndex('accessedAt', 'accessedAt', { unique: false })
            store.createIndex('size', 'size', { unique: false })
          }
        })
      }
    })
  }

  // 计算数据大小
  const calculateSize = (data) => {
    if (data instanceof ArrayBuffer) {
      return data.byteLength
    }
    if (data instanceof Float32Array) {
      return data.byteLength
    }
    if (typeof data === 'string') {
      return new Blob([data]).size
    }
    if (typeof data === 'object') {
      return new Blob([JSON.stringify(data)]).size
    }
    return 0
  }

  // 压缩数据
  const compressData = async (data) => {
    if (!enableCompression) return data

    try {
      const stream = new CompressionStream('gzip')
      const writer = stream.writable.getWriter()
      const reader = stream.readable.getReader()

      let compressedData = new Uint8Array()

      // 写入数据
      if (data instanceof ArrayBuffer) {
        writer.write(new Uint8Array(data))
      } else {
        writer.write(new TextEncoder().encode(JSON.stringify(data)))
      }
      writer.close()

      // 读取压缩结果
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const newData = new Uint8Array(compressedData.length + value.length)
        newData.set(compressedData)
        newData.set(value, compressedData.length)
        compressedData = newData
      }

      return {
        compressed: true,
        data: compressedData.buffer
      }
    } catch (error) {
      console.warn('数据压缩失败，使用原始数据:', error)
      return data
    }
  }

  // 解压数据
  const decompressData = async (compressedItem) => {
    if (!compressedItem.compressed) return compressedItem.data

    try {
      const stream = new DecompressionStream('gzip')
      const writer = stream.writable.getWriter()
      const reader = stream.readable.getReader()

      let decompressedData = new Uint8Array()

      // 写入压缩数据
      writer.write(new Uint8Array(compressedItem.data))
      writer.close()

      // 读取解压结果
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const newData = new Uint8Array(decompressedData.length + value.length)
        newData.set(decompressedData)
        newData.set(value, decompressedData.length)
        decompressedData = newData
      }

      return decompressedData.buffer
    } catch (error) {
      console.error('数据解压失败:', error)
      throw error
    }
  }

  // 存储到IndexedDB
  const storeToIndexedDB = async (storeName, key, data) => {
    if (!db) throw new Error('数据库未初始化')

    const transaction = db.transaction([storeName], 'readwrite')
    const store = transaction.objectStore(storeName)

    const size = calculateSize(data)
    const compressedData = await compressData(data)

    const item = {
      key,
      data: compressedData,
      size,
      createdAt: Date.now(),
      accessedAt: Date.now(),
      expiresAt: Date.now() + cacheExpiry
    }

    return new Promise((resolve, reject) => {
      const request = store.put(item)

      request.onsuccess = () => {
        cacheStats.value.diskUsage += size
        resolve(item)
      }

      request.onerror = () => {
        reject(request.error)
      }
    })
  }

  // 从IndexedDB读取
  const getFromIndexedDB = async (storeName, key) => {
    if (!db) throw new Error('数据库未初始化')

    const transaction = db.transaction([storeName], 'readonly')
    const store = transaction.objectStore(storeName)

    return new Promise((resolve, reject) => {
      const request = store.get(key)

      request.onsuccess = async () => {
        const item = request.result

        if (!item) {
          resolve(null)
          return
        }

        // 检查是否过期
        if (item.expiresAt < Date.now()) {
          // 删除过期项
          deleteFromIndexedDB(storeName, key)
          resolve(null)
          return
        }

        // 更新访问时间
        item.accessedAt = Date.now()
        store.put(item)

        try {
          const data = await decompressData(item)
          resolve(data)
        } catch (error) {
          reject(error)
        }
      }

      request.onerror = () => {
        reject(request.error)
      }
    })
  }

  // 从IndexedDB删除
  const deleteFromIndexedDB = async (storeName, key) => {
    if (!db) return

    const transaction = db.transaction([storeName], 'readwrite')
    const store = transaction.objectStore(storeName)

    return new Promise((resolve) => {
      const request = store.delete(key)
      request.onsuccess = () => resolve()
      request.onerror = () => resolve() // 忽略删除错误
    })
  }

  // 清理过期缓存
  const cleanupExpiredCache = async () => {
    if (!db) return

    const now = Date.now()

    for (const storeName of Object.values(dbStores)) {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const index = store.index('createdAt')

      const request = index.openCursor()
      request.onsuccess = (event) => {
        const cursor = event.target.result
        if (cursor) {
          const item = cursor.value
          if (item.expiresAt < now) {
            cursor.delete()
            cacheStats.value.diskUsage -= item.size
          }
          cursor.continue()
        }
      }
    }
  }

  // 获取缓存项
  const get = async (category, key) => {
    cacheStats.value.totalRequests++

    const cacheKey = `${category}:${key}`

    // 先从内存缓存查找
    const memoryItem = lruCache.get(cacheKey)
    if (memoryItem) {
      cacheStats.value.hitCount++
      return memoryItem.value
    }

    // 从IndexedDB查找
    try {
      const diskData = await getFromIndexedDB(category, key)
      if (diskData) {
        // 加载到内存缓存
        const size = calculateSize(diskData)
        lruCache.set(cacheKey, diskData, size)

        cacheStats.value.hitCount++
        return diskData
      }
    } catch (error) {
      console.error('从磁盘缓存读取失败:', error)
    }

    cacheStats.value.missCount++
    return null
  }

  // 设置缓存项
  const set = async (category, key, data) => {
    const cacheKey = `${category}:${key}`
    const size = calculateSize(data)

    // 存储到内存缓存
    lruCache.set(cacheKey, data, size)
    cacheStats.value.memoryUsage = lruCache.currentSize

    // 异步存储到IndexedDB
    try {
      await storeToIndexedDB(category, key, data)
    } catch (error) {
      console.error('存储到磁盘缓存失败:', error)
    }
  }

  // 删除缓存项
  const remove = async (category, key) => {
    const cacheKey = `${category}:${key}`

    // 从内存缓存删除
    lruCache.delete(cacheKey)
    cacheStats.value.memoryUsage = lruCache.currentSize

    // 从IndexedDB删除
    await deleteFromIndexedDB(category, key)
  }

  // 清空所有缓存
  const clear = async () => {
    // 清空内存缓存
    lruCache.clear()
    cacheStats.value.memoryUsage = 0

    // 清空IndexedDB
    if (db) {
      for (const storeName of Object.values(dbStores)) {
        const transaction = db.transaction([storeName], 'readwrite')
        const store = transaction.objectStore(storeName)
        store.clear()
      }
      cacheStats.value.diskUsage = 0
    }
  }

  // 预加载相关数据
  const preload = async (category, keys) => {
    if (!enablePreload) return

    const preloadPromises = keys.map(async (key) => {
      const cached = await get(category, key)
      if (!cached) {
        // 这里可以实现预加载逻辑
        console.log(`预加载 ${category}:${key}`)
      }
    })

    await Promise.allSettled(preloadPromises)
  }

  // 获取缓存统计信息
  const getStats = () => {
    const memoryStats = lruCache.getStats()

    return {
      ...cacheStats.value,
      memoryStats,
      hitRate:
        cacheStats.value.totalRequests > 0
          ? (cacheStats.value.hitCount / cacheStats.value.totalRequests) * 100
          : 0,
      isInitialized: isInitialized.value
    }
  }

  // 计算属性
  const hitRate = computed(() => {
    if (cacheStats.value.totalRequests === 0) return 0
    return (cacheStats.value.hitCount / cacheStats.value.totalRequests) * 100
  })

  // 初始化
  onMounted(async () => {
    try {
      await initDB()
      isInitialized.value = true

      // 启动定期清理
      setInterval(cleanupExpiredCache, 60 * 60 * 1000) // 每小时清理一次

      console.log('缓存管理器初始化成功')
    } catch (error) {
      console.error('缓存管理器初始化失败:', error)
      message.error('缓存系统初始化失败')
    }
  })

  return {
    // 状态
    isInitialized,
    cacheStats,
    hitRate,

    // 核心方法
    get,
    set,
    remove,
    clear,

    // 预加载
    preload,

    // 统计信息
    getStats,

    // 便捷方法
    getWaveform: (key) => get(dbStores.waveforms, key),
    setWaveform: (key, data) => set(dbStores.waveforms, key, data),

    getAudioData: (key) => get(dbStores.audioData, key),
    setAudioData: (key, data) => set(dbStores.audioData, key, data),

    getPreset: (key) => get(dbStores.presets, key),
    setPreset: (key, data) => set(dbStores.presets, key, data),

    getMetadata: (key) => get(dbStores.metadata, key),
    setMetadata: (key, data) => set(dbStores.metadata, key, data)
  }
}
