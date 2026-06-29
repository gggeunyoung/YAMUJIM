<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { fetchMe, updateNickname, updateProfileImage } from '../api/auth'
import { fetchTrips } from '../api/trips'
import { fetchCommunityPosts } from '../api/community'

const router = useRouter()
const auth = useAuthStore()

const me = ref(null)
const trips = ref([])
const myPosts = ref([])
const loadingMe = ref(false)
const loadingTrips = ref(false)
const loadingPosts = ref(false)
const savingNickname = ref(false)
const savingAvatar = ref(false)
const avatarInput = ref(null)
const nicknameInput = ref('')
const nicknameError = ref('')
const avatarError = ref('')
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
  loadingPosts.value = true
  try {
    const { data } = await fetchMe()
    me.value = data
    nicknameInput.value = data.nickname || ''
    auth.setUser(data)
  } catch {
    error.value = '프로필을 불러오지 못했습니다.'
  } finally {
    loadingMe.value = false
  }
  try {
    const { data } = await fetchTrips()
    trips.value = data
  } catch {
    if (!error.value) error.value = '여행 목록을 불러오지 못했습니다.'
  } finally {
    loadingTrips.value = false
  }
  try {
    const { data } = await fetchCommunityPosts()
    myPosts.value = data.filter((p) => p.is_mine)
  } catch {
    if (!error.value) error.value = '커뮤니티 글을 불러오지 못했습니다.'
  } finally {
    loadingPosts.value = false
  }
}

async function saveNickname() {
  nicknameError.value = ''
  const next = nicknameInput.value.trim()
  if (!next) {
    nicknameError.value = '닉네임을 입력해주세요.'
    return
  }
  if (next === me.value?.nickname) return
  savingNickname.value = true
  try {
    const { data } = await updateNickname(next)
    me.value = data
    auth.setUser(data)
  } catch (e) {
    const detail = e.response?.data
    nicknameError.value = detail?.nickname?.[0] || detail?.detail || '닉네임 변경에 실패했습니다.'
  } finally {
    savingNickname.value = false
  }
}

function openAvatarPicker() {
  if (savingAvatar.value) return
  avatarInput.value?.click()
}

async function changeAvatar(e) {
  avatarError.value = ''
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    avatarError.value = '이미지 파일만 업로드할 수 있습니다.'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    avatarError.value = '프로필 이미지는 2MB 이하만 업로드할 수 있습니다.'
    return
  }

  savingAvatar.value = true
  try {
    const { data } = await updateProfileImage(file)
    me.value = data
    auth.setUser(data)
  } catch (err) {
    const detail = err.response?.data
    avatarError.value = detail?.profile_image?.[0] || detail?.detail || '프로필 사진 변경에 실패했습니다.'
  } finally {
    savingAvatar.value = false
  }
}

function avatarLetter(author) {
  return (author?.nickname || '여')[0]
}

function openTrip(t) {
  const label = t.city_name ? `${t.city_name} ${nights(t)}박 ${nights(t) + 1}일` : ''
  router.push({ name: 'result', params: { tripId: t.id }, state: { tripLabel: label } })
}

function openCommunity() {
  router.push({ name: 'community' })
}

function logout() {
  auth.clear()
  router.push({ name: 'login' })
}

onMounted(loadData)
</script>

