import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import routes from './router/index.js'

// 引入调试工具（开发环境）
if (import.meta.env.DEV) {
  import('./utils/debugTools.js')
  import('./utils/polling.js')
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.use(Antd)
app.mount('#app')