import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { fetchMe } from '../api/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, hideHeader: true },
  },
  {
    path: '/auth/kakao/callback',
    name: 'kakao-callback',
    component: () => import('../views/KakaoCallbackView.vue'),
    meta: { public: true, hideHeader: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { hideHeader: true },
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/preference',
    name: 'preference',
    component: () => import('../views/PreferenceView.vue'),
  },
  {
    path: '/trip',
    name: 'trip',
    component: () => import('../views/TripView.vue'),
  },
  {
    path: '/community',
    name: 'community',
    component: () => import('../views/CommunityView.vue'),
  },
  {
    path: '/mypage',
    name: 'mypage',
    component: () => import('../views/MyPageView.vue'),
  },
  {
    path: '/trip/:tripId/result',
    name: 'result',
    component: () => import('../views/ResultView.vue'),
  },
  { path: '/', redirect: { name: 'home' } },
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

async function ensureUser(auth) {
  if (auth.user) return auth.user
  try {
    const { data } = await fetchMe()
    auth.setUser(data)
    return data
  } catch {
    auth.clear()
    return null
  }
}

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    const user = await ensureUser(auth)
    if (!user) return true
    if (!user.profile_complete) return { name: 'profile' }
    return { name: 'home' }
  }
  if (!to.meta.public && auth.isAuthenticated) {
    const user = await ensureUser(auth)
    if (!user) {
      return { name: 'login', query: { next: to.fullPath } }
    }
    if (to.name !== 'profile' && !user.profile_complete) {
      return { name: 'profile', query: { next: to.fullPath } }
    }
  }
  return true
})

export default router
