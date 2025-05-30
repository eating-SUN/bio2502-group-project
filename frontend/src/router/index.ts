// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import Upload from '../views/Upload.vue';
import Results from '../views/Results.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload
  },
  {
    path: '/results',
    name: 'Results',
    component: Results,
    props: (route) => ({ 
      task_id: route.query.task_id 
    })
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

export default router;