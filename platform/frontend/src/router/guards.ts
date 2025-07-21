import { useAuthStore } from '@/stores/auth'
import { ROLES } from '@/utils/auth'
import type { Router } from 'vue-router'

/**
 * 创建路由元数据
 * @param {Object} meta 路由元数据对象
 * @param {string} meta.title 页面标题
 * @param {boolean} meta.requiresAuth 是否需要认证
 * @param {string|string[]} [meta.permissions] 所需权限
 * @param {string|string[]} [meta.roles] 所需角色
 * @param {boolean} [meta.hidden] 是否在导航中隐藏
 * @returns {Object} 处理后的路由元数据
 */
export function createRouteMeta(meta) {
  return {
    title: meta.title || '',
    requiresAuth: meta.requiresAuth !== false,
    permissions: Array.isArray(meta.permissions)
      ? meta.permissions
      : meta.permissions
        ? [meta.permissions]
        : [],
    roles: Array.isArray(meta.roles) ? meta.roles : meta.roles ? [meta.roles] : [],
    hidden: meta.hidden || false
  }
}

/**
 * 全局前置守卫
 * @param {import('vue-router').RouteLocationNormalized} to 目标路由
 * @param {import('vue-router').RouteLocationNormalized} from 来源路由
 * @param {Function} next 路由解析函数
 */
async function beforeEach(to, from, next) {
  const authStore = useAuthStore()
  const { isAuthenticated, userPermissions, userRole } = authStore

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - AI Sound`
  }

  // 处理需要认证的路由
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    // 检查权限 - 超级管理员跳过权限检查
    const requiredPermissions = to.meta.permissions || []
    if (requiredPermissions.length > 0) {
      // 如果是超级管理员，直接通过
      if (authStore.user?.is_superuser) {
        // 超级管理员拥有所有权限，直接通过
      } else {
        const hasPermission = requiredPermissions.every((permission) =>
          userPermissions.includes(permission)
        )
        if (!hasPermission) {
          next({ name: 'Forbidden' })
          return
        }
      }
    }

    // 检查角色
    const requiredRoles = to.meta.roles || []
    if (requiredRoles.length > 0) {
      const hasRole = requiredRoles.includes(userRole) || userRole === ROLES.ADMIN
      if (!hasRole) {
        next({ name: 'Forbidden' })
        return
      }
    }
  }

  next()
}

/**
 * 全局后置钩子
 * @param {import('vue-router').RouteLocationNormalized} to 目标路由
 * @param {import('vue-router').RouteLocationNormalized} from 来源路由
 */
function afterEach(to, from) {
  // 可以在这里添加路由切换后的逻辑
  // 比如关闭加载动画等
}

/**
 * 设置全局前置守卫
 * @param {Router} router Vue Router实例
 */
export function setupBeforeGuards(router: Router) {
  router.beforeEach(beforeEach)
}

/**
 * 设置全局后置守卫
 * @param {Router} router Vue Router实例
 */
export function setupAfterGuards(router: Router) {
  router.afterEach(afterEach)
}
