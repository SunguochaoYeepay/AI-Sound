/**
 * 用户状态管理
 * 用户信息、权限等
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const user = ref({
    id: null,
    name: '管理员',
    email: 'admin@ai-sound.com',
    avatar: null,
    role: 'admin'
  })
  
  const isLoggedIn = ref(true) // 临时设为已登录
  
  // 用户设置
  const settings = ref({
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    defaultVoice: 'default'
  })
  
  return {
    user,
    isLoggedIn,
    settings
  }
}) 