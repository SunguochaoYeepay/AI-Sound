import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import router from './router/index.js'
import pinia from './stores/index.js'
import { vPermission, vRole } from './utils/auth'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

// 注册全局指令
app.directive('permission', vPermission)
app.directive('role', vRole)

app.use(router)
app.use(pinia)
app.use(Antd)

// 初始化认证状态
const authStore = useAuthStore()
authStore.initialize().then(() => {
  app.mount('#app')
})