import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'

/**
 * 自动保存系统
 * 支持定时保存、离线保存、数据恢复和版本冲突处理
 */
export function useAutoSave(options = {}) {
  const {
    interval = 30000, // 30秒自动保存
    maxLocalVersions = 10, // 最多保存10个本地版本
    enableOfflineMode = true, // 启用离线模式
    storageKey = 'ai-sound-autosave', // 本地存储键名
    saveFn = null, // 保存函数
    loadFn = null, // 加载函数
    compareFn = null // 版本比较函数
  } = options

  // 状态管理
  const isAutoSaveEnabled = ref(true)
  const isSaving = ref(false)
  const isOnline = ref(navigator.onLine)
  const lastSaveTime = ref(null)
  const saveTimer = ref(null)
  const pendingChanges = ref(false)
  const currentVersion = ref(0)
  const localVersions = ref([])

  // 计算属性
  const timeSinceLastSave = computed(() => {
    if (!lastSaveTime.value) return null
    return Date.now() - lastSaveTime.value
  })

  const shouldSave = computed(() => {
    return (
      isAutoSaveEnabled.value &&
      pendingChanges.value &&
      !isSaving.value &&
      (timeSinceLastSave.value === null || timeSinceLastSave.value >= interval)
    )
  })

  const saveStatus = computed(() => {
    if (isSaving.value) return 'saving'
    if (!isOnline.value) return 'offline'
    if (pendingChanges.value) return 'unsaved'
    return 'saved'
  })

  // 监听网络状态
  const handleOnline = () => {
    isOnline.value = true
    message.success('网络连接已恢复，正在同步数据...')
    syncOfflineData()
  }

  const handleOffline = () => {
    isOnline.value = false
    message.warning('网络连接已断开，将使用离线模式保存')
  }

  // 初始化
  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // 页面卸载时保存
    window.addEventListener('beforeunload', handleBeforeUnload)

    // 启动自动保存定时器
    startAutoSave()

    // 检查是否有未保存的本地数据
    checkLocalData()
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
    window.removeEventListener('beforeunload', handleBeforeUnload)

    stopAutoSave()
  })

  // 页面卸载处理
  const handleBeforeUnload = (event) => {
    if (pendingChanges.value) {
      // 同步保存到本地存储
      saveToLocal()

      // 提示用户有未保存的更改
      const message = '您有未保存的更改，确定要离开吗？'
      event.returnValue = message
      return message
    }
  }

  // 启动自动保存
  const startAutoSave = () => {
    if (saveTimer.value) return

    saveTimer.value = setInterval(() => {
      if (shouldSave.value) {
        performAutoSave()
      }
    }, 5000) // 每5秒检查一次
  }

  // 停止自动保存
  const stopAutoSave = () => {
    if (saveTimer.value) {
      clearInterval(saveTimer.value)
      saveTimer.value = null
    }
  }

  // 执行自动保存
  const performAutoSave = async () => {
    if (isSaving.value) return

    try {
      isSaving.value = true

      if (isOnline.value && saveFn) {
        await saveToServer()
      } else {
        await saveToLocal()
      }

      pendingChanges.value = false
      lastSaveTime.value = Date.now()
    } catch (error) {
      console.error('自动保存失败:', error)

      // 服务器保存失败时，尝试本地保存
      if (isOnline.value && enableOfflineMode) {
        try {
          await saveToLocal()
          message.warning('服务器保存失败，已保存到本地')
        } catch (localError) {
          console.error('本地保存也失败:', localError)
          message.error('保存失败，请检查存储空间')
        }
      }
    } finally {
      isSaving.value = false
    }
  }

  // 保存到服务器
  const saveToServer = async () => {
    if (!saveFn) throw new Error('未提供保存函数')

    const result = await saveFn()

    if (result && result.version) {
      currentVersion.value = result.version
    }

    // 保存成功后清除本地临时数据
    clearLocalTempData()

    return result
  }

  // 保存到本地存储
  const saveToLocal = async () => {
    if (!enableOfflineMode) return

    const data = {
      version: currentVersion.value + 1,
      timestamp: Date.now(),
      data: await getCurrentData(),
      isOffline: !isOnline.value
    }

    // 保存到本地存储
    const key = `${storageKey}-${Date.now()}`
    localStorage.setItem(key, JSON.stringify(data))

    // 更新本地版本列表
    localVersions.value.push(key)

    // 限制本地版本数量
    if (localVersions.value.length > maxLocalVersions) {
      const oldKey = localVersions.value.shift()
      localStorage.removeItem(oldKey)
    }

    // 保存版本列表
    localStorage.setItem(`${storageKey}-versions`, JSON.stringify(localVersions.value))

    return data
  }

  // 获取当前数据
  const getCurrentData = async () => {
    // 这里应该获取当前编辑器的所有数据
    // 包括项目设置、轨道信息、音频片段等
    return {
      project: window.currentProject || {},
      tracks: window.currentTracks || [],
      settings: window.editorSettings || {},
      timestamp: Date.now()
    }
  }

  // 检查本地数据
  const checkLocalData = () => {
    if (!enableOfflineMode) return

    try {
      const versionsData = localStorage.getItem(`${storageKey}-versions`)
      if (versionsData) {
        localVersions.value = JSON.parse(versionsData)

        // 检查是否有未同步的本地数据
        if (localVersions.value.length > 0) {
          message.info('发现本地保存的数据，您可以选择恢复或同步')
        }
      }
    } catch (error) {
      console.error('检查本地数据失败:', error)
    }
  }

  // 同步离线数据
  const syncOfflineData = async () => {
    if (!isOnline.value || localVersions.value.length === 0) return

    try {
      for (const versionKey of localVersions.value) {
        const data = localStorage.getItem(versionKey)
        if (data) {
          const versionData = JSON.parse(data)

          if (versionData.isOffline && saveFn) {
            await saveFn(versionData.data)
            localStorage.removeItem(versionKey)
          }
        }
      }

      // 清空本地版本列表
      localVersions.value = []
      localStorage.removeItem(`${storageKey}-versions`)

      message.success('离线数据同步完成')
    } catch (error) {
      console.error('同步离线数据失败:', error)
      message.error('同步离线数据失败')
    }
  }

  // 恢复本地数据
  const restoreFromLocal = async (versionKey) => {
    try {
      const data = localStorage.getItem(versionKey)
      if (!data) throw new Error('本地数据不存在')

      const versionData = JSON.parse(data)

      if (loadFn) {
        await loadFn(versionData.data)
      }

      currentVersion.value = versionData.version
      lastSaveTime.value = versionData.timestamp
      pendingChanges.value = false

      message.success('数据恢复成功')
      return versionData
    } catch (error) {
      console.error('恢复本地数据失败:', error)
      message.error('恢复数据失败')
      throw error
    }
  }

  // 获取本地版本列表
  const getLocalVersions = () => {
    return localVersions.value
      .map((key) => {
        const data = localStorage.getItem(key)
        if (data) {
          const versionData = JSON.parse(data)
          return {
            key,
            version: versionData.version,
            timestamp: versionData.timestamp,
            isOffline: versionData.isOffline,
            size: new Blob([data]).size
          }
        }
        return null
      })
      .filter(Boolean)
  }

  // 清除本地临时数据
  const clearLocalTempData = () => {
    localVersions.value.forEach((key) => {
      localStorage.removeItem(key)
    })
    localVersions.value = []
    localStorage.removeItem(`${storageKey}-versions`)
  }

  // 手动保存
  const manualSave = async () => {
    if (isSaving.value) {
      message.warning('正在保存中，请稍候...')
      return false
    }

    try {
      await performAutoSave()
      message.success('保存成功')
      return true
    } catch (error) {
      message.error('保存失败')
      return false
    }
  }

  // 标记有待保存的更改
  const markAsChanged = () => {
    pendingChanges.value = true
  }

  // 启用/禁用自动保存
  const enableAutoSave = () => {
    isAutoSaveEnabled.value = true
    startAutoSave()
    message.success('自动保存已启用')
  }

  const disableAutoSave = () => {
    isAutoSaveEnabled.value = false
    stopAutoSave()
    message.info('自动保存已禁用')
  }

  // 获取保存状态信息
  const getSaveStatus = () => {
    return {
      status: saveStatus.value,
      isAutoSaveEnabled: isAutoSaveEnabled.value,
      isSaving: isSaving.value,
      isOnline: isOnline.value,
      pendingChanges: pendingChanges.value,
      lastSaveTime: lastSaveTime.value,
      timeSinceLastSave: timeSinceLastSave.value,
      localVersionsCount: localVersions.value.length
    }
  }

  return {
    // 状态
    isAutoSaveEnabled,
    isSaving,
    isOnline,
    pendingChanges,
    saveStatus,
    lastSaveTime,
    timeSinceLastSave,

    // 核心方法
    manualSave,
    markAsChanged,

    // 控制方法
    enableAutoSave,
    disableAutoSave,
    startAutoSave,
    stopAutoSave,

    // 本地数据管理
    restoreFromLocal,
    getLocalVersions,
    clearLocalTempData,
    syncOfflineData,

    // 信息获取
    getSaveStatus
  }
}
