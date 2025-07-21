/**
 * 用户认证状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const userRoles = computed(() => user.value?.roles || [])
  const userPermissions = computed(() => user.value?.permissions || [])

  // 权限检查
  const hasPermission = (permission) => {
    // 如果没有用户信息，返回false
    if (!user.value) {
      return false
    }
    // 超级管理员拥有所有权限
    if (user.value.is_superuser) {
      return true
    }
    return userPermissions.value.includes(permission)
  }

  const hasRole = (role) => {
    if (!user.value) return false
    return userRoles.value.includes(role)
  }

  const hasAnyRole = (roles) => {
    if (!user.value) return false
    return roles.some((role) => userRoles.value.includes(role))
  }

  const hasAllPermissions = (permissions) => {
    if (!user.value) return false
    return permissions.every((permission) => userPermissions.value.includes(permission))
  }

  // 用户配额检查
  const canUseTTS = computed(() => {
    if (!user.value) return false
    return user.value.used_quota < user.value.daily_quota
  })

  const quotaUsagePercentage = computed(() => {
    if (!user.value || user.value.daily_quota === 0) return 0
    return Math.round((user.value.used_quota / user.value.daily_quota) * 100)
  })

  // 设置请求拦截器
  const setupInterceptors = () => {
    // 请求拦截器 - 添加token
    axios.interceptors.request.use(
      (config) => {
        if (token.value) {
          config.headers.Authorization = `Bearer ${token.value}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // 响应拦截器 - 处理token过期
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401 && token.value) {
          // Token过期，尝试刷新
          const refreshed = await refreshTokens()
          if (refreshed) {
            // 重新发送原请求
            const originalRequest = error.config
            originalRequest.headers.Authorization = `Bearer ${token.value}`
            return axios.request(originalRequest)
          } else {
            // 刷新失败，跳转登录
            await logout()
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Actions
  const login = async (credentials) => {
    loading.value = true
    try {
      // 将JSON数据转换为表单数据格式
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await axios.post('/api/v1/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      if (response.data) {
        // 保存token
        token.value = response.data.access_token
        refreshToken.value = response.data.refresh_token
        localStorage.setItem('token', token.value)
        localStorage.setItem('refreshToken', refreshToken.value)

        // 获取用户信息 (需要单独调用)
        await fetchUserInfo()

        message.success('登录成功')
        return { success: true }
      }
    } catch (error) {
      console.error('Login error:', error)
      const errorMsg = error.response?.data?.detail || '登录失败'
      message.error(errorMsg)
      return { success: false, message: errorMsg }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    // 防止重复退出
    if (!token.value) {
      console.log('Already logged out, skipping')
      return
    }

    try {
      // 调用后端注销接口 (暂时没有实现)
      // if (token.value) {
      //   await axios.post('/api/v1/logout')
      // }
    } catch (error) {
      console.warn('Logout API call failed:', error)
    } finally {
      // 清除本地数据
      user.value = null
      token.value = ''
      refreshToken.value = ''
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')

      message.info('已退出登录')
    }
  }

  const register = async (userData) => {
    loading.value = true
    try {
      // 注册功能暂未实现
      throw new Error('注册功能暂未实现')
      // const response = await axios.post('/api/v1/register', userData)

      if (response.data) {
        message.success('注册成功，请登录')
        return { success: true }
      }
    } catch (error) {
      console.error('Register error:', error)
      const errorMsg = error.response?.data?.detail || '注册失败'
      message.error(errorMsg)
      return { success: false, message: errorMsg }
    } finally {
      loading.value = false
    }
  }

  const fetchUserInfo = async () => {
    if (!token.value) {
      console.warn('No token available, cannot fetch user info')
      return false
    }

    try {
      const response = await axios.get('/api/v1/me')
      if (response.data) {
        user.value = response.data
        console.log('User info fetched successfully:', response.data)
        return true
      }
    } catch (error) {
      console.error('Fetch user info error:', error)
      if (error.response?.status === 401) {
        console.warn('Token invalid, logging out')
        await logout()
      }
      return false
    }
    return false
  }

  const updateUserInfo = async (updateData) => {
    try {
      // 更新用户信息功能暂未实现
      throw new Error('更新用户信息功能暂未实现')
      // const response = await axios.put('/api/v1/me', updateData)
      if (response.data) {
        user.value = response.data
        message.success('个人信息更新成功')
        return { success: true }
      }
    } catch (error) {
      console.error('Update user info error:', error)
      const errorMsg = error.response?.data?.detail || '更新失败'
      message.error(errorMsg)
      return { success: false, message: errorMsg }
    }
  }

  const changePassword = async (passwordData) => {
    try {
      // 修改密码功能暂未实现
      throw new Error('修改密码功能暂未实现')
      // const response = await axios.post('/api/v1/change-password', passwordData)
      if (response.data) {
        message.success('密码修改成功，请重新登录')
        await logout()
        return { success: true }
      }
    } catch (error) {
      console.error('Change password error:', error)
      const errorMsg = error.response?.data?.detail || '密码修改失败'
      message.error(errorMsg)
      return { success: false, message: errorMsg }
    }
  }

  const refreshTokens = async () => {
    if (!refreshToken.value) {
      await logout()
      return false
    }

    try {
      // 刷新token功能暂未实现
      throw new Error('刷新token功能暂未实现')
      // const response = await axios.post('/api/v1/refresh', {
      //   refresh_token: refreshToken.value
      // })

      if (response.data) {
        token.value = response.data.access_token
        localStorage.setItem('token', token.value)

        if (response.data.refresh_token) {
          refreshToken.value = response.data.refresh_token
          localStorage.setItem('refreshToken', refreshToken.value)
        }

        user.value = response.data.user
        return true
      }
    } catch (error) {
      console.error('Refresh token error:', error)
      await logout()
      return false
    }
  }

  // 初始化
  const initialize = async () => {
    console.log('Initializing auth store...')
    setupInterceptors()

    if (token.value) {
      console.log('Token found, fetching user info...')
      const success = await fetchUserInfo()
      if (!success) {
        console.warn('Failed to fetch user info, clearing token')
        // 如果获取用户信息失败，清除无效token
        token.value = ''
        refreshToken.value = ''
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
      }
    } else {
      console.log('No token found, user not authenticated')
    }
    console.log('Auth store initialized')
  }

  return {
    // State
    user,
    token,
    loading,

    // Getters
    isAuthenticated,
    userRoles,
    userPermissions,
    canUseTTS,
    quotaUsagePercentage,

    // Permission checks
    hasPermission,
    hasRole,
    hasAnyRole,
    hasAllPermissions,

    // Actions
    login,
    logout,
    register,
    fetchUserInfo,
    updateUserInfo,
    changePassword,
    refreshTokens,
    initialize
  }
})
