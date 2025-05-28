import { createRouter, createWebHistory } from 'vue-router'

// 懒加载路由
const TtsDemoView = () => import('../views/TtsDemoView.vue')
const DashboardView = () => import('../views/DashboardView.vue')
const EngineStatusView = () => import('../views/EngineStatusView.vue')
const NovelProcessorView = () => import('../views/NovelProcessorView.vue')
const TaskMonitorView = () => import('../views/TaskMonitorView.vue')
const NovelManageView = () => import('../views/NovelManageView.vue')
const SystemSettingsView = () => import('../views/SystemSettingsView.vue')
const AudioLibraryView = () => import('../views/AudioLibraryView.vue')
const VoiceFeatureView = () => import('../views/VoiceFeatureView.vue')
const VoiceListView = () => import('../views/VoiceListView.vue')
const VoiceUploadView = () => import('../views/VoiceUploadView.vue')
const CharacterMapperView = () => import('../views/CharacterMapperView.vue')

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { title: '控制台' }
  },
  {
    path: '/engines',
    name: 'EngineStatus',
    component: EngineStatusView,
    meta: { title: '引擎状态' }
  },
  {
    path: '/tts',
    name: 'TtsDemo',
    component: TtsDemoView,
    meta: { title: '语音试听' }
  },
  {
    path: '/novel',
    name: 'NovelProcessor',
    component: NovelProcessorView,
    meta: { title: '小说处理' }
  },
  {
    path: '/tasks',
    name: 'TaskMonitor',
    component: TaskMonitorView,
    meta: { title: '任务监控' }
  },
  {
    path: '/novels',
    name: 'NovelManage',
    component: NovelManageView,
    meta: { title: '小说管理' }
  },
  {
    path: '/library',
    name: 'AudioLibrary',
    component: AudioLibraryView,
    meta: { title: '音频库' }
  },
  {
    path: '/voice-feature',
    name: 'VoiceFeature',
    component: VoiceFeatureView,
    meta: { title: '声纹特征提取' }
  },
  {
    path: '/voice-list',
    name: 'VoiceList',
    component: VoiceListView,
    meta: { title: '声音库' }
  },
  {
    path: '/voice-upload',
    name: 'VoiceUpload',
    component: VoiceUploadView,
    meta: { title: '声音上传' }
  },
  {
    path: '/character-mapper',
    name: 'CharacterMapper',
    component: CharacterMapperView,
    meta: { title: '角色声音映射' }
  },
  {
    path: '/settings',
    name: 'SystemSettings',
    component: SystemSettingsView,
    meta: { title: '系统设置' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由前置守卫，设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `AI-Sound - ${to.meta.title}`
  }
  next()
})

export default router 