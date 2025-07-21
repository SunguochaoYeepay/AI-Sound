import { createRouter, createWebHistory } from 'vue-router'
import { setupRouterGuards, setupRouterAfterGuards } from './guards'
import { PERMISSIONS } from '@/utils/auth'

import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import BasicTTS from '../views/BasicTTS.vue'
import Characters from '../views/Characters.vue'
import Books from '../views/Books.vue'
import BookDetail from '../views/BookDetail.vue'
import BookCreate from '../views/BookCreate.vue'
// NovelReader.vue已删除，项目详情功能整合到SynthesisCenter
import NovelProjects from '../views/NovelProjects.vue'
import NovelProjectCreate from '../views/NovelProjectCreate.vue'
import SynthesisCenter from '../views/SynthesisCenter.vue'
import SynthesisResults from '../views/SynthesisResults.vue'
import AudioLibrary from '../views/AudioLibrary.vue'
import EnvironmentSounds from '../views/EnvironmentSounds.vue'
import MusicLibrary from '../views/MusicLibrary.vue'
import WebSocketTest from '../views/WebSocketTest.vue'
import Settings from '../views/Settings.vue'
import LogMonitor from '../views/LogMonitor.vue'
import BackupManagement from '../views/BackupManagement.vue'
import UserManagement from '../views/UserManagement.vue'
import RoleManagement from '../views/RoleManagement.vue'
import LoginView from '../views/auth/LoginView.vue'

const routes = [
  // 认证路由
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: {
      title: '用户登录',
      requiresAuth: false,
      hidden: true
    }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页',
      requiresAuth: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '工作台',
      requiresAuth: true
    }
  },
  {
    path: '/basic-tts',
    name: 'BasicTTS',
    component: BasicTTS,
    meta: {
      title: '基础TTS',
      requiresAuth: true,
      permission: PERMISSIONS.TTS_USE
    }
  },
  {
    path: '/characters',
    name: 'Characters',
    component: Characters,
    meta: {
      title: '角色管理',
      requiresAuth: true,
      permission: PERMISSIONS.PRESET_VIEW
    }
  },
  // 书籍管理路由
  {
    path: '/books',
    name: 'Books',
    component: Books,
    meta: {
      title: '书籍管理',
      requiresAuth: true,
      permission: PERMISSIONS.BOOK_VIEW
    }
  },
  {
    path: '/books/create',
    name: 'BookCreate',
    component: BookCreate,
    meta: {
      title: '创建书籍',
      requiresAuth: true,
      permission: PERMISSIONS.BOOK_CREATE
    }
  },
  {
    path: '/books/edit/:id',
    name: 'BookEdit',
    component: BookCreate,
    meta: {
      title: '编辑书籍',
      requiresAuth: true,
      permission: PERMISSIONS.BOOK_EDIT
    }
  },
  {
    path: '/books/detail/:id',
    name: 'BookDetail',
    component: BookDetail,
    meta: {
      title: '书籍详情',
      requiresAuth: true,
      permission: PERMISSIONS.BOOK_VIEW
    }
  },
  // 项目管理路由（重构后）
  {
    path: '/novel-reader',
    name: 'NovelProjects',
    component: NovelProjects
  },
  {
    path: '/novel-reader/create',
    name: 'NovelProjectCreate',
    component: NovelProjectCreate
  },
  {
    path: '/novel-reader/edit/:id',
    name: 'NovelProjectEdit',
    component: NovelProjectCreate
  },
  // novel-reader/detail 路由已删除，项目详情重定向到合成中心
  // 对话音生成路由
  {
    path: '/synthesis/:projectId',
    name: 'DialogueAudioGeneration',
    component: SynthesisCenter
  },
  // 合成结果路由
  {
    path: '/synthesis-results/:projectId',
    name: 'SynthesisResults',
    component: SynthesisResults
  },
  {
    path: '/audio-library',
    name: 'AudioLibrary',
    component: AudioLibrary
  },
  {
    path: '/environment-sounds',
    name: 'EnvironmentSounds',
    component: EnvironmentSounds
  },
  {
    path: '/environment-mixing',
    name: 'EnvironmentMixing',
    component: () => import('../views/EnvironmentMixing.vue'),
    meta: {
      title: '环境混音',
      requiresAuth: true
    }
  },
  {
    path: '/music-library',
    name: 'MusicLibrary',
    component: MusicLibrary
  },

  // 音频编辑器路由（新增）
  {
    path: '/sound-editor',
    name: 'SoundEditorProjects',
    component: () => import('../views/SoundEditorProjects.vue'),
    meta: {
      title: '音频编辑器',
      requiresAuth: true,
      permission: PERMISSIONS.EDITOR_USE
    }
  },
  {
    path: '/sound-editor/edit/:projectId',
    name: 'SoundEditor',
    component: () => import('../views/SoundEditor.vue'),
    meta: {
      title: '编辑器',
      requiresAuth: true,
      permission: PERMISSIONS.EDITOR_USE
    }
  },
  {
    path: '/websocket-test',
    name: 'WebSocketTest',
    component: WebSocketTest
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: true,
      permission: PERMISSIONS.SYSTEM_SETTINGS
    }
  },
  {
    path: '/logs',
    name: 'LogMonitor',
    component: LogMonitor,
    meta: {
      title: '日志监控',
      requiresAuth: true,
      permission: PERMISSIONS.SYSTEM_LOGS
    }
  },
  {
    path: '/backup',
    name: 'BackupManagement',
    component: BackupManagement,
    meta: {
      title: '备份管理',
      requiresAuth: true,
      permission: PERMISSIONS.SYSTEM_BACKUP
    }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: UserManagement,
    meta: {
      title: '用户管理',
      requiresAuth: true,
      permission: PERMISSIONS.USER_MANAGE
    }
  },
  {
    path: '/roles',
    name: 'RoleManagement',
    component: RoleManagement,
    meta: {
      title: '角色管理',
      requiresAuth: true,
      permission: PERMISSIONS.ROLE_MANAGE
    }
  },

  // 错误页面和其他路由
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('../views/error/403.vue'),
    meta: {
      title: '权限不足',
      requiresAuth: false,
      hidden: true
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('../views/error/404.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false,
      hidden: true
    }
  },

  // 捕获所有未匹配的路由
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 设置路由守卫
setupRouterGuards(router)
setupRouterAfterGuards(router)

export default router
