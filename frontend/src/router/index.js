import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import Balances from '../views/Balances.vue';
import AddBalance from '../views/AddBalance.vue';
import AddCategory from '../views/AddCategory.vue';
import WebApp from '../views/WebApp.vue';

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/balances', name: 'Balances', component: Balances }, // табличка с балансами и датами
  { path: '/add-balance', name: 'AddBalance', component: AddBalance },
  { path: '/add-category', name: 'AddCategory', component: AddCategory },
  { path: "/webapp", name: "WebApp", component: WebApp },


];

const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_BASE_URL || '/'),
  routes,
});

export default router;  // Экспортируем router по умолчанию

