/** 路由配置 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    redirect: '/agents',
  },
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

