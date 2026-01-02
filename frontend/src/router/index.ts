/** 路由配置 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    redirect: '/modules/ai-tools',
  },
  {
    path: '/modules/:moduleId',
    name: 'module',
    component: () => import('../layouts/MainLayout.vue'),
    props: true,
  },
  // 保留原有路由（后续处理）
  {
    path: '/agents',
    name: 'agent-list',
    component: () => import('../views/AgentListView.vue'),
  },
  {
    path: '/agent/:agentId',
    name: 'agent-detail',
    component: () => import('../views/AgentDetailView.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

