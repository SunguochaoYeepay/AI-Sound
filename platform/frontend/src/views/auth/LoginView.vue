<template>
  <div class="login-container">
    <div class="login-background">
      <div class="background-animation"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">
          <SoundOutlined class="logo-icon" />
          AI-Sound
        </h1>
        <p class="login-subtitle">智能语音合成平台</p>
      </div>
      
      <a-form
        ref="loginForm"
        :model="loginData"
        :rules="loginRules"
        @finish="handleLogin"
        class="login-form"
        layout="vertical"
      >
        <a-form-item name="username" label="用户名或邮箱">
          <a-input
            v-model:value="loginData.username"
            size="large"
            placeholder="请输入用户名或邮箱"
            :prefix="h(UserOutlined)"
            autocomplete="username"
          />
        </a-form-item>
        
        <a-form-item name="password" label="密码">
          <a-input-password
            v-model:value="loginData.password"
            size="large"
            placeholder="请输入密码"
            :prefix="h(LockOutlined)"
            autocomplete="current-password"
          />
        </a-form-item>
        
        <a-form-item>
          <div class="login-options">
            <a-checkbox v-model:checked="loginData.remember_me">
              记住我
            </a-checkbox>
            <a-button type="link" @click="showForgotPassword = true">
              忘记密码？
            </a-button>
          </div>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="authStore.loading"
            class="login-button"
            block
          >
            {{ authStore.loading ? '登录中...' : '登录' }}
          </a-button>
        </a-form-item>
        
        <div class="login-footer">
          <span>还没有账号？</span>
          <a-button type="link" @click="showRegisterModal = true">
            立即注册
          </a-button>
        </div>
      </a-form>
    </div>
    
    <!-- 注册模态框 -->
    <a-modal
      v-model:open="showRegisterModal"
      title="用户注册"
      :footer="null"
      width="480px"
    >
      <a-form
        ref="registerForm"
        :model="registerData"
        :rules="registerRules"
        @finish="handleRegister"
        layout="vertical"
      >
        <a-form-item name="username" label="用户名">
          <a-input
            v-model:value="registerData.username"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </a-form-item>
        
        <a-form-item name="email" label="邮箱">
          <a-input
            v-model:value="registerData.email"
            type="email"
            placeholder="请输入邮箱地址"
            autocomplete="email"
          />
        </a-form-item>
        
        <a-form-item name="full_name" label="真实姓名">
          <a-input
            v-model:value="registerData.full_name"
            placeholder="请输入真实姓名（可选）"
          />
        </a-form-item>
        
        <a-form-item name="password" label="密码">
          <a-input-password
            v-model:value="registerData.password"
            placeholder="请输入密码"
            autocomplete="new-password"
          />
        </a-form-item>
        
        <a-form-item name="confirmPassword" label="确认密码">
          <a-input-password
            v-model:value="registerData.confirmPassword"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="registerLoading"
            block
          >
            注册
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>
    
    <!-- 忘记密码模态框 -->
    <a-modal
      v-model:open="showForgotPassword"
      title="重置密码"
      :footer="null"
    >
      <a-result
        status="info"
        title="密码重置"
        sub-title="如需重置密码，请联系系统管理员或通过其他方式验证身份。"
      >
        <template #extra>
          <a-button type="primary" @click="showForgotPassword = false">
            我知道了
          </a-button>
        </template>
      </a-result>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  LockOutlined,
  SoundOutlined
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 登录表单数据
const loginData = reactive({
  username: '',
  password: '',
  remember_me: false
})

// 登录验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ]
}

// 注册相关
const showRegisterModal = ref(false)
const registerLoading = ref(false)
const registerData = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirmPassword: ''
})

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { 
      validator: (rule, value) => {
        if (value !== registerData.password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      }, 
      trigger: 'blur' 
    }
  ]
}

// 忘记密码
const showForgotPassword = ref(false)

// 处理登录
const handleLogin = async () => {
  try {
    const result = await authStore.login(loginData)
    
    if (result.success) {
      // 跳转到首页或之前页面
      const redirect = router.currentRoute.value.query.redirect || '/'
      router.push(redirect)
    }
  } catch (error) {
    console.error('Login error:', error)
  }
}

// 处理注册
const handleRegister = async () => {
  registerLoading.value = true
  try {
    const result = await authStore.register({
      username: registerData.username,
      email: registerData.email,
      password: registerData.password,
      full_name: registerData.full_name || null
    })
    
    if (result.success) {
      showRegisterModal.value = false
      // 清空注册表单
      Object.keys(registerData).forEach(key => {
        registerData[key] = ''
      })
    }
  } catch (error) {
    console.error('Register error:', error)
  } finally {
    registerLoading.value = false
  }
}

// 组件挂载后检查是否已登录
onMounted(async () => {
  await authStore.initialize()
  
  if (authStore.isAuthenticated) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #4158d0 0%, #c850c0 46%, #ffcc70 100%);
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.background-animation {
  position: absolute;
  width: 200%;
  height: 200%;
  top: -50%;
  left: -50%;
  background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 50%);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1890ff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.logo-icon {
  font-size: 32px;
}

.login-subtitle {
  margin: 8px 0 0 0;
  color: #666;
  font-size: 14px;
}

.login-form {
  margin-top: 24px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.login-button {
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #4158d0 0%, #c850c0 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  background: linear-gradient(135deg, #3a4ec0 0%, #b840b0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-card {
    margin: 20px;
    padding: 24px;
  }
  
  .login-title {
    font-size: 24px;
  }
}

/* 深色模式适配 */
[data-theme="dark"] .login-container {
  background: linear-gradient(135deg, #1e1b4b 0%, #581c87 46%, #dc2626 100%) !important;
}

[data-theme="dark"] .login-card {
  background: rgba(31, 31, 31, 0.95) !important;
  backdrop-filter: blur(10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .login-title {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .login-subtitle {
  color: #8c8c8c !important;
}

[data-theme="dark"] .login-footer {
  color: #8c8c8c !important;
}

/* 深色模式下的表单组件适配 */
[data-theme="dark"] :deep(.ant-form-item-label > label) {
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-input) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-affix-wrapper) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-input-affix-wrapper:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input-affix-wrapper:focus,
.ant-input-affix-wrapper-focused) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input-affix-wrapper .ant-input) {
  background-color: transparent !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input-affix-wrapper .ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-prefix) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-password) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-input-password:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input-password:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input-password .ant-input) {
  background-color: transparent !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input-password .ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-password-icon) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-input-password-icon:hover) {
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-checkbox-wrapper) {
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-checkbox-checked .ant-checkbox-inner) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-checkbox:hover .ant-checkbox-inner) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-btn-link) {
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-btn-link:hover) {
  color: var(--secondary-color) !important;
}

/* 模态框深色模式适配 */
[data-theme="dark"] :deep(.ant-modal-content) {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-header) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-title) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-modal-body) {
  background: #1f1f1f !important;
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-modal-footer) {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-result-title) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-result-subtitle) {
  color: #8c8c8c !important;
}

/* 主按钮保持原有的渐变样式 */
[data-theme="dark"] .login-button {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
  border: none !important;
}

[data-theme="dark"] .login-button:hover {
  background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%) !important;
}
</style>