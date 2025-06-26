import { useAuthStore } from '@/stores/auth'
import { hasPermission } from '@/utils/auth'

/**
 * 路由前置守卫
 */
export function setupRouterGuards(router) {
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    
    // 获取当前用户信息
    const user = authStore.user
    const token = authStore.token
    
    // 如果没有token，重定向到登录页
    if (!token) {
      if (to.path !== '/login') {
        console.log('No token, redirecting to login')
        next('/login')
        return
      }
      next()
      return
    }
    
    // 如果有token但没有用户信息，尝试获取用户信息
    if (!user) {
      console.log('Token exists but no user info, fetching...')
      const success = await authStore.fetchUserInfo()
      if (!success) {
        console.error('获取用户信息失败，跳转登录')
        await authStore.logout()
        next('/login')
        return
      }
    }
    
    // 如果已登录且访问登录页，重定向到首页
    if (to.path === '/login') {
      next('/')
      return
    }
    
    // 检查路由权限
    if (to.meta?.requiresAuth !== false) {
      const currentUser = authStore.user
      
      // 超级管理员跳过所有权限检查
      if (currentUser?.is_superuser) {
        next()
        return
      }
      
      // 检查页面访问权限
      if (to.meta?.permission) {
        if (!hasPermission(to.meta.permission)) {
          console.warn(`用户 ${currentUser?.username} 无权限访问页面: ${to.path}`)
          next('/403')
          return
        }
      }
      
      // 检查多个权限（任一满足即可）
      if (to.meta?.permissions && Array.isArray(to.meta.permissions)) {
        const hasAnyPermission = to.meta.permissions.some(permission => 
          hasPermission(permission)
        )
        
        if (!hasAnyPermission) {
          console.warn(`用户 ${currentUser?.username} 无权限访问页面: ${to.path}`)
          next('/403')
          return
        }
      }
      
      // 检查角色权限
      if (to.meta?.roles && Array.isArray(to.meta.roles)) {
        const userRoles = currentUser?.roles?.map(role => role.name) || []
        const hasRequiredRole = to.meta.roles.some(role => userRoles.includes(role))
        
        if (!hasRequiredRole) {
          console.warn(`用户 ${currentUser?.username} 角色不足，无法访问页面: ${to.path}`)
          next('/403')
          return
        }
      }
    }
    
    next()
  })
}

/**
 * 路由后置守卫
 */
export function setupRouterAfterGuards(router) {
  router.afterEach((to) => {
    // 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - AI-Sound`
    } else {
      document.title = 'AI-Sound'
    }
    
    // 记录页面访问日志
    console.log(`页面访问: ${to.path}`)
  })
}