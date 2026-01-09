/** 路由配置 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    redirect: '/modules/ai-tools',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginPage.vue'),
  },
  {
    path: '/admin/users',
    name: 'user-list',
    component: () => import('../views/UserListPage.vue'),
  },
  {
    path: '/modules/:moduleId',
    name: 'module',
    component: () => import('../layouts/MainLayout.vue'),
    props: true,
  },
  {
    path: '/common-tools',
    name: 'common-tools',
    component: () => import('../layouts/CommonToolsLayout.vue'),
    children: [
      {
        path: '',
        name: 'common-tools-home',
        component: () => import('../views/CommonToolsView.vue'),
      },
      {
        path: 'markdown-editor',
        name: 'markdown-editor',
        component: () => import('../views/MarkdownEditorView.vue'),
      },
      {
        path: 'html/:toolId',
        name: 'html-tool',
        component: () => import('../views/HtmlToolView.vue'),
        props: true,
      },
    ],
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

// 公开路由（不需要登录即可访问）
const publicRoutes = ['/login']

// 路由守卫
router.beforeEach(async (to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const authStore = useAuthStore()

  // 如果是登录页
  if (to.path === '/login') {
    // 如果已登录，跳转到首页
    if (authStore.isAuthenticated) {
      // 验证Token是否有效
      const isValid = await authStore.verifyToken()
      if (isValid) {
        next('/modules/ai-tools')
        return
      }
    }
    next()
    return
  }

  // 检查是否为公开路由
  if (publicRoutes.includes(to.path)) {
    next()
    return
  }

  // 需要登录的路由
  if (!authStore.isAuthenticated) {
    // 未登录，跳转到登录页，并记录原访问页面
    next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
    return
  }

  // 已登录，验证Token是否有效
  const isValid = await authStore.verifyToken()
  if (!isValid) {
    // Token无效，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
    return
  }

  next()
})

export default router

