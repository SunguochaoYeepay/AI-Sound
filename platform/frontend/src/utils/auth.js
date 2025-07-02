/**
 * 权限管理工具模块
 */

import { useAuthStore } from '@/stores/auth'

// 权限常量定义
export const PERMISSIONS = {
  // TTS服务权限
  TTS_BASIC: 'tts.basic',
  TTS_ADVANCED: 'tts.advanced',
  TTS_BATCH: 'tts.batch',
  TTS_VOICE_CLONE: 'tts.voice_clone',
  TTS_USE: 'tts.basic',  // BasicTTS.vue使用的权限
  TTS_EXPORT: 'tts.advanced',  // BasicTTS.vue使用的导出权限
  
  // 角色管理权限
  PRESET_VIEW: 'preset.view',
  PRESET_CREATE: 'preset.create',
  PRESET_EDIT: 'preset.edit',
  PRESET_DELETE: 'preset.delete',
  
  // 书籍管理权限
  BOOK_VIEW: 'book.view',
  BOOK_CREATE: 'book.create',
  BOOK_EDIT: 'book.edit',
  BOOK_DELETE: 'book.delete',
  
  // 项目管理权限
  PROJECT_VIEW: 'project.view',
  PROJECT_CREATE: 'project.create',
  PROJECT_EDIT: 'project.edit',
  PROJECT_DELETE: 'project.delete',
  
  // 用户管理权限
  USER_VIEW: 'user.view',
  USER_CREATE: 'user.create',
  USER_EDIT: 'user.edit',
  USER_DELETE: 'user.delete',
  
  // 系统管理权限
  SYSTEM_SETTINGS: 'system.settings',
  SYSTEM_LOGS: 'system.logs',
  SYSTEM_BACKUP: 'system.backup',
  
  // 音频编辑器权限
  EDITOR_USE: 'editor.use'
}

// 角色常量定义
export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest'
}

/**
 * 检查用户是否拥有指定权限
 */
export function hasPermission(permission) {
  const authStore = useAuthStore()
  
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }
  
  // 超级管理员拥有所有权限
  if (authStore.user.is_superuser) {
    return true
  }
  
  return authStore.user.permissions?.includes(permission) || false
}

/**
 * 检查用户是否拥有指定角色
 */
export function hasRole(role) {
  const authStore = useAuthStore()
  
  if (!authStore.isAuthenticated || !authStore.user) {
    return false
  }
  
  return authStore.user.roles?.some(userRole => userRole.name === role) || false
}

/**
 * 检查是否为管理员
 */
export function isAdmin() {
  return hasRole(ROLES.ADMIN)
}

/**
 * 权限检查
 */
export function canAccess(requiredPermissions) {
  if (!requiredPermissions) {
    return true
  }
  
  if (Array.isArray(requiredPermissions)) {
    return requiredPermissions.some(permission => hasPermission(permission))
  }
  
  return hasPermission(requiredPermissions)
}

/**
 * 权限指令
 * 用法：v-permission="'user.create'" 或 v-permission="['user.create', 'user.edit']"
 */
export const vPermission = {
  mounted(el, binding) {
    const permissions = binding.value
    if (!canAccess(permissions)) {
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * 角色指令
 * 用法：v-role="'admin'" 或 v-role="['admin', 'manager']"
 */
export const vRole = {
  mounted(el, binding) {
    const roles = binding.value
    const hasRequiredRole = Array.isArray(roles)
      ? roles.some(role => hasRole(role))
      : hasRole(roles)
    
    if (!hasRequiredRole) {
      el.parentNode?.removeChild(el)
    }
  }
}