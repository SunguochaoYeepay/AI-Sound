import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import routes from './router/index.js'
import pinia from './stores/index.js'

// 调试工具已移除 - WebSocket替代轮询后不再需要

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.use(pinia)
app.use(Antd)
app.mount('#app')