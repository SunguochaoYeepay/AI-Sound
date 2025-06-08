<template>
  <a-layout style="min-height: 100vh">
    <!-- 左侧导航栏 -->
    <a-layout-sider 
      v-model:collapsed="collapsed" 
      :trigger="null" 
      collapsible
      width="280"
      style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); box-shadow: 2px 0 8px rgba(0,0,0,0.1);"
    >
      <!-- Logo区域 -->
      <div class="logo-container">
        <div class="logo-content">
          <div class="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M16 2L26 8V16L16 30L6 16V8L16 2Z" fill="#ffffff" opacity="0.9"/>
              <path d="M16 8L22 12V20L16 26L10 20V12L16 8Z" fill="#06b6d4"/>
            </svg>
          </div>
          <div v-if="!collapsed" class="logo-text">
            <h3 style="color: white; margin: 0; font-weight: 600;">AI-Sound</h3>
            <span style="color: rgba(255,255,255,0.8); font-size: 12px;">Voice Platform</span>
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
        <a-menu-item key="voice-clone" @click="navigateTo('voice-clone')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">声音克隆测试</span>
        </a-menu-item>

        <a-menu-item key="voice-library" @click="navigateTo('voice-library')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">声音库管理</span>
        </a-menu-item>

        <a-menu-item key="books" @click="navigateTo('books')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">书籍管理</span>
        </a-menu-item>

        <a-menu-item key="novel-projects" @click="navigateTo('novel-projects')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">语音合成</span>
        </a-menu-item>

        <a-menu-item key="audio-library" @click="navigateTo('audio-library')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21s4.5-2.01 4.5-4.5V7h4V3h-7z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">音频资源库</span>
        </a-menu-item>

        <a-menu-divider style="background-color: rgba(255,255,255,0.1); margin: 16px 0;" />

        <a-menu-item key="settings" @click="navigateTo('settings')">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.82,11.69,4.82,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
            </svg>
          </template>
          <span style="font-weight: 500;">设置</span>
        </a-menu-item>
      </a-menu>

      <!-- 收起/展开按钮 -->
      <div class="collapse-button" @click="collapsed = !collapsed">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white" :style="{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }">
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
        </svg>
      </div>
    </a-layout-sider>

    <!-- 主内容区域 -->
    <a-layout>
      <!-- 顶部状态栏 -->
      <a-layout-header style="background: linear-gradient(135deg, #ffffff 0%, #fdf9f4 100%) !important; border-bottom: 1px solid rgba(255, 123, 84, 0.1); height: 60px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center;">
          <h2 style="margin: 0; color: #2c3e50; font-weight: 600;">{{ getPageTitle() }}</h2>
          <a-tag color="#52c41a" style="margin-left: 16px;">
            <template #icon>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="6"/>
              </svg>
            </template>
            MegaTTS3 运行中
          </a-tag>
        </div>
        
        <div style="display: flex; align-items: center; gap: 16px;">
          <a-badge count="3" size="small">
            <a-button type="text" shape="circle">
              <template #icon>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
                </svg>
              </template>
            </a-button>
          </a-badge>

          <a-dropdown>
            <a-button type="text" style="display: flex; align-items: center; gap: 8px;">
              <a-avatar size="small" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);">
                <span style="color: white; font-weight: 600;">U</span>
              </a-avatar>
              <span style="color: #2c3e50;">用户</span>
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
      <a-layout-content style="margin: 0; background: #faf9f8;">
        <div style="padding: 24px; min-height: calc(100vh - 60px);">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const collapsed = ref(false)
const selectedKeys = ref(['voice-clone'])

// 根据当前路由设置选中的菜单项
const updateSelectedKeys = () => {
  const routeToKey = {
    '/': 'voice-clone',
    '/basic-tts': 'voice-clone', 
    '/characters': 'voice-library',
    '/books': 'books',
    '/novel-reader': 'novel-projects',
    '/novel-reader/create': 'novel-projects',
    '/novel-reader/edit': 'novel-projects',
    '/novel-reader/detail': 'novel-projects',
    '/audio-library': 'audio-library',
    '/settings': 'settings'
  }
  
  let key = 'voice-clone'
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
watch(route, () => {
  updateSelectedKeys()
}, { immediate: true })

// 组件挂载时更新选中状态
onMounted(() => {
  updateSelectedKeys()
})

// 导航函数 - 使用Vue Router
const navigateTo = (view) => {
  const viewToRoute = {
    'voice-clone': '/basic-tts',
    'voice-library': '/characters',
    'books': '/books',
    'novel-projects': '/novel-reader',
    'audio-library': '/audio-library',
    'settings': '/settings'
  }
  
  const targetRoute = viewToRoute[view] || '/basic-tts'
  
  // 只有在路由真正改变时才跳转
  if (route.path !== targetRoute) {
    router.push(targetRoute)
  }
  
  selectedKeys.value = [view]
}

// 根据当前路由获取页面标题
const getPageTitle = () => {
  const titles = {
    '/basic-tts': '声音克隆测试平台',
    '/': '声音克隆测试平台',
    '/characters': '声音库管理',
    '/books': '书籍管理',
    '/novel-reader': '语音合成',
    '/novel-reader/create': '语音合成',
    '/novel-reader/edit': '语音合成',
    '/novel-reader/detail': '语音合成',
    '/audio-library': '音频资源库',
    '/settings': '系统设置'
  }
  
  // 支持动态路由匹配
  for (const [path, title] of Object.entries(titles)) {
    if (route.path === path || route.path.startsWith(path + '/')) {
      return title
    }
  }
  
  return '声音克隆测试平台'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: #faf9f8;
}

.logo-container {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.logo-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
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

.collapse-button {
  position: absolute;
  bottom: 20px;
  left: 50%;
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
}

.collapse-button:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-50%) scale(1.1);
}

/* 菜单项样式优化 */
.ant-menu-dark .ant-menu-item {
  border-radius: 8px !important;
  margin: 4px 16px !important;
  width: auto !important;
  background: transparent !important;
  color: rgba(255, 255, 255, 0.85) !important;
  transition: all 0.3s !important;
}

.ant-menu-dark .ant-menu-item:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.1)) !important;
  color: white !important;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.ant-menu-dark .ant-menu-item-selected {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.15)) !important;
  color: white !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.ant-menu-dark .ant-menu-item .ant-menu-item-icon {
  margin-right: 12px !important;
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