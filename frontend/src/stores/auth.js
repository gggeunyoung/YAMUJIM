import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const ACCESS_KEY = 'yamujim_access'
const REFRESH_KEY = 'yamujim_refresh'

/**
 * JWT 기반 인증 상태. 토큰은 localStorage에 보관하고,
 * api/client.js의 인터셉터가 이 스토어를 참조해 헤더를 붙이고 갱신한다.
 */
export const useAuthStore = defineStore('auth', () => {
  const access = ref(localStorage.getItem(ACCESS_KEY) || '')
  const refresh = ref(localStorage.getItem(REFRESH_KEY) || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!access.value)

  function setTokens({ access: a, refresh: r }) {
    if (a) {
      access.value = a
      localStorage.setItem(ACCESS_KEY, a)
    }
    if (r) {
      refresh.value = r
      localStorage.setItem(REFRESH_KEY, r)
    }
  }

  function setUser(u) {
    user.value = u
  }

  function clear() {
    access.value = ''
    refresh.value = ''
    user.value = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }

  return { access, refresh, user, isAuthenticated, setTokens, setUser, clear }
})
