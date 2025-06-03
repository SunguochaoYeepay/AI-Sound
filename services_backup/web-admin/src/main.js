import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import axios from './plugins/axios'

import App from './App.vue'
import router from './router'

// 全局样式
import './assets/css/main.css'

const app = createApp(App)

// 全局配置axios
app.config.globalProperties.$axios = axios
window.axios = axios  // 使现有代码中的axios引用指向我们的实例

app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')