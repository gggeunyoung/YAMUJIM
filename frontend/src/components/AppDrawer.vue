<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { fetchMe } from '../api/auth'
import { fetchTrips } from '../api/trips'

const router = useRouter()
const auth = useAuthStore()

const open = ref(false)
const me = ref(null)
const trips = ref([])
const loadingMe = ref(false)
const loadingTrips = ref(false)
const error = ref('')

const COMPANION = {
  alone: '혼자', friend: '친구', family: '가족', couple: '연인', seeking: '동행 구함',
}
const PROVIDER = { kakao: '카카오', google: '구글' }
const GENDER = { male: '남성', female: '여성' }

function nights(t) {
  return Math.max(0, Math.round((new Date(t.end_date) - new Date(t.start_date)) / 86400000))
}

async function loadData() {
  error.value = ''
  loadingMe.value = true
  loadingTrips.value = true
  try {
    const { data } = await fetchMe()
    me.value = data
    auth.setUser(data)
  } catch (e) {
    error.value = '프로필을 불러오지 못했습니다.'
  } finally {
    loadingMe.value = false
  }
  try {
    const { data } = await fetchTrips()
    trips.value = data
  } catch (e) {
    if (!error.value) error.value = '여행 목록을 불러오지 못했습니다.'
  } finally {
    loadingTrips.value = false
  }
}

// 드로어 열릴 때마다 최신 데이터 로드
watch(open, (v) => { if (v) loadData() })

function go(path) {
  open.value = false
  router.push(path)
}

function openTrip(t) {
  open.value = false
  const label = t.city_name ? `${t.city_name} ${nights(t)}박 ${nights(t) + 1}일` : ''
  router.push({ name: 'result', params: { tripId: t.id }, state: { tripLabel: label } })
}

function editPreference() {
  go({ name: 'preference' })
}

function logout() {
  auth.clear()
  open.value = false
  router.push({ name: 'login' })
}
</script>

<template>
  <!-- 고정 버튼 -->
  <button class="fab" type="button" aria-label="내 메뉴" @click="open = true">
    <span class="fab__icon">👤</span>
  </button>

  <!-- 드로어 -->
  <Transition name="drawer">
    <div v-if="open" class="drawer-root">
      <div class="backdrop" @click="open = false" />
      <aside class="drawer">
        <header class="drawer__head">
          <h2>내 메뉴</h2>
          <button class="close" type="button" aria-label="닫기" @click="open = false">✕</button>
        </header>

        <!-- 프로필 -->
        <section class="profile">
          <div class="avatar">{{ (me?.nickname || '여')[0] }}</div>
          <div class="profile__info">
            <div v-if="loadingMe" class="muted">불러오는 중...</div>
            <template v-else-if="me">
              <p class="profile__name">
                {{ me.nickname || '여행자' }}
                <span class="provider">{{ PROVIDER[me.social_provider] || me.social_provider }}</span>
              </p>
              <p class="profile__sub">
                <span v-if="me.email">{{ me.email }}</span>
                <span v-if="me.gender">· {{ GENDER[me.gender] || me.gender }}</span>
                <span v-if="me.age_bracket_label">· {{ me.age_bracket_label }}</span>
                <span v-else-if="me.age">· 만 {{ me.age }}세</span>
              </p>
            </template>
          </div>
        </section>

        <button class="action" type="button" @click="editPreference">
          <span>🎯 취향 정보 수정</span>
          <span class="chev">›</span>
        </button>

        <!-- 내 여행 -->
        <section class="trips">
          <h3>내 여행 <span class="count" v-if="trips.length">{{ trips.length }}</span></h3>
          <div v-if="loadingTrips" class="muted pad">불러오는 중...</div>
          <div v-else-if="!trips.length" class="empty">
            아직 등록한 여행이 없어요.
            <button class="link" @click="go({ name: 'trip' })">여행 추가하기 →</button>
          </div>
          <ul v-else class="trip-list">
            <li v-for="t in trips" :key="t.id">
              <button class="trip" type="button" @click="openTrip(t)">
                <div class="trip__main">
                  <strong>{{ t.city_name }}</strong>
                  <span class="trip__country">{{ t.country_name }}</span>
                </div>
                <div class="trip__meta">
                  {{ t.start_date }} ~ {{ t.end_date }} · {{ nights(t) }}박{{ nights(t) + 1 }}일
                  · {{ COMPANION[t.companion_type] || t.companion_type }}
                </div>
                <span class="chev">›</span>
              </button>
            </li>
          </ul>
        </section>

        <p v-if="error" class="error">⚠️ {{ error }}</p>

        <button class="logout" type="button" @click="logout">로그아웃</button>
      </aside>
    </div>
  </Transition>
