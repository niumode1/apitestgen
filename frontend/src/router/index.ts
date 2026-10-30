import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/workspaces',
      name: 'workspaces',
      component: () => import('@/views/WorkspacesPage.vue'),
    },
    {
      path: '/workspaces/:id',
      name: 'workspace',
      component: () => import('@/views/WorkspacePage.vue'),
    },
    {
      path: '/postman',
      name: 'postman',
      component: () => import('@/views/PostmanPage.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsPage.vue'),
    },
    // Redirect old routes
    {
      path: '/projects',
      redirect: '/workspaces',
    },
    {
      path: '/projects/:id',
      redirect: to => `/workspaces/${to.params.id}`,
    },
    {
      path: '/llm-settings',
      redirect: '/settings',
    },
  ],
})

export default router
