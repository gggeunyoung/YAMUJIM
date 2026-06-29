<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { kakaoLogin } from '../api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const error = ref('')

onMounted(async () => {
  // 카카오가 에러를 돌려준 경우 (사용자가 동의 취소 등)
  if (route.query.error) {
    error.value = `카카오 로그인이 취소되었거나 실패했습니다. (${route.query.error})`
    return
  }

  const code = route.query.code
  if (!code) {
    error.value = '인가 코드가 없습니다. 다시 시도해주세요.'
    return
  }

  try {
    const { data } = await kakaoLogin(String(code))
    auth.setTokens({ access: data.access, refresh: data.refresh })
    auth.setUser(data.user)
    // 신규 가입자는 취향 테스트부터, 기존 유저도 일단 취향 테스트로 진입
    router.replace({ name: 'profile' })
  } catch (e) {
    error.value = e.response?.data?.detail
      || '로그인 처리에 실패했습니다. 잠시 후 다시 시도해주세요.'
  }
})

function backToLogin() {
  router.replace({ name: 'login' })
}
</script>

<template>
  <div class="callback-page">
    <template v-if="!error">
      <div class="state__icon">🧳</div>
      <p>로그인 처리 중...</p>
    </template>
    <template v-else>
      <div class="state__icon">😅</div>
      <p class="error">{{ error }}</p>
      <button class="btn" @click="backToLogin">로그인으로 돌아가기</button>
    </template>
  </div>
</template>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: var(--muted);
  padding: 24px;
  text-align: center;
}
.state__icon { font-size: 3rem; }
.error { color: #c62828; max-width: 360px; line-height: 1.5; }
.btn {
  background: var(--ocean);
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-weight: 700;
  cursor: pointer;
}
</style>
