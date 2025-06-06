// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import type { RouteLocationNormalized } from 'vue-router'; // 类型-only 导入
import Home from '../views/Home.vue';
import Upload from '../views/Upload.vue';
import Results from '../views/Results.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    props: (route: RouteLocationNormalized) => ({
      id: route.params.id,
      query: route.query.search
    })
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    props: (route: RouteLocationNormalized) => ({
      id: route.params.id,
      query: route.query.search
    })
  },
  {
    path: '/results',
    name: 'Results',
    component: Results,
    props: (route: RouteLocationNormalized) => ({
      id: route.params.id,
      query: route.query.search
    })
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

export default router;