</template>

<style scoped>
.fab {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: var(--ocean);
  color: #fff;
  box-shadow: 0 6px 20px rgba(26, 83, 92, 0.35);
  cursor: pointer;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, box-shadow 0.15s;
}
.fab:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(26, 83, 92, 0.4); }
.fab__icon { font-size: 1.5rem; }

.drawer-root { position: fixed; inset: 0; z-index: 100; }
.backdrop { position: absolute; inset: 0; background: rgba(20, 30, 35, 0.45); }
.drawer {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: min(360px, 88vw);
  background: linear-gradient(180deg, #fdf8f3 0%, var(--sand) 100%);
  box-shadow: -8px 0 30px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
}
.drawer__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.drawer__head h2 { font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif; color: var(--ocean); font-size: 1.3rem; margin: 0; }
.close { background: none; border: none; font-size: 1.1rem; color: var(--muted); cursor: pointer; }

.profile {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  margin-bottom: 12px;
}
.avatar {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: var(--ocean);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem; font-weight: 700;
  flex-shrink: 0;
}
.profile__info { min-width: 0; }
.profile__name { margin: 0 0 4px; font-weight: 700; font-size: 1.05rem; display: flex; align-items: center; gap: 8px; }
.provider { font-size: 0.68rem; font-weight: 600; color: var(--ocean); background: rgba(26, 83, 92, 0.1); padding: 2px 8px; border-radius: 10px; }
.profile__sub { margin: 0; font-size: 0.8rem; color: var(--muted); word-break: break-all; }

.action {
  width: 100%;
  display: flex; align-items: center; justify-content: space-between;
  padding: 15px 16px;
  border-radius: 14px;
  border: 1px solid rgba(26, 83, 92, 0.12);
  background: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem; font-weight: 600; color: var(--ink);
  cursor: pointer;
  margin-bottom: 18px;
}
.action:hover { background: #fff; }

.trips { flex: 1; }
.trips h3 { font-size: 0.95rem; color: var(--ocean); margin: 0 0 10px; display: flex; align-items: center; gap: 8px; }
.count { font-size: 0.72rem; background: var(--ocean); color: #fff; border-radius: 10px; padding: 1px 8px; }
.muted { color: var(--muted); font-size: 0.85rem; }
.pad { padding: 8px 0; }
.empty { color: var(--muted); font-size: 0.85rem; padding: 16px; background: rgba(255,255,255,0.5); border-radius: 12px; text-align: center; }

.trip-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.trip {
  width: 100%;
  position: relative;
  display: block;
  text-align: left;
  padding: 13px 30px 13px 14px;
  border-radius: 14px;
  border: 1px solid rgba(26, 83, 92, 0.12);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
}
.trip:hover { background: #fff; border-color: rgba(26, 83, 92, 0.25); }
.trip__main { display: flex; align-items: baseline; gap: 8px; }
.trip__main strong { font-size: 0.98rem; color: var(--ink); }
.trip__country { font-size: 0.75rem; color: var(--muted); }
.trip__meta { font-size: 0.74rem; color: var(--muted); margin-top: 4px; }
.chev { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 1.2rem; }
.action .chev { position: static; transform: none; }

.error { color: #c62828; font-size: 0.82rem; text-align: center; }
.logout {
  width: 100%;
  margin-top: 16px;
  padding: 13px;
  border-radius: 12px;
  border: 1px solid rgba(198, 40, 40, 0.3);
  background: transparent;
  color: #c62828;
  font-weight: 600;
  cursor: pointer;
}
.logout:hover { background: rgba(198, 40, 40, 0.06); }

/* 트랜지션 */
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active .drawer, .drawer-leave-active .drawer { transition: transform 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }
</style>
