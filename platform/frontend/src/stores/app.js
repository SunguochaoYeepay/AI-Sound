/**
 * 应用全局状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 应用状态
  const loading = ref(false)
  const title = ref('AI-Sound 智能语音合成平台')
  const version = ref('2.0.0')
  
  // 侧边栏状态
  const sidebarCollapsed = ref(false)
  
  // 主题设置
  const theme = ref('light')
  const primaryColor = ref('#1890ff')
  
  // 通知系统
  const notifications = ref([])
  const notificationCount = computed(() => notifications.value.length)
  
  // 系统状态
  const systemStatus = ref({
    database: 'unknown',
    tts_service: 'unknown',
    websocket: 'unknown',
    last_check: null
  })
  
  // 方法
  const setLoading = (status) => {
    loading.value = status
  }
  
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  const setTheme = (newTheme) => {
    theme.value = newTheme
    // 保存到localStorage
    localStorage.setItem('app-theme', newTheme)
  }
  
  const addNotification = (notification) => {
    const id = Date.now()
    notifications.value.unshift({
      id,
      timestamp: new Date(),
      ...notification
    })
    
    // 自动移除通知（可选）
    if (notification.autoClose !== false) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration || 5000)
    }
  }
  
  const removeNotification = (id) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  const clearNotifications = () => {
    notifications.value = []
  }
  
  const updateSystemStatus = (status) => {
    systemStatus.value = {
      ...systemStatus.value,
      ...status,
      last_check: new Date()
    }
  }
  
  // 初始化
  const initApp = () => {
    // 从localStorage恢复主题
    const savedTheme = localStorage.getItem('app-theme')
    if (savedTheme) {
      theme.value = savedTheme
    }
    
    // 从localStorage恢复侧边栏状态
    const savedSidebarState = localStorage.getItem('sidebar-collapsed')
    if (savedSidebarState !== null) {
      sidebarCollapsed.value = JSON.parse(savedSidebarState)
    }
  }
  
  // 保存设置到localStorage
  const saveSettings = () => {
    localStorage.setItem('app-theme', theme.value)
    localStorage.setItem('sidebar-collapsed', JSON.stringify(sidebarCollapsed.value))
  }
  
  return {
    // 状态
    loading,
    title,
    version,
    sidebarCollapsed,
    theme,
    primaryColor,
    notifications,
    notificationCount,
    systemStatus,
    
    // 方法
    setLoading,
    toggleSidebar,
    setTheme,
    addNotification,
    removeNotification,
    clearNotifications,
    updateSystemStatus,
    initApp,
    saveSettings
  }
}) 