import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import axios from 'axios';

// 配置 Axios 的基础 URL
axios.defaults.baseURL = 'http://localhost:5000/api';

const app = createApp(App);
app.use(router);
app.mount('#app');