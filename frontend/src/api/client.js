import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

// 백엔드는 /api/v1/ 하위에 API를 서빙한다. vite proxy가 /api → Django(8000)로 포워딩.
const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 180000,
})

// 요청마다 access 토큰을 Authorization 헤더에 부착
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.access && !config._skipAuth) {
    config.headers.Authorization = `Bearer ${auth.access}`
  }
  return config
})

// 동시 401 발생 시 refresh 호출이 한 번만 일어나도록 공유 Promise 사용
let refreshPromise = null

async function refreshAccessToken() {
  const auth = useAuthStore()
  if (!auth.refresh) throw new Error('no refresh token')
  // 인터셉터를 타지 않는 raw axios로 refresh 호출 (무한루프 방지)
  const { data } = await axios.post(
    '/api/v1/auth/token/refresh/',
    { refresh: auth.refresh },
    { headers: { 'Content-Type': 'application/json' } },
  )
  auth.setTokens({ access: data.access })
  return data.access
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    // 401 + 아직 재시도 안 했고 + refresh 토큰 보유 → 갱신 후 1회 재시도
    if (status === 401 && original && !original._retry) {
      const auth = useAuthStore()
      if (auth.refresh) {
        original._retry = true
        try {
          if (!refreshPromise) refreshPromise = refreshAccessToken()
          const newAccess = await refreshPromise
          refreshPromise = null
          original.headers.Authorization = `Bearer ${newAccess}`
          return client(original)
        } catch (e) {
          refreshPromise = null
          auth.clear()
          router.push({ name: 'login' })
          return Promise.reject(e)
        }
      }
      // refresh 토큰이 없으면 로그인으로
      auth.clear()
      router.push({ name: 'login' })
    }

    return Promise.reject(error)
  },
)

export default client
