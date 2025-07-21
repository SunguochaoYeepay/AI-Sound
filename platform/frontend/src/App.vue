<template>
  <!-- 登录页面不显示布局 -->
  <router-view v-if="isAuthRoute"></router-view>

  <!-- 其他页面显示完整布局 -->
  <a-layout v-else style="min-height: 100vh">
    <!-- 左侧导航栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      width="180"
      :style="{
        background:
          appStore.actualThemeMode === 'dark'
            ? 'linear-gradient(135deg, #1f1f1f 0%, #2d2d2d 100%)'
            : appStore.sidebarBackground,
        boxShadow: '2px 0 8px rgba(0,0,0,0.1)'
      }"
    >
      <!-- Logo区域 -->
      <div class="logo-container">
        <div class="logo-content">
          <div class="logo-icon" v-if="!appStore.siteSettings.logo">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
              <path d="M16 2L26 8V16L16 30L6 16V8L16 2Z" fill="#ffffff" opacity="0.9" />
              <path
                d="M16 8L22 12V20L16 26L10 20V12L16 8Z"
                :fill="
                  appStore.actualThemeMode === 'dark'
                    ? '#4a9eff'
                    : appStore.currentColorScheme.secondary
                "
              />
            </svg>
          </div>
          <div class="logo-image" v-else>
            <img
              :src="appStore.siteSettings.logo"
              :alt="appStore.siteSettings.siteName"
              style="width: 24px; height: 24px; object-fit: contain"
            />
          </div>
          <div v-if="!collapsed" class="logo-text">
            <h3 style="color: white; margin: 0; font-weight: 600">
              {{ appStore.siteSettings.siteName }}
            </h3>
            <span style="color: rgba(255, 255, 255, 0.8); font-size: 12px">{{
              appStore.siteSettings.siteSubtitle
            }}</span>
          </div>
        </div>
      </div>

      <!-- 导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        mode="inline"
        theme="dark"
        :style="{
          background: 'transparent',
          border: 'none',
          marginTop: '20px'
        }"
      >
        <!-- 内容管理 -->
        <a-menu-divider class="menu-group-divider" />
        <div v-if="!collapsed" class="menu-group-title">📚 内容管理</div>

        <a-menu-item key="home" @click="navigateTo('home')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
            </svg>
          </template>
          <span style="font-weight: 500">首页</span>
        </a-menu-item>

        <a-menu-item key="books" @click="navigateTo('books')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">书籍管理</span>
        </a-menu-item>

        <!-- 声音资源 -->
        <a-menu-divider class="menu-group-divider" />
        <div v-if="!collapsed" class="menu-group-title">🎵 声音资源</div>

        <a-menu-item key="voice-clone" @click="navigateTo('voice-clone')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
              />
              <path
                d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">声音克隆</span>
        </a-menu-item>

        <a-menu-item key="voice-library" @click="navigateTo('voice-library')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">角色配音</span>
        </a-menu-item>

        <a-menu-item key="environment-sounds" @click="navigateTo('environment-sounds')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"
              />
              <path d="M11 7h2v2h-2zm0 4h2v6h-2z" />
            </svg>
          </template>
          <span style="font-weight: 500">环境音效</span>
        </a-menu-item>

        <a-menu-item key="audio-library" @click="navigateTo('audio-library')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21s4.5-2.01 4.5-4.5V7h4V3h-7z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">音频库</span>
        </a-menu-item>

        <a-menu-item key="music-library" @click="navigateTo('music-library')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
              />
              <path d="M12 9c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5S12.83 9 12 9z" />
            </svg>
          </template>
          <span style="font-weight: 500">背景音乐</span>
        </a-menu-item>

        <!-- 创作中心 -->
        <a-menu-divider class="menu-group-divider" />
        <div v-if="!collapsed" class="menu-group-title">🎬 创作中心</div>

        <a-menu-item key="novel-projects" @click="navigateTo('novel-projects')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">语音合成</span>
        </a-menu-item>

        <a-menu-item key="environment-mixing" @click="navigateTo('environment-mixing')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21s4.5-2.01 4.5-4.5V7h4V3h-6zM10.5 19C9.12 19 8 17.88 8 16.5S9.12 14 10.5 14s2.5 1.12 2.5 2.5S11.88 19 10.5 19z"
              />
              <path d="M3 9h2v6H3zM19 9h2v6h-2z" />
            </svg>
          </template>
          <span style="font-weight: 500">环境混音</span>
        </a-menu-item>

        <a-menu-item key="sound-editor" @click="navigateTo('sound-editor')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6zM10 19c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"
              />
              <path d="M2 7h4v2H2V7zm0 3h4v2H2v-2zm0 3h4v2H2v-2z" />
            </svg>
          </template>
          <span style="font-weight: 500">编辑器</span>
        </a-menu-item>

        <!-- 用户权限 -->
        <a-menu-divider class="menu-group-divider" />
        <div v-if="!collapsed" class="menu-group-title">👥 用户权限</div>

        <a-menu-item key="users" @click="navigateTo('users')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M16 7c0-2.21-1.79-4-4-4S8 4.79 8 7s1.79 4 4 4 4-1.79 4-4zm-4 6c-2.67 0-8 1.34-8 4v3h16v-3c0-2.66-5.33-4-8-4z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">用户管理</span>
        </a-menu-item>

        <a-menu-item key="roles" @click="navigateTo('roles')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10V11.5C14.8,12.6 14.4,13.5 13.29,13.5H10.71C9.6,13.5 9.2,12.6 9.2,11.5V10C9.2,8.6 10.6,7 12,7Z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">角色权限</span>
        </a-menu-item>

        <!-- 系统运维 -->
        <a-menu-divider class="menu-group-divider" />
        <div v-if="!collapsed" class="menu-group-title">⚙️ 系统运维</div>

        <a-menu-item key="logs" @click="navigateTo('logs')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M9 3h6l1.83 2H21v2H3V5h4.17L9 3zm0 2l-.5 2h7l-.5-2H9zm-.5 4h7l-.5 2h-6l-.5-2zm-1 4h8l-.5 2H8.5l-.5-2zm-1 4h10v2H6v-2z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">日志监控</span>
        </a-menu-item>

        <a-menu-item key="backup" @click="navigateTo('backup')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">数据备份</span>
        </a-menu-item>

        <a-menu-item key="settings" @click="navigateTo('settings')">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.82,11.69,4.82,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"
              />
            </svg>
          </template>
          <span style="font-weight: 500">系统配置</span>
        </a-menu-item>
      </a-menu>

      <!-- 收起/展开按钮 -->
      <div class="collapse-button" @click="collapsed = !collapsed">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="white"
          :style="{
            transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s'
          }"
        >
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
        </svg>
      </div>
    </a-layout-sider>

    <!-- 主内容区域 -->
    <a-layout>
      <!-- 顶部状态栏 -->
      <a-layout-header class="app-header">
        <div class="header-left">
          <h2 class="page-title-header">
            {{ getPageTitle() }}
          </h2>
          <a-tag :color="getSystemStatusColor()" style="margin-left: 16px">
            <template #icon>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="6" />
              </svg>
            </template>
            {{ getSystemStatusText() }}
          </a-tag>
        </div>

        <div class="header-right">
          <!-- 系统状态显示 -->
          <a-tooltip title="查看系统状态">
            <a-button
              type="text"
              shape="circle"
              @click="router.push('/settings')"
              :class="{ 'settings-btn-active': route.path === '/settings' }"
              class="header-icon-btn"
            >
              <template #icon>
                <svg width="18" height="18" viewBox="0 0 24 24" :fill="appStore.primaryColor">
                  <path
                    d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59 7.59L19 8l-9 9z"
                  />
                </svg>
              </template>
            </a-button>
          </a-tooltip>

          <a-badge :count="notificationCount" size="small">
            <a-button type="text" shape="circle" @click="showNotifications = !showNotifications">
              <template #icon>
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  :fill="appStore.actualThemeMode === 'dark' ? '#fff' : '#666'"
                >
                  <path
                    d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"
                  />
                </svg>
              </template>
            </a-button>
          </a-badge>

          <a-dropdown>
            <a-button type="text" class="user-dropdown-btn">
              <a-avatar size="small" class="user-avatar">
                <span class="user-avatar-text">{{ userInitial }}</span>
              </a-avatar>
              <span class="user-name">{{ userName }}</span>
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">个人资料</a-menu-item>
                <a-menu-item key="logout">退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 页面内容 -->
      <a-layout-content
        :style="{
          margin: 0,
          background: appStore.themeSettings.mode === 'dark' ? '#141414' : '#faf9f8'
        }"
      >
        <div
          :style="{
            padding:
              appStore.themeSettings.layout === 'compact'
                ? '16px'
                : appStore.themeSettings.layout === 'spacious'
                  ? '32px'
                  : '24px',
            minHeight: 'calc(100vh - 60px)'
          }"
        >
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>

    <!-- 开发者控制台 -->
    <DevConsole v-if="isDev" />

    <!-- 全局音频播放器 -->
    <GlobalAudioPlayer />

  </a-layout>