<template>
  <div class="mypage">
    <header class="mp-hero">
      <span class="kicker">MY PAGE</span>
      <h1>내 여행 보관함</h1>
      <p>프로필과 내가 만든 짐 리스트를 한눈에 관리하세요.</p>
    </header>

    <!-- 프로필 배너 -->
    <section class="card profile">
      <div class="avatar-wrap">
        <button
          type="button"
          class="avatar-button"
          :disabled="savingAvatar || loadingMe"
          aria-label="프로필 사진 변경"
          @click="openAvatarPicker"
        >
          <img
            v-if="me?.profile_image_url"
            :src="me.profile_image_url"
            alt=""
            class="avatar avatar--img"
          />
          <span v-else class="avatar">{{ avatarLetter(me) }}</span>
          <span class="avatar-edit">{{ savingAvatar ? '저장 중' : '변경' }}</span>
        </button>
        <input
          ref="avatarInput"
          type="file"
          accept="image/*"
          class="avatar-input"
          @change="changeAvatar"
        />
      </div>
      <div class="profile__body">
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
          </p>
        </template>
        <p v-if="avatarError" class="error avatar-error">{{ avatarError }}</p>
      </div>
      <div class="profile__stats">
        <div class="stat">
          <strong>{{ trips.length }}</strong>
          <span>여행</span>
        </div>
        <div class="stat">
          <strong>{{ myPosts.length }}</strong>
          <span>공유글</span>
        </div>
      </div>
    </section>

    <!-- 설정: 닉네임 + 취향 -->
    <section class="card">
      <h2 class="section-title"><span class="bar"></span>닉네임</h2>
      <p class="hint">서비스에서 보이는 이름이에요. 최대 10글자까지 변경할 수 있어요.</p>
      <div class="nickname-row">
        <input
          v-model="nicknameInput"
          type="text"
          maxlength="10"
          class="input"
          placeholder="닉네임"
        />
        <button
          type="button"
          class="btn"
          :disabled="savingNickname"
          @click="saveNickname"
        >
          {{ savingNickname ? '저장 중...' : '저장' }}
        </button>
      </div>
      <p v-if="nicknameError" class="error">{{ nicknameError }}</p>

      <button class="action" type="button" @click="router.push({ name: 'preference' })">
        <span>🎯 취향 정보 수정</span>
        <span class="chev">›</span>
      </button>
    </section>

    <!-- 내 여행 / 내가 쓴 글 -->
    <div class="mp-grid">
      <section class="card trips">
        <h2 class="section-title">
          <span class="bar"></span>내 여행
          <span v-if="trips.length" class="count">{{ trips.length }}</span>
        </h2>
        <div v-if="loadingTrips" class="muted pad">불러오는 중...</div>
        <div v-else-if="!trips.length" class="empty">
          아직 등록한 여행이 없어요.
          <button class="link" type="button" @click="router.push({ name: 'trip' })">
            여행 추가하기 →
          </button>
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

      <section class="card posts">
        <h2 class="section-title">
          <span class="bar"></span>내가 쓴 글
          <span v-if="myPosts.length" class="count">{{ myPosts.length }}</span>
        </h2>
        <div v-if="loadingPosts" class="muted pad">불러오는 중...</div>
        <div v-else-if="!myPosts.length" class="empty">
          아직 커뮤니티에 공유한 글이 없어요.
          <button class="link" type="button" @click="openCommunity">
            커뮤니티 둘러보기 →
          </button>
        </div>
        <ul v-else class="trip-list">
          <li v-for="p in myPosts" :key="p.id">
            <button class="trip" type="button" @click="openCommunity">
              <div class="trip__main">
                <strong>{{ p.title }}</strong>
              </div>
              <div class="trip__meta">
                {{ p.country_name }} · {{ p.city_name }} · {{ p.created_at?.slice(0, 10) }}
              </div>
              <div class="post-stats">
                <span>♥ {{ p.like_count }}</span>
                <span>💬 {{ p.comment_count }}</span>
              </div>
              <span class="chev">›</span>
            </button>
          </li>
        </ul>
      </section>
    </div>

    <p v-if="error" class="error center">⚠️ {{ error }}</p>

    <button class="logout" type="button" @click="logout">로그아웃</button>
  </div>
</template>

<style scoped>
.mypage {
  max-width: var(--container);
  margin: 0 auto;
  padding: 40px 24px 64px;
}
.mp-hero { margin-bottom: 26px; }
.kicker {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  border: 1px solid var(--line);
  padding: 6px 13px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.mp-hero h1 {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ink);
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
}
.mp-hero p { margin: 0; color: var(--muted); font-size: 1rem; }

.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 24px;
  margin-bottom: 18px;
  box-shadow: var(--shadow-soft);
}
.mp-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}
.mp-grid .card { margin-bottom: 0; }

