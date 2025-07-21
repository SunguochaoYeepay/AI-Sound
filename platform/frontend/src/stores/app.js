/**
 * 应用全局状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 应用状态
  const loading = ref(false)
  const version = ref('2.0.0')

  // 侧边栏状态
  const sidebarCollapsed = ref(false)

  // 站点设置
  const siteSettings = ref({
    siteName: 'AI-Sound 智能语音平台',
    siteSubtitle: '专业的AI语音合成解决方案',
    siteDescription:
      '基于最新AI技术的语音合成平台，支持多种语音模型、情感表达和个性化定制，为您提供专业的语音解决方案。',
    adminEmail: 'admin@ai-sound.com',
    supportContact: 'support@ai-sound.com',
    logo: '',
    favicon: ''
  })

  // 主题设置
  const themeSettings = ref({
    // 基础主题
    mode: 'system', // system, light, dark
    // 主色调方案
    colorScheme: 'blue', // blue, green, purple, red, orange
    // 布局设置
    layout: 'comfortable', // compact, comfortable, spacious
    // 侧边栏样式
    sidebarStyle: 'gradient', // gradient, solid, glass
    // 卡片样式
    cardStyle: 'rounded', // rounded, square
    // 动画效果
    enableAnimations: true,
    // 紧凑模式
    compactMode: false
  })

  // 颜色主题配置
  const colorSchemes = {
    blue: {
      primary: '#1890ff',
      secondary: '#06b6d4',
      gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
      sidebarGradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
    },
    green: {
      primary: '#52c41a',
      secondary: '#10b981',
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      sidebarGradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    },
    purple: {
      primary: '#722ed1',
      secondary: '#8b5cf6',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      sidebarGradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
    },
    red: {
      primary: '#f5222d',
      secondary: '#ef4444',
      gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      sidebarGradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
    },
    orange: {
      primary: '#fa8c16',
      secondary: '#f97316',
      gradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
      sidebarGradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)'
    }
  }

  // 获取实际主题模式（处理系统主题）
  const actualThemeMode = computed(() => {
    if (themeSettings.value.mode === 'system') {
      // 检测系统主题
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    }
    return themeSettings.value.mode
  })

  // 计算属性
  const title = computed(() => siteSettings.value.siteName)
  const currentColorScheme = computed(() => colorSchemes[themeSettings.value.colorScheme])
  const primaryColor = computed(() => currentColorScheme.value.primary)
  const sidebarBackground = computed(() => {
    if (themeSettings.value.sidebarStyle === 'gradient') {
      return currentColorScheme.value.sidebarGradient
    } else if (themeSettings.value.sidebarStyle === 'solid') {
      return currentColorScheme.value.primary
    } else {
      // glass
      return `linear-gradient(135deg, ${currentColorScheme.value.primary}88 0%, ${currentColorScheme.value.secondary}88 100%)`
    }
  })

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
    saveSettings()
  }

  const updateSiteSettings = (newSettings) => {
    Object.assign(siteSettings.value, newSettings)
    saveSettings()
    applySettings()
  }

  const updateThemeSettings = (newSettings) => {
    Object.assign(themeSettings.value, newSettings)
    saveSettings()
    applySettings()
  }

  const setTheme = (newTheme) => {
    themeSettings.value.mode = newTheme
    saveSettings()
    applySettings()
  }

  const setColorScheme = (scheme) => {
    themeSettings.value.colorScheme = scheme
    saveSettings()
    applySettings()
  }

  const addNotification = (notification) => {
    // 检查是否已存在相同的通知（防止重复）
    const isDuplicate = notifications.value.some(
      (existing) =>
        existing.message === notification.message &&
        existing.type === notification.type &&
        Date.now() - existing.timestamp.getTime() < 3000 // 3秒内的相同通知视为重复
    )

    if (isDuplicate) {
      console.log('Duplicate notification ignored:', notification.message)
      return
    }

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
    const index = notifications.value.findIndex((n) => n.id === id)
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

  // 应用设置到DOM
  const applySettings = () => {
    const root = document.documentElement

    // 转换hex颜色为RGB值
    const hexToRgb = (hex) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result
        ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
          }
        : null
    }

    const primaryRgb = hexToRgb(currentColorScheme.value.primary)
    const secondaryRgb = hexToRgb(currentColorScheme.value.secondary)

    // 应用主色调
    root.style.setProperty('--primary-color', currentColorScheme.value.primary)
    root.style.setProperty('--secondary-color', currentColorScheme.value.secondary)
    root.style.setProperty('--primary-gradient', currentColorScheme.value.gradient)

    // 应用RGB格式的颜色变量
    if (primaryRgb) {
      root.style.setProperty(
        '--primary-color-rgb',
        `${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}`
      )
    }
    if (secondaryRgb) {
      root.style.setProperty(
        '--secondary-color-rgb',
        `${secondaryRgb.r}, ${secondaryRgb.g}, ${secondaryRgb.b}`
      )
    }

    // 应用主题模式（使用实际主题模式）
    root.setAttribute('data-theme', actualThemeMode.value)
    root.setAttribute('data-layout', themeSettings.value.layout)
    root.setAttribute('data-card-style', themeSettings.value.cardStyle)

    // 应用favicon
    if (siteSettings.value.favicon) {
      let favicon = document.querySelector('link[rel="icon"]')
      if (!favicon) {
        favicon = document.createElement('link')
        favicon.rel = 'icon'
        document.head.appendChild(favicon)
      }
      favicon.href = siteSettings.value.favicon
    }

    // 应用页面标题
    if (siteSettings.value.siteName) {
      document.title = siteSettings.value.siteName
    }

    // 应用紧凑模式
    if (themeSettings.value.compactMode) {
      document.body.classList.add('compact-mode')
    } else {
      document.body.classList.remove('compact-mode')
    }

    // 应用动画设置
    if (!themeSettings.value.enableAnimations) {
      document.body.classList.add('no-animations')
    } else {
      document.body.classList.remove('no-animations')
    }
  }

  // 初始化
  const initApp = () => {
    // 从localStorage恢复设置
    const savedSiteSettings = localStorage.getItem('site-settings')
    if (savedSiteSettings) {
      try {
        Object.assign(siteSettings.value, JSON.parse(savedSiteSettings))
      } catch (e) {
        console.warn('Failed to load site settings:', e)
      }
    }

    const savedThemeSettings = localStorage.getItem('theme-settings')
    if (savedThemeSettings) {
      try {
        Object.assign(themeSettings.value, JSON.parse(savedThemeSettings))
      } catch (e) {
        console.warn('Failed to load theme settings:', e)
      }
    }

    // 从localStorage恢复侧边栏状态
    const savedSidebarState = localStorage.getItem('sidebar-collapsed')
    if (savedSidebarState !== null) {
      sidebarCollapsed.value = JSON.parse(savedSidebarState)
    }

    // 应用设置
    applySettings()

    // 监听系统主题变化
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', () => {
        if (themeSettings.value.mode === 'system') {
          applySettings()
        }
      })
    }
  }

  // 保存设置到localStorage
  const saveSettings = () => {
    localStorage.setItem('site-settings', JSON.stringify(siteSettings.value))
    localStorage.setItem('theme-settings', JSON.stringify(themeSettings.value))
    localStorage.setItem('sidebar-collapsed', JSON.stringify(sidebarCollapsed.value))
  }

  return {
    // 状态
    loading,
    title,
    version,
    sidebarCollapsed,
    siteSettings,
    themeSettings,
    colorSchemes,
    currentColorScheme,
    primaryColor,
    sidebarBackground,
    notifications,
    notificationCount,
    systemStatus,
    actualThemeMode,

    // 方法
    setLoading,
    toggleSidebar,
    updateSiteSettings,
    updateThemeSettings,
    setTheme,
    setColorScheme,
    addNotification,
    removeNotification,
    clearNotifications,
    updateSystemStatus,
    initApp,
    saveSettings,
    applySettings
  }
})
