import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import App from './App.vue'
import router from './router/index.js'
import pinia from './stores/index.js'
import { vPermission, vRole } from './utils/auth'
import { useAuthStore } from './stores/auth'

// 配置dayjs
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// 将dayjs设为全局可用
window.dayjs = dayjs

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
