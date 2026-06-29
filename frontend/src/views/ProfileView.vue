<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { updateProfile } from '../api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const gender = ref(auth.user?.gender || '')
const birthDate = ref(auth.user?.birth_date || '')
const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => gender.value && birthDate.value && !loading.value)

const loginLabel = computed(() => {
  if (auth.user?.nickname) return `${auth.user.nickname}님, 환영해요!`
  if (auth.user?.social_provider === 'kakao') return '카카오 로그인 완료'
  return '로그인 완료'
})

function goNext() {
  const next = route.query.next
  router.replace(next ? String(next) : { name: 'preference' })
}

function logout() {
  auth.clear()
  router.replace({ name: 'login' })
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await updateProfile({
      gender: gender.value,
      birth_date: birthDate.value,
    })
    auth.setUser(data)
    goNext()
  } catch (e) {
    const detail = e.response?.data
    if (typeof detail === 'object' && detail) {
      const birthErr = detail.birth_date
      error.value = Array.isArray(birthErr) ? birthErr[0] : birthErr
        || detail.detail
        || '프로필 저장에 실패했습니다.'
    } else {
      error.value = '프로필 저장에 실패했습니다.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="card">
      <div class="logo-row">
        <span class="logo-emoji">🧳</span>
        <h1 class="logo-text">야무짐</h1>
      </div>

      <p class="steps">
        <span class="steps__done">① 로그인</span>
        <span class="steps__arrow">→</span>
        <span class="steps__current">② 여행자 정보</span>
        <span class="steps__arrow">→</span>
        <span class="steps__next">③ 취향 테스트</span>
      </p>

      <p class="welcome">{{ loginLabel }}</p>
      <p class="desc">맞춤 짐 추천을 위해 성별과 생년월일을 입력해주세요.</p>

      <section class="block">
        <h2 class="label">성별</h2>
        <div class="gender-row">
          <button
            type="button"
            class="chip"
            :class="{ 'chip--on': gender === 'female' }"
            @click="gender = 'female'"
          >
            여자
          </button>
          <button
            type="button"
            class="chip"
            :class="{ 'chip--on': gender === 'male' }"
            @click="gender = 'male'"
          >
            남자
          </button>
        </div>
      </section>

      <section class="block">
        <h2 class="label">생년월일</h2>
        <input
          v-model="birthDate"
          class="date-input"
          type="date"
          :max="new Date().toISOString().slice(0, 10)"
        />
        <p class="hint">만 10세~100세 여행자만 이용할 수 있어요.</p>
      </section>

      <p v-if="error" class="error">{{ error }}</p>

      <button class="submit" type="button" :disabled="!canSubmit" @click="submit">
        {{ loading ? '저장 중...' : '다음' }}
      </button>

      <button class="logout" type="button" @click="logout">
        다른 계정으로 로그인 (카카오)
      </button>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.card {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(26, 83, 92, 0.1);
  border-radius: 20px;
  padding: 32px 28px;
  box-shadow: 0 12px 40px rgba(26, 83, 92, 0.1);
}
.logo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 14px;
}
.logo-emoji { font-size: 2rem; }
.logo-text {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ocean);
  margin: 0;
  font-size: 1.75rem;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px 6px;
  font-size: 0.72rem;
  margin: 0 0 12px;
  color: var(--muted);
}
.steps__done { color: var(--ocean); font-weight: 700; }
.steps__current { color: var(--ocean); font-weight: 800; }
.steps__next { opacity: 0.55; }
.steps__arrow { opacity: 0.4; font-size: 0.65rem; }
.welcome {
  text-align: center;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ocean);
  margin: 0 0 6px;
}
.desc {
  color: var(--muted);
  font-size: 0.88rem;
  margin: 0 0 22px;
  line-height: 1.5;
  text-align: center;
}
.block { margin-bottom: 22px; }
.label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ocean);
  margin: 0 0 10px;
}
.gender-row { display: flex; gap: 10px; }
.chip {
  flex: 1;
  border: 2px solid rgba(26, 83, 92, 0.15);
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
}
.chip--on {
  border-color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  color: var(--ocean);
}
.date-input {
  width: 100%;
  box-sizing: border-box;
  border: 2px solid rgba(26, 83, 92, 0.15);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 1rem;
  color: var(--ink);
}
.hint {
  margin: 8px 0 0;
  font-size: 0.78rem;
  color: var(--muted);
}
.error {
  color: #c62828;
  font-size: 0.85rem;
  line-height: 1.45;
  margin: 0 0 12px;
}
.submit {
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 14px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  background: var(--ocean);
  color: #fff;
}
.submit:disabled {
  opacity: 0.5;
  cursor: default;
}
.logout {
  width: 100%;
  margin-top: 12px;
  border: none;
  background: none;
  color: var(--muted);
  font-size: 0.8rem;
  text-decoration: underline;
  cursor: pointer;
  padding: 8px;
}
.logout:hover { color: var(--ocean); }
</style>
