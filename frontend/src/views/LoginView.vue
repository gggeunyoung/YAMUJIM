<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { fetchKakaoAuthorizeUrl, devLogin } from '../api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const loading = ref('')
const error = ref('')
const devUsername = ref('')

function goAfterLogin(user) {
  const next = route.query.next
  if (next) {
    router.push(String(next))
    return
  }
  if (!user?.profile_complete) {
    router.push({ name: 'profile' })
    return
  }
  router.push({ name: 'home' })
}

async function loginWithKakao() {
  error.value = ''
  loading.value = 'kakao'
  try {
    const { data } = await fetchKakaoAuthorizeUrl()
    window.location.href = data.authorize_url
  } catch (e) {
    loading.value = ''
    error.value = '카카오 로그인 URL을 가져오지 못했습니다. 백엔드 설정을 확인해주세요.'
  }
}

async function loginAsDev() {
  error.value = ''
  const username = devUsername.value.trim()
  if (!username) {
    error.value = '개발자 로그인용 사용자명을 입력해주세요.'
    return
  }
  loading.value = 'dev'
  try {
    const { data } = await devLogin(username)
    auth.setTokens({ access: data.access, refresh: data.refresh })
    auth.setUser(data.user)
    goAfterLogin(data.user)
  } catch (e) {
    const detail = e.response?.data
    error.value = detail?.username?.[0]
      || (e.response?.status === 403
        ? '개발자 로그인은 DEBUG 환경에서만 가능합니다.'
        : '개발자 로그인에 실패했습니다.')
  } finally {
    loading.value = ''
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="logo-row">
        <span class="logo-emoji">🧳</span>
        <h1 class="logo-text">야무짐</h1>
      </div>
      <p class="tagline">AI가 딱 맞는 여행 준비물을 추천해드려요</p>

      <button class="btn btn--kakao" :disabled="!!loading" @click="loginWithKakao">
        <span v-if="loading === 'kakao'">이동 중...</span>
        <span v-else>카카오로 시작하기</span>
      </button>

      <div class="dev-box">
        <label class="dev-label" for="dev-username">개발자 로그인 (DEBUG)</label>
        <input
          id="dev-username"
          v-model="devUsername"
          type="text"
          class="dev-input"
          maxlength="30"
          placeholder="사용자명 입력"
          :disabled="!!loading"
          @keyup.enter="loginAsDev"
        />
        <button class="btn btn--dev" :disabled="!!loading" @click="loginAsDev">
          <span v-if="loading === 'dev'">로그인 중...</span>
          <span v-else>입력한 이름으로 시작</span>
        </button>
      </div>

      <p v-if="error" class="error">⚠️ {{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.auth-card {
  width: 100%;
  max-width: 360px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(26, 83, 92, 0.1);
  border-radius: 20px;
  padding: 36px 28px;
  text-align: center;
  box-shadow: 0 12px 40px rgba(26, 83, 92, 0.1);
}
.logo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 6px;
}
.logo-emoji { font-size: 2.2rem; }
.logo-text {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  font-size: 2rem;
  color: var(--ocean);
  margin: 0;
}
.tagline {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0 0 28px;
}
.btn {
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 14px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 12px;
}
.btn:disabled { opacity: 0.6; cursor: default; }
.btn--kakao { background: #fee500; color: #191600; }
.btn--dev { background: var(--ocean); color: #fff; margin-bottom: 0; }
.dev-box {
  margin-top: 4px;
  padding-top: 16px;
  border-top: 1px dashed rgba(26, 83, 92, 0.15);
  text-align: left;
}
.dev-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--ocean);
  margin-bottom: 8px;
}
.dev-input {
  width: 100%;
  border: 1px solid rgba(26, 83, 92, 0.2);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 0.95rem;
  margin-bottom: 10px;
  box-sizing: border-box;
}
.dev-input:disabled { opacity: 0.6; }
.error {
  color: #c62828;
  font-size: 0.82rem;
  margin: 12px 0 0;
  line-height: 1.4;
  text-align: center;
}
</style>