</template>

<script setup>
  import { ref, computed, watch, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useAppStore } from './stores/app.js'
  import { useUserStore } from './stores/user.js'
  import { useWebSocketStore } from './stores/websocket.js'
  import { systemAPI } from './api/v2.js'
  import DevConsole from './components/DevConsole.vue'
  import GlobalAudioPlayer from './components/GlobalAudioPlayer.vue'
  import { StagewiseToolbar } from '@stagewise/toolbar-vue'
  // import stagewiseConfigFile from '../stagewise.config.js'

  const router = useRouter()
  const route = useRoute()

  // 判断是否为认证相关路由（登录、注册等）
  const isAuthRoute = computed(() => {
    return ['/login', '/register', '/forgot-password'].includes(route.path)
  })

  // Stores
  const appStore = useAppStore()
  const userStore = useUserStore()
  const wsStore = useWebSocketStore()

  const collapsed = ref(false)
  const selectedKeys = ref(['home'])
  const showNotifications = ref(false)

  // 检查是否为开发环境
  const isDev = computed(() => import.meta.env.DEV)

  // Stagewise工具栏配置
  const stagewiseConfig = {
    plugins: [],
    experimental: {
      enableStagewiseMCP: false,
      enableToolCalls: false
    },
    network: {
      scanPorts: [8001],
      excludePorts: [5747, 5749],
      timeout: 1000
    },
    debug: {
      verbose: false,
      disableAutoScan: true
    }
  }

  // 计算属性
  const notificationCount = computed(() => appStore.notificationCount)
  const systemStatus = computed(() => appStore.systemStatus)
  const userName = computed(() => userStore.user.name)
  const userInitial = computed(() => userName.value.charAt(0).toUpperCase())

  // 根据当前路由设置选中的菜单项
  const updateSelectedKeys = () => {
    const routeToKey = {
      '/': 'home',
      '/books': 'books',
      '/basic-tts': 'voice-clone',
      '/characters': 'voice-library',
      '/environment-sounds': 'environment-sounds',
      '/audio-library': 'audio-library',
      '/music-library': 'music-library', // 🎵 添加背景音乐路由映射
      '/novel-reader': 'novel-projects',
      '/novel-reader/create': 'novel-projects',
      '/novel-reader/edit': 'novel-projects',
      '/synthesis': 'novel-projects',
      '/sound-editor': 'sound-editor', // 🎵 新增音频编辑器路由映射
      '/environment-mixing': 'environment-mixing', // 环境混音页面
      '/users': 'users',
      '/roles': 'roles',
      '/logs': 'logs',
      '/backup': 'backup',
      '/settings': 'settings'
    }

    let key = 'home'
    // 检查路由路径匹配
    for (const [path, menuKey] of Object.entries(routeToKey)) {
      if (route.path === path || route.path.startsWith(path + '/')) {
        key = menuKey
        break
      }
    }

    selectedKeys.value = [key]
  }

  // 监听路由变化
  watch(
    route,
    () => {
      updateSelectedKeys()
    },
    { immediate: true }
  )

  // 开发环境设置
  onMounted(() => {
    if (import.meta.env.DEV) {
      document.body.classList.add('dev-mode')
    }

    // 初始化应用
    initializeApp()

    // 更新选中状态
    updateSelectedKeys()
  })

  // 导航函数 - 使用Vue Router
  const navigateTo = (view) => {
    const viewToRoute = {
      home: '/',
      books: '/books',
      'voice-clone': '/basic-tts',
      'voice-library': '/characters',
      'environment-sounds': '/environment-sounds',
      'audio-library': '/audio-library',
      'music-library': '/music-library', // 🎵 添加背景音乐路由映射
      'novel-projects': '/novel-reader',
      'environment-mixing': '/environment-mixing', // 环境混音页面
      'sound-editor': '/sound-editor', // 🎵 新增音频编辑器路由映射
      users: '/users',
      roles: '/roles',
      logs: '/logs',
      backup: '/backup',
      settings: '/settings'
    }

    const targetRoute = viewToRoute[view] || '/'

    // 只有在路由真正改变时才跳转
    if (route.path !== targetRoute) {
      router.push(targetRoute)
    }

    selectedKeys.value = [view]
  }

  // 根据当前路由获取页面标题
  const getPageTitle = () => {
    const titles = {
      '/': 'AI-Sound 智能语音平台',
      '/books': '书籍管理',
      '/basic-tts': '声音克隆',
      '/characters': '角色配音',
      '/environment-sounds': '环境音效',
      '/audio-library': '音频库',
      '/music-library': '背景音乐', // 🎵 添加背景音乐页面标题
      '/novel-reader': '语音合成',
      '/novel-reader/create': '语音合成',
      '/novel-reader/edit': '语音合成',
      '/synthesis': '创作中心',
      '/sound-editor': '多轨音频编辑器', // 🎵 新增音频编辑器页面标题
      '/environment-mixing': '环境混音', // 环境混音页面标题
      '/users': '用户管理',
      '/roles': '角色权限',
      '/logs': '日志监控',
      '/backup': '数据备份',
      '/settings': '系统配置'
    }

    // 支持动态路由匹配
    for (const [path, title] of Object.entries(titles)) {
      if (route.path === path || route.path.startsWith(path + '/')) {
        return title
      }
    }

    return 'AI-Sound 智能语音平台'
  }

  // 获取系统状态颜色
  const getSystemStatusColor = () => {
    const status = systemStatus.value
    const dbOk = status.database === 'healthy'
    const ttsOk = status.tts_service === 'healthy'

    // 处理初始状态或未知状态
    if (status.database === 'unknown' || status.tts_service === 'unknown') {
      return '#1890ff' // 蓝色表示检查中
    }

    if (dbOk && ttsOk) return '#52c41a'
    if (!dbOk || !ttsOk) return '#ff4d4f'
    return '#fa8c16'
  }

  // 获取系统状态文本
  const getSystemStatusText = () => {
    const status = systemStatus.value
    const dbOk = status.database === 'healthy'
    const ttsOk = status.tts_service === 'healthy'

    // 处理初始状态或未知状态
    if (status.database === 'unknown' || status.tts_service === 'unknown') {
      return 'AI-Sound 状态检查中...'
    }

    if (dbOk && ttsOk) return 'AI-Sound 运行正常'
    if (!dbOk) return '数据库连接异常'
    if (!ttsOk) return 'TTS服务异常'
    return 'AI-Sound 部分异常'
  }

  // 初始化应用
  const initializeApp = async () => {
    // 初始化应用状态
    appStore.initApp()

    // 立即执行一次健康检查
    await checkSystemHealth()

    // 🚀 临时禁用定期健康检查轮询
    // TODO: 后续可以通过WebSocket事件驱动的方式更新系统状态
    // setInterval(checkSystemHealth, 300000) // 每5分钟检查一次
  }

  // 系统健康检查
  const checkSystemHealth = async () => {
    try {
      const result = await systemAPI.healthCheck()
      if (result.success && result.data) {
        const services = result.data.services || {}
        appStore.updateSystemStatus({
          database: services.database?.status || 'unknown',
          tts_service: Object.values(services.tts_client || {}).every(Boolean)
            ? 'healthy'
            : 'unhealthy',
          websocket: services.websocket_manager?.status || 'unknown'
        })
      }
    } catch (error) {
      console.error('系统健康检查失败:', error)
      // 如果检查失败，设置为异常状态
      appStore.updateSystemStatus({
        database: 'unhealthy',
        tts_service: 'unhealthy',
        websocket: 'unhealthy'
      })
    }
  }
