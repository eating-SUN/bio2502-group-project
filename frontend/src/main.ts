import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import VueAxios from 'vue-axios'
// 确保导入全局样式
import '@assets/css/global.css'

// 导入Bootstrap
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'


const app = createApp(App)
// 配置 axios 基础 URL
axios.defaults.baseURL = import.meta.env.DEV 
  ? '/'  // 开发环境直接使用根路径（代理会处理）
  : 'https://your-production-domain.com/api'; // 生产环境地址

app.use(router)
app.use(VueAxios, axios)
app.provide('axios', app.config.globalProperties.axios) // 提供全局访问

app.mount('#app')