/* 프로필 배너 */
.profile {
  display: flex;
  align-items: center;
  gap: 18px;
}
.avatar-wrap { position: relative; flex-shrink: 0; }
.avatar-button {
  position: relative;
  display: block;
  width: 72px;
  height: 72px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  overflow: hidden;
  cursor: pointer;
}
.avatar-button:disabled { cursor: wait; }
.avatar-input { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--grad-hero);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
  font-weight: 700;
}
.avatar--img { object-fit: cover; display: block; }
.avatar-edit {
  position: absolute;
  inset: auto 0 0;
  padding: 4px 0 5px;
  background: rgba(20, 30, 35, 0.68);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.14s ease;
}
.avatar-button:hover .avatar-edit,
.avatar-button:focus-visible .avatar-edit,
.avatar-button:disabled .avatar-edit { opacity: 1; }
.profile__body { flex: 1; min-width: 0; }
.profile__name {
  margin: 0 0 6px;
  font-size: 1.3rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 8px;
}
.provider {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.1);
  padding: 3px 9px;
  border-radius: 10px;
}
.profile__sub { margin: 0; font-size: 0.86rem; color: var(--muted); word-break: break-all; }
.avatar-error { margin-top: 5px; }
.profile__stats {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.stat {
  text-align: center;
  min-width: 64px;
  padding: 12px 10px;
  border-radius: 14px;
  background: var(--lining);
  border: 1px solid var(--line);
}
.stat strong { display: block; font-size: 1.4rem; font-weight: 900; color: var(--ocean); }
.stat span { font-size: 0.74rem; color: var(--muted); font-weight: 600; }

.section-title {
  margin: 0 0 12px;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 10px;
}
.bar {
  width: 5px;
  height: 18px;
  border-radius: 3px;
  background: var(--grad-accent);
  flex-shrink: 0;
}
.count {
  font-size: 0.74rem;
  background: var(--ocean);
  color: #fff;
  border-radius: 10px;
  padding: 1px 9px;
  font-weight: 700;
}
.hint { margin: 0 0 12px; font-size: 0.84rem; color: var(--muted); }
.nickname-row { display: flex; gap: 8px; }
.input {
  flex: 1;
  border: 1.5px solid rgba(26, 83, 92, 0.2);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 0.95rem;
}
.btn {
  border: none;
  border-radius: 12px;
  background: var(--ocean);
  color: #fff;
  font-weight: 700;
  padding: 0 20px;
  cursor: pointer;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.action {
  width: 100%;
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--lining);
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}
.action:hover { background: #fff; transform: translateY(-1px); }

.trip-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.trip {
  width: 100%;
  position: relative;
  text-align: left;
  padding: 15px 32px 15px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--lining);
  cursor: pointer;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
}
.trip:hover { background: #fff; transform: translateY(-2px); box-shadow: var(--shadow-soft); }
.trip__main { display: flex; align-items: baseline; gap: 8px; }
.trip__main strong { font-size: 1rem; }
.trip__country { font-size: 0.76rem; color: var(--muted); }
.trip__meta { font-size: 0.76rem; color: var(--muted); margin-top: 5px; }
.post-stats { display: flex; gap: 12px; margin-top: 8px; font-size: 0.78rem; color: var(--ocean); font-weight: 600; }
.chev { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 1.1rem; }
.action .chev { position: static; transform: none; }
.muted { color: var(--muted); font-size: 0.88rem; }
.pad { padding: 10px 0; }
.empty { color: var(--muted); font-size: 0.88rem; text-align: center; padding: 16px 0; }
.link { display: block; margin-top: 8px; border: none; background: none; color: var(--ocean); font-weight: 700; cursor: pointer; }
.error { color: #c62828; font-size: 0.84rem; margin: 8px 0 0; }
.center { text-align: center; }
.logout {
  display: block;
  margin: 18px auto 0;
  min-width: 220px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(198, 40, 40, 0.3);
  background: transparent;
  color: #c62828;
  font-weight: 700;
  cursor: pointer;
}
.logout:hover { background: rgba(198, 40, 40, 0.06); }

@media (max-width: 760px) {
  .mp-grid { grid-template-columns: 1fr; }
}
@media (max-width: 540px) {
  .mypage { padding: 28px 16px 56px; }
  .mp-hero h1 { font-size: 1.7rem; }
  .profile { flex-wrap: wrap; }
  .profile__stats { width: 100%; justify-content: flex-start; }
  .logout { width: 100%; min-width: 0; }
}
</style>