</script>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family:
      -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
      'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: #faf9f8;
  }

  .logo-container {
    padding: 17px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }

  .logo-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    transition: all 0.3s;
  }

  .logo-icon:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }

  .logo-text {
    display: flex;
    flex-direction: column;
  }

  .logo-text h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    margin: 0 !important;
    line-height: 1.2 !important;
  }

  .logo-text span {
    font-size: 11px !important;
    opacity: 0.8 !important;
    line-height: 1.1 !important;
  }

  .collapse-button {
    position: fixed;
    bottom: 20px;
    left: 74px;
    transform: translateX(-50%);
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s;
    z-index: 1000;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .collapse-button:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: translateX(-50%) scale(1.1);
  }

  /* 菜单分组样式 */
  .menu-group-divider {
    background-color: rgba(255, 255, 255, 0.1) !important;
    margin: 8px 0 !important;
  }

  .menu-group-divider:first-of-type {
    margin: 8px 0 !important;
  }

  .menu-group-divider:not(:first-of-type) {
    margin: 16px 0 8px 0 !important;
  }

  .menu-group-title {
    padding: 8px 16px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* 收起状态下的按钮位置调整 - 确保在80px宽度内 */
  .ant-layout-sider-collapsed .collapse-button {
    left: 40px !important;
    transform: translateX(-50%) !important;
    width: 24px !important;
    height: 24px !important;
  }

  .ant-layout-sider-collapsed .collapse-button:hover {
    left: 40px !important;
    transform: translateX(-50%) scale(1) !important;
    width: 24px !important;
    height: 24px !important;
  }

  /* 菜单项样式优化 */
  .ant-menu-dark .ant-menu-item {
    border-radius: 6px !important;
    margin: 3px 12px !important;
    width: auto !important;
    background: transparent !important;
    color: rgba(255, 255, 255, 0.85) !important;
    transition: all 0.3s !important;
  }

  .ant-menu-dark .ant-menu-item:hover {
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.15),
      rgba(255, 255, 255, 0.1)
    ) !important;
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .ant-menu-dark .ant-menu-item-selected {
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.2),
      rgba(255, 255, 255, 0.15)
    ) !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }

  .ant-menu-dark .ant-menu-item .ant-menu-item-icon {
    margin-right: 8px !important;
  }

  /* 收起状态下菜单项图标居中 */
  .ant-layout-sider-collapsed .ant-menu-dark .ant-menu-item {
    text-align: center !important;
    padding: 0 !important;
    margin: 3px 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .ant-layout-sider-collapsed .ant-menu-dark .ant-menu-item .ant-menu-item-icon {
    margin-right: 0 !important;
    margin-left: 0 !important;
    font-size: 16px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .ant-layout-sider-collapsed .ant-menu-dark .ant-menu-item:hover {
    transform: none !important;
  }

  /* 隐藏收起状态下的菜单文本 */
  .ant-layout-sider-collapsed .ant-menu-dark .ant-menu-item span[role='img'] + span {
    display: none !important;
  }

  .ant-layout-sider-collapsed .ant-menu-dark .ant-menu-item .ant-menu-title-content {
    display: none !important;
  }

  /* 强制收起状态下图标居中 */
  .ant-layout-sider-collapsed .ant-menu-item {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  .ant-layout-sider-collapsed .ant-menu-item-icon {
    width: 100% !important;
    text-align: center !important;
  }

  .ant-layout-sider-collapsed .ant-menu-item .anticon {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  /* 收起按钮暗黑模式适配 */
  [data-theme='dark'] .collapse-button {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
  }

  [data-theme='dark'] .collapse-button:hover {
    background: rgba(255, 255, 255, 0.2) !important;
  }

  /* 暗黑模式下菜单分组样式 */
  [data-theme='dark'] .menu-group-divider {
    background-color: rgba(255, 255, 255, 0.15) !important;
  }

  [data-theme='dark'] .menu-group-title {
    color: rgba(255, 255, 255, 0.6) !important;
  }

  /* 顶部状态栏优化 */
  .a-layout-header {
    background: linear-gradient(135deg, #ffffff 0%, #fdf9f4 100%) !important;
    border-bottom: 1px solid rgba(255, 123, 84, 0.1);
  }

  /* 标签和按钮优化 */
  .ant-tag {
    border-radius: 6px;
    border: none;
    font-weight: 500;
  }

  .ant-btn {
    border-radius: 6px;
    transition: all 0.3s;
  }

  .ant-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 123, 84, 0.2);
  }

  /* 滚动条样式 */
  ::-webkit-scrollbar {
    width: 6px;
  }

  ::-webkit-scrollbar-track {
    background: #f5f3f0;
  }

  ::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    border-radius: 3px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
  }

  /* 全局暗黑模式适配 */
  [data-theme='dark'] {
    color: #d1d5db !important;
  }

  [data-theme='dark'] body {
    background: #141414 !important;
    color: #d1d5db !important;
  }

  /* 暗黑模式下的文字颜色 */
  [data-theme='dark'] h1,
  [data-theme='dark'] h2,
  [data-theme='dark'] h3,
  [data-theme='dark'] h4,
  [data-theme='dark'] h5,
  [data-theme='dark'] h6 {
    color: #fff !important;
  }

  [data-theme='dark'] p,
  [data-theme='dark'] span,
  [data-theme='dark'] div {
    color: #d1d5db !important;
  }

  /* Ant Design 组件全局暗黑模式适配 */
  [data-theme='dark'] .ant-card {
    background: #1f1f1f !important;
    border-color: #434343 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  }

  [data-theme='dark'] .ant-card-head {
    background: #1f1f1f !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .ant-card-head-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-card-body {
    color: #d1d5db !important;
  }

  /* 表格全局适配 */
  [data-theme='dark'] .ant-table {
    background: #1f1f1f !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-table-thead > tr > th {
    background: #2d2d2d !important;
    color: #fff !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .ant-table-tbody > tr > td {
    background: #1f1f1f !important;
    color: #fff !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .ant-table-tbody > tr:hover > td {
    background: #2d2d2d !important;
  }

  [data-theme='dark'] .ant-table-tbody > tr.ant-table-row-selected > td {
    background: #1f2937 !important;
  }

  [data-theme='dark'] .ant-table-container {
    border-color: #434343 !important;
  }

  /* 表单组件全局适配 */
  [data-theme='dark'] .ant-input {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-input::placeholder {
    color: #8c8c8c !important;
  }

  /* 搜索输入框特殊适配 */
  [data-theme='dark'] .ant-input-search .ant-input {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-search .ant-input:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-input-search .ant-input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-input-search .ant-input-search-button {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-search .ant-input-search-button:hover {
    background-color: var(--secondary-color) !important;
    border-color: var(--secondary-color) !important;
  }

  [data-theme='dark'] .ant-input-affix-wrapper {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-input-affix-wrapper:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-input-affix-wrapper:focus,
  [data-theme='dark'] .ant-input-affix-wrapper-focused {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-input-affix-wrapper .ant-input {
    background-color: transparent !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-affix-wrapper .ant-input::placeholder {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-suffix {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-prefix {
    color: #8c8c8c !important;
  }

  /* 密码输入框 */
  [data-theme='dark'] .ant-input-password {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-password:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-input-password:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-input-password .ant-input {
    background-color: transparent !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-password .ant-input::placeholder {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-password-icon {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-password-icon:hover {
    color: var(--primary-color) !important;
  }

  /* 输入组合框 */
  [data-theme='dark'] .ant-input-group {
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-input-group .ant-input {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-group-addon {
    background-color: #434343 !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  /* 自动完成输入框 */
  [data-theme='dark'] .ant-select-auto-complete .ant-select-selector {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-select-auto-complete:hover .ant-select-selector {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-select-auto-complete .ant-select-selection-search-input {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-select-auto-complete .ant-select-selection-placeholder {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-select {
    background-color: #2d2d2d !important;
  }

  [data-theme='dark'] .ant-select-selector {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-select-selection-item {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-select-arrow {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-select:hover .ant-select-selector {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-select-focused .ant-select-selector {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-select-dropdown {
    background-color: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-select-item {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-select-item-option-selected {
    background-color: rgba(var(--primary-color-rgb), 0.15) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-select-item-option-active {
    background-color: #2d2d2d !important;
  }

  [data-theme='dark'] .ant-select-selection-placeholder {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-textarea {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-textarea:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-textarea:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-textarea::placeholder {
    color: #8c8c8c !important;
  }

  /* 数字输入框 */
  [data-theme='dark'] .ant-input-number {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-number:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-input-number:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  [data-theme='dark'] .ant-input-number-input {
    background-color: transparent !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-input-number-input::placeholder {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-number-handler-wrap {
    background: #434343 !important;
  }

  [data-theme='dark'] .ant-input-number-handler {
    border-color: #434343 !important;
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-input-number-handler:hover {
    color: var(--primary-color) !important;
  }

  /* 按钮全局适配 */
  [data-theme='dark'] .ant-btn-default {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-btn-default:hover {
    background-color: #3a3a3a !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  /* 单选/复选框适配 */
  [data-theme='dark'] .ant-radio-button-wrapper {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-radio-button-wrapper:hover {
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-radio-button-wrapper-checked {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-checkbox-wrapper {
    color: #fff !important;
  }

  /* 开关组件 */
  [data-theme='dark'] .ant-switch {
    background-color: #434343 !important;
  }

  [data-theme='dark'] .ant-switch-checked {
    background-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-switch-checked:hover:not(.ant-switch-disabled) {
    background-color: var(--secondary-color) !important;
  }

  /* 滑块组件 */
  [data-theme='dark'] .ant-slider-track {
    background-color: #4a9eff !important;
  }

  [data-theme='dark'] .ant-slider-handle {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-slider-rail {
    background-color: #434343 !important;
  }

  /* 标签组件 */
  [data-theme='dark'] .ant-tag {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  /* 状态标签颜色适配 */
  [data-theme='dark'] .ant-tag-blue {
    background-color: rgba(var(--primary-color-rgb), 0.15) !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-tag-success,
  [data-theme='dark'] .ant-tag-green {
    background-color: rgba(var(--primary-color-rgb), 0.15) !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-tag-orange {
    background-color: #4d3319 !important;
    border-color: #d97706 !important;
    color: #f59e0b !important;
  }

  [data-theme='dark'] .ant-tag-red,
  [data-theme='dark'] .ant-tag-error {
    background-color: #4d1f1f !important;
    border-color: #dc2626 !important;
    color: #ef4444 !important;
  }

  [data-theme='dark'] .ant-tag-purple {
    background-color: rgba(var(--primary-color-rgb), 0.15) !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-tag-default {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  /* 空状态 */
  [data-theme='dark'] .ant-empty-description {
    color: #8c8c8c !important;
  }

  /* 表单标签 */
  [data-theme='dark'] .ant-form-item-label > label {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-form-item-label {
    color: #fff !important;
  }

  /* 弹框组件 */
  [data-theme='dark'] .ant-modal-content {
    background-color: #1f1f1f !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-modal-header {
    background-color: #1f1f1f !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .ant-modal-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-modal-footer {
    background-color: #1f1f1f !important;
    border-top-color: #434343 !important;
  }

  /* 下拉菜单 */
  [data-theme='dark'] .ant-dropdown-menu {
    background-color: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-dropdown-menu-item {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-dropdown-menu-item:hover {
    background-color: #2d2d2d !important;
  }

  /* 分页组件 */
  [data-theme='dark'] .ant-pagination {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-item {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-pagination-item a {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-item:hover {
    background-color: #3d3d3d !important;
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-item:hover a {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-item-active {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-item-active a {
    color: #fff !important;
  }

  /* 前一页/后一页按钮 */
  [data-theme='dark'] .ant-pagination-prev,
  [data-theme='dark'] .ant-pagination-next {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-pagination-prev .ant-pagination-item-link,
  [data-theme='dark'] .ant-pagination-next .ant-pagination-item-link {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-prev:hover .ant-pagination-item-link,
  [data-theme='dark'] .ant-pagination-next:hover .ant-pagination-item-link {
    background-color: #3d3d3d !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-disabled .ant-pagination-item-link {
    background-color: #1f1f1f !important;
    border-color: #2d2d2d !important;
    color: #595959 !important;
  }

  /* 分页信息文字 */
  [data-theme='dark'] .ant-pagination-total-text {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-simple-pager {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-simple-pager input {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-simple-pager input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  /* 页面大小选择器 */
  [data-theme='dark'] .ant-pagination-options {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-options-size-changer {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-options-size-changer .ant-select-selector {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-options-size-changer .ant-select-selector:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-options-size-changer .ant-select-arrow {
    color: #8c8c8c !important;
  }

  /* 快速跳转 */
  [data-theme='dark'] .ant-pagination-options-quick-jumper {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-options-quick-jumper input {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-pagination-options-quick-jumper input:hover {
    border-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-pagination-options-quick-jumper input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  /* 省略号 */
  [data-theme='dark'] .ant-pagination-item-ellipsis {
    color: #8c8c8c !important;
  }

  /* 分页器跳转页数显示 */
  [data-theme='dark'] .ant-pagination-slash {
    color: #d1d5db !important;
  }

  /* 暗黑模式下的滚动条 */
  [data-theme='dark'] ::-webkit-scrollbar-track {
    background: #2d2d2d !important;
  }

  [data-theme='dark'] ::-webkit-scrollbar-thumb {
    background: linear-gradient(
      135deg,
      var(--primary-color) 0%,
      var(--secondary-color) 100%
    ) !important;
  }

  /* 抽屉组件暗黑模式适配 */
  [data-theme='dark'] .ant-drawer-content-wrapper {
    background-color: transparent !important;
  }

  [data-theme='dark'] .ant-drawer-content {
    background-color: #1f1f1f !important;
    border-left: 1px solid #434343;
  }

  [data-theme='dark'] .ant-drawer-header {
    background-color: #1f1f1f !important;
    border-bottom-color: #434343 !important;
  }

  [data-theme='dark'] .ant-drawer-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-drawer-body {
    background-color: #1f1f1f !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer-footer {
    background-color: #1f1f1f !important;
    border-top-color: #434343 !important;
  }

  [data-theme='dark'] .ant-drawer-extra {
    background-color: transparent !important;
  }

  [data-theme='dark'] .ant-drawer-close {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-drawer-close:hover {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-drawer-mask {
    background-color: rgba(0, 0, 0, 0.45) !important;
  }

  /* 抽屉内的组件适配 */
  [data-theme='dark'] .ant-drawer .ant-form-item-label > label {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-divider {
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-drawer .ant-divider-horizontal.ant-divider-with-text {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-alert {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-alert-message {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-drawer .ant-alert-description {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-descriptions-item-label {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-drawer .ant-descriptions-item-content {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-steps-item-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-drawer .ant-steps-item-description {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-drawer .ant-tabs-nav {
    background: transparent !important;
  }

  [data-theme='dark'] .ant-drawer .ant-tabs-tab {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-drawer .ant-tabs-tab-active {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-drawer .ant-tabs-ink-bar {
    background: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-drawer .ant-upload-dragger {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-drawer .ant-upload-text {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-upload-hint {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-drawer .ant-progress-text {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-drawer .ant-slider-mark-text {
    color: #8c8c8c !important;
  }

  /* 暗黑模式下的表单组件特殊适配 */
  [data-theme='dark'] .ant-radio-button-wrapper {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-radio-button-wrapper:hover {
    background-color: #3d3d3d !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-radio-button-wrapper-checked {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-radio-button-wrapper-checked:hover {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-select-dropdown {
    background-color: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-select-item {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-select-item-option-selected {
    background-color: rgba(var(--primary-color-rgb), 0.15) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-select-item-option-active {
    background-color: rgba(var(--primary-color-rgb), 0.1) !important;
  }

  [data-theme='dark'] .ant-picker-dropdown {
    background-color: #1f1f1f !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .ant-picker-cell-in-view.ant-picker-cell-selected .ant-picker-cell-inner {
    background: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-picker-cell-in-view.ant-picker-cell-range-start .ant-picker-cell-inner,
  [data-theme='dark'] .ant-picker-cell-in-view.ant-picker-cell-range-end .ant-picker-cell-inner {
    background: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-picker-cell-in-view:hover .ant-picker-cell-inner {
    background: rgba(var(--primary-color-rgb), 0.15) !important;
  }

  [data-theme='dark'] .ant-tag-checkable-checked {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-tag:not(.ant-tag-checkable-checked):hover {
    color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  /* 全局主按钮样式 - 使用主题颜色 */
  .ant-btn-primary {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  .ant-btn-primary:hover {
    background: var(--secondary-color) !important;
    border-color: var(--secondary-color) !important;
    color: #fff !important;
  }

  .ant-btn-primary:focus,
  .ant-btn-primary:active {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  /* 幽灵按钮样式 */
  .ant-btn-primary.ant-btn-background-ghost {
    background: transparent !important;
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  .ant-btn-primary.ant-btn-background-ghost:hover {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  /* 暗黑模式下的幽灵按钮 */
  [data-theme='dark'] .ant-btn-primary.ant-btn-background-ghost {
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-btn-primary.ant-btn-background-ghost:hover {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  /* 其他颜色主题的主按钮样式 */
  .ant-btn-default {
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
  }

  .ant-btn-default:hover {
    border-color: var(--secondary-color) !important;
    color: var(--secondary-color) !important;
  }

  /* 链接按钮 */
  .ant-btn-link {
    color: var(--primary-color) !important;
  }

  .ant-btn-link:hover {
    color: var(--secondary-color) !important;
  }

  /* 文本按钮 */
  .ant-btn-text {
    color: var(--primary-color) !important;
  }

  .ant-btn-text:hover {
    color: var(--secondary-color) !important;
  }

  /* 选中状态的Radio按钮 */
  .ant-radio-button-wrapper-checked {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  .ant-radio-button-wrapper-checked:hover {
    background: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  /* 普通Radio按钮 */
  .ant-radio-checked .ant-radio-inner {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-radio:hover .ant-radio-inner {
    border-color: var(--primary-color) !important;
  }

  .ant-radio-input:focus + .ant-radio-inner {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  /* Checkbox复选框 */
  .ant-checkbox-checked .ant-checkbox-inner {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-checkbox:hover .ant-checkbox-inner {
    border-color: var(--primary-color) !important;
  }

  .ant-checkbox-input:focus + .ant-checkbox-inner {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-checkbox-indeterminate .ant-checkbox-inner {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  /* Switch开关 */
  .ant-switch-checked {
    background-color: var(--primary-color) !important;
  }

  .ant-switch-checked:hover:not(.ant-switch-disabled) {
    background-color: var(--secondary-color) !important;
  }

  .ant-switch:focus {
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-switch-checked:focus {
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-switch-loading-icon {
    color: var(--primary-color) !important;
  }

  .ant-switch-checked .ant-switch-loading-icon {
    color: #fff !important;
  }

  .ant-switch-checked .ant-switch-handle::before {
    background-color: #fff !important;
  }

  /* Switch开关小尺寸 */
  .ant-switch-small.ant-switch-checked {
    background-color: var(--primary-color) !important;
  }

  .ant-switch-small.ant-switch-checked:hover:not(.ant-switch-disabled) {
    background-color: var(--secondary-color) !important;
  }

  /* 输入框聚焦状态 */
  .ant-input:focus,
  .ant-input-affix-wrapper:focus,
  .ant-input-affix-wrapper-focused {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-input-number:focus,
  .ant-input-number-focused {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  /* 文本域聚焦状态 */
  .ant-input-textarea-focus .ant-input {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  /* 选择器 */
  .ant-select:not(.ant-select-disabled):hover .ant-select-selector {
    border-color: var(--primary-color) !important;
  }

  .ant-select-focused .ant-select-selector {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-select-item-option-selected {
    background-color: rgba(var(--primary-color-rgb), 0.1) !important;
    color: var(--primary-color) !important;
  }

  .ant-select-item-option-active {
    background-color: rgba(var(--primary-color-rgb), 0.06) !important;
  }

  /* 日期选择器 */
  .ant-picker:hover {
    border-color: var(--primary-color) !important;
  }

  .ant-picker-focused {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-picker-cell-selected .ant-picker-cell-inner {
    background: var(--primary-color) !important;
  }

  .ant-picker-cell:hover .ant-picker-cell-inner {
    background: rgba(var(--primary-color-rgb), 0.1) !important;
  }

  /* 滑块 */
  .ant-slider-track {
    background-color: var(--primary-color) !important;
  }

  .ant-slider-handle {
    border-color: var(--primary-color) !important;
  }

  .ant-slider-handle:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 5px rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .ant-slider:hover .ant-slider-track {
    background-color: var(--primary-color) !important;
  }

  .ant-slider:hover .ant-slider-handle:not(.ant-tooltip-open) {
    border-color: var(--primary-color) !important;
  }

  /* 评分组件 */
  .ant-rate-star-focused,
  .ant-rate-star:hover,
  .ant-rate-star-full {
    color: var(--primary-color) !important;
  }

  /* 上传组件 */
  .ant-upload-list-item-done .ant-upload-list-item-name:hover {
    color: var(--primary-color) !important;
  }

  .ant-upload-drag:not(.ant-upload-disabled):hover {
    border-color: var(--primary-color) !important;
  }

  /* 穿梭框 */
  .ant-transfer-list-header-selected {
    background: var(--primary-color) !important;
  }

  .ant-transfer-list-item:hover {
    background-color: rgba(var(--primary-color-rgb), 0.06) !important;
  }

  .ant-transfer-list-item-checked {
    background-color: rgba(var(--primary-color-rgb), 0.1) !important;
  }

  /* 进度条 */
  .ant-progress-bg {
    background-color: var(--primary-color) !important;
  }

  /* 标签页激活状态 */
  .ant-tabs-tab-active .ant-tabs-tab-btn {
    color: var(--primary-color) !important;
  }

  .ant-tabs-ink-bar {
    background-color: var(--primary-color) !important;
  }

  /* 步骤条 */
  .ant-steps-item-finish .ant-steps-item-icon {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-steps-item-active .ant-steps-item-icon {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-steps-item-finish .ant-steps-item-title::after {
    background-color: var(--primary-color) !important;
  }

  .ant-steps-item-process .ant-steps-item-icon {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  /* 暗黑模式下的步骤条 */
  [data-theme='dark'] .ant-steps-item-title {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-steps-item-description {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-steps-item-icon {
    background-color: #2d2d2d !important;
    border-color: #434343 !important;
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-steps-item-finish .ant-steps-item-icon,
  [data-theme='dark'] .ant-steps-item-active .ant-steps-item-icon,
  [data-theme='dark'] .ant-steps-item-process .ant-steps-item-icon {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-steps-item-finish .ant-steps-item-title,
  [data-theme='dark'] .ant-steps-item-active .ant-steps-item-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-steps-item-tail::after {
    background-color: #434343 !important;
  }

  [data-theme='dark'] .ant-steps-item-finish .ant-steps-item-tail::after {
    background-color: var(--primary-color) !important;
  }

  /* 徽章 */
  .ant-badge-count {
    background-color: var(--primary-color) !important;
  }

  .ant-badge-dot {
    background-color: var(--primary-color) !important;
  }

  /* 标签 */
  .ant-tag-checkable:not(.ant-tag-checkable-checked):hover {
    color: var(--primary-color) !important;
  }

  .ant-tag-checkable-checked {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: #fff !important;
  }

  /* 菜单项激活状态 */
  .ant-menu-item-selected {
    color: var(--primary-color) !important;
  }

  .ant-menu-item-selected::after {
    border-right-color: var(--primary-color) !important;
  }

  .ant-menu-item:hover {
    color: var(--primary-color) !important;
  }

  /* 下拉菜单选中项 */
  .ant-dropdown-menu-item:hover,
  .ant-dropdown-menu-submenu-title:hover {
    background-color: rgba(var(--primary-color-rgb), 0.06) !important;
    color: var(--primary-color) !important;
  }

  /* 表格 */
  .ant-table-thead > tr > th {
    background: rgba(var(--primary-color-rgb), 0.02) !important;
  }

  .ant-table-tbody > tr:hover > td {
    background: rgba(var(--primary-color-rgb), 0.03) !important;
  }

  .ant-table-tbody > tr.ant-table-row-selected > td {
    background: rgba(var(--primary-color-rgb), 0.05) !important;
  }

  .ant-table-tbody > tr.ant-table-row-selected:hover > td {
    background: rgba(var(--primary-color-rgb), 0.08) !important;
  }

  /* 分页器 */
  .ant-pagination-item-active {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-pagination-item:hover {
    border-color: var(--primary-color) !important;
  }

  .ant-pagination-item:hover a {
    color: var(--primary-color) !important;
  }

  .ant-pagination-next:hover .ant-pagination-item-link,
  .ant-pagination-prev:hover .ant-pagination-item-link {
    color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  /* 回到顶部 */
  .ant-back-top {
    background-color: var(--primary-color) !important;
  }

  /* 锚点 */
  .ant-anchor-link-active > .ant-anchor-link-title {
    color: var(--primary-color) !important;
  }

  .ant-anchor-ink::before {
    background-color: var(--primary-color) !important;
  }

  .ant-anchor-ink-ball {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  /* 警告提示 */
  .ant-alert-info {
    border-color: rgba(var(--primary-color-rgb), 0.3) !important;
    background-color: rgba(var(--primary-color-rgb), 0.05) !important;
  }

  .ant-alert-info .ant-alert-icon {
    color: var(--primary-color) !important;
  }

  /* 抽屉和模态框中的组件 */
  .ant-modal .ant-radio-checked .ant-radio-inner,
  .ant-drawer .ant-radio-checked .ant-radio-inner {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-modal .ant-checkbox-checked .ant-checkbox-inner,
  .ant-drawer .ant-checkbox-checked .ant-checkbox-inner {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
  }

  .ant-modal .ant-switch-checked,
  .ant-drawer .ant-switch-checked {
    background-color: var(--primary-color) !important;
  }

  /* 链接颜色 */
  a {
    color: var(--primary-color) !important;
  }

  a:hover {
    color: var(--secondary-color) !important;
  }

  /* 消息提示框暗黑模式适配 */
  [data-theme='dark'] .ant-message {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-message-notice-content {
    background: #1f1f1f !important;
    border: 1px solid #434343 !important;
    color: #d1d5db !important;
    box-shadow:
      0 6px 16px -8px rgba(0, 0, 0, 0.8),
      0 9px 28px 0 rgba(0, 0, 0, 0.6),
      0 3px 6px -4px rgba(0, 0, 0, 0.4) !important;
  }

  [data-theme='dark'] .ant-message-success .anticon {
    color: #52c41a !important;
  }

  [data-theme='dark'] .ant-message-error .anticon {
    color: #ff4d4f !important;
  }

  [data-theme='dark'] .ant-message-warning .anticon {
    color: #faad14 !important;
  }

  [data-theme='dark'] .ant-message-info .anticon {
    color: var(--primary-color) !important;
  }

  [data-theme='dark'] .ant-message-loading .anticon {
    color: var(--primary-color) !important;
  }

  /* 通知框暗黑模式适配 */
  [data-theme='dark'] .ant-notification {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-notification-notice {
    background: #1f1f1f !important;
    border: 1px solid #434343 !important;
    box-shadow:
      0 6px 16px -8px rgba(0, 0, 0, 0.8),
      0 9px 28px 0 rgba(0, 0, 0, 0.6),
      0 3px 6px -4px rgba(0, 0, 0, 0.4) !important;
  }

  [data-theme='dark'] .ant-notification-notice-message {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-notification-notice-description {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-notification-notice-close {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .ant-notification-notice-close:hover {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-notification-notice-icon-success {
    color: #52c41a !important;
  }

  [data-theme='dark'] .ant-notification-notice-icon-error {
    color: #ff4d4f !important;
  }

  [data-theme='dark'] .ant-notification-notice-icon-warning {
    color: #faad14 !important;
  }

  [data-theme='dark'] .ant-notification-notice-icon-info {
    color: var(--primary-color) !important;
  }

  /* 工具提示框暗黑模式适配 */
  [data-theme='dark'] .ant-tooltip {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-tooltip-inner {
    background-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .ant-tooltip-arrow-content {
    background-color: #434343 !important;
  }

  /* 气泡确认框暗黑模式适配 */
  [data-theme='dark'] .ant-popconfirm {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-popconfirm-inner {
    background-color: #1f1f1f !important;
    border: 1px solid #434343 !important;
  }

  [data-theme='dark'] .ant-popconfirm-message {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .ant-popconfirm-message-title {
    color: #fff !important;
  }

  [data-theme='dark'] .ant-popconfirm-buttons {
    border-top-color: #434343 !important;
  }

  [data-theme='dark'] .ant-popconfirm-arrow-content {
    background-color: #1f1f1f !important;
  }

  /* 顶部工具条样式 */
  .app-header {
    background: linear-gradient(135deg, #ffffff 0%, #fdf9f4 100%) !important;
    border-bottom: 1px solid rgba(255, 123, 84, 0.1) !important;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  [data-theme='dark'] .app-header {
    background: #1f1f1f !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .header-left {
    display: flex;
    align-items: center;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .page-title-header {
    margin: 0;
    color: #2c3e50;
    font-weight: 600;
    font-size: 18px;
  }

  [data-theme='dark'] .page-title-header {
    color: #fff;
  }

  .header-icon-btn {
    background: transparent;
  }

  .settings-btn-active {
    background: rgba(var(--primary-color-rgb), 0.2) !important;
  }

  .user-avatar {
    background: var(--primary-color) !important;
  }

  .user-avatar-text {
    color: white;
    font-weight: 600;
  }

  .user-name {
    color: #2c3e50;
  }

  [data-theme='dark'] .user-name {
    color: #fff;
  }

  .user-dropdown-btn {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* 音频编辑器全屏模式样式 */
  body.sound-editor-fullscreen .ant-layout-sider {
    display: none !important;
  }

  body.sound-editor-fullscreen .ant-layout-header {
    display: none !important;
  }

  body.sound-editor-fullscreen .ant-layout-content {
    margin: 0 !important;
    padding: 0 !important;
  }

  body.sound-editor-fullscreen .ant-layout-content > div {
    padding: 0 !important;
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .ant-layout-sider {
      position: fixed !important;
      left: 0;
      top: 0;
      bottom: 0;
      z-index: 1000;
    }

    .ant-layout-content {
      margin-left: 0 !important;
    }

    .logo-text h3 {
      font-size: 14px !important;
    }
  }
</style>
