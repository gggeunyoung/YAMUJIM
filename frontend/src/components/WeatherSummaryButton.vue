<script setup>
import { ref } from 'vue'
import { fetchTripWeatherSummary } from '../api/trips'

const props = defineProps({
  tripId: { type: [String, Number], required: true },
})

const open = ref(false)
const loading = ref(false)
const error = ref('')
const summary = ref(null) // ai_summary
const trip = ref(null) // weather.trip 표시용(선택)

async function openSummary() {
  open.value = true
  // 이미 받아온 게 있으면 재요청 안 함
  if (summary.value || loading.value) return
  await load()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchTripWeatherSummary(props.tripId)
    summary.value = data.ai_summary || null
    if (!summary.value) error.value = '요약 결과가 비어 있어요.'
  } catch (e) {
    error.value = e.response?.data?.detail
      || '날씨 요약을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <button class="weather-btn" type="button" @click="openSummary">
    <span class="weather-btn__icon">☀️</span>
    <span class="weather-btn__label">날씨 AI 요약</span>
  </button>

  <Transition name="ws">
    <div v-if="open" class="ws-root">
      <div class="backdrop" @click="open = false" />
      <div class="panel">
        <header class="panel__head">
          <h2>여행 기간 날씨 요약</h2>
          <button class="close" type="button" aria-label="닫기" @click="open = false">✕</button>
        </header>

        <!-- 로딩 -->
        <div v-if="loading" class="state">
          <div class="state__icon">🌤️</div>
          <p>AI가 날씨를 분석하는 중...</p>
          <p class="muted">최대 1~2분 걸릴 수 있어요</p>
        </div>

        <!-- 에러 -->
        <div v-else-if="error" class="state">
          <div class="state__icon">😅</div>
          <p class="err">{{ error }}</p>
          <button class="retry" type="button" @click="load">다시 시도</button>
        </div>

        <!-- 결과 -->
        <div v-else-if="summary" class="content">
          <p v-if="summary.headline" class="headline">{{ summary.headline }}</p>
          <p v-if="summary.summary" class="summary">{{ summary.summary }}</p>

          <section v-if="summary.alerts && summary.alerts.length" class="block">
            <h3>⚠️ 주의</h3>
            <div class="alerts">
              <span v-for="(a, i) in summary.alerts" :key="i" class="alert">{{ a }}</span>
            </div>
          </section>

          <section v-if="summary.daily && summary.daily.length" class="block">
            <h3>📅 일자별</h3>
            <ul class="daily">
              <li v-for="(d, i) in summary.daily" :key="i">
                <span class="daily__date">{{ d.date }}</span>
                <span class="daily__text">{{ d.summary }}</span>
              </li>
            </ul>
          </section>

          <section v-if="summary.packing_notes && summary.packing_notes.length" class="block">
            <h3>🎒 챙기면 좋은 것</h3>
            <ul class="notes">
              <li v-for="(n, i) in summary.packing_notes" :key="i">{{ n }}</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.weather-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  border-radius: 20px;
  border: 1px solid rgba(26, 83, 92, 0.18);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ocean);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(26, 83, 92, 0.12);
  transition: background 0.15s, transform 0.15s;
}
.weather-btn:hover { background: #fff; transform: translateY(-1px); }
.weather-btn__icon { font-size: 1rem; }

.ws-root { position: fixed; inset: 0; z-index: 110; display: flex; align-items: center; justify-content: center; padding: 20px; }
.backdrop { position: absolute; inset: 0; background: rgba(20, 30, 35, 0.5); }
.panel {
  position: relative;
  width: 100%;
  max-width: 460px;
  max-height: 84vh;
  overflow-y: auto;
  background: linear-gradient(180deg, #fdf8f3 0%, var(--sand) 100%);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  padding: 22px;
  box-sizing: border-box;
}
.panel__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.panel__head h2 { font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif; color: var(--ocean); font-size: 1.25rem; margin: 0; }
.close { background: none; border: none; font-size: 1.1rem; color: var(--muted); cursor: pointer; }

.state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 40px 0; color: var(--muted); text-align: center; }
.state__icon { font-size: 3rem; animation: bob 1.4s ease-in-out infinite; }
.muted { color: var(--muted); font-size: 0.82rem; margin: 0; }
.err { color: #c62828; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.retry { margin-top: 8px; background: var(--ocean); color: #fff; border: none; border-radius: 10px; padding: 10px 18px; font-weight: 700; cursor: pointer; }

.headline { font-size: 1.1rem; font-weight: 800; color: var(--ocean); margin: 0 0 8px; line-height: 1.4; }
.summary { font-size: 0.92rem; line-height: 1.6; color: var(--ink); margin: 0 0 18px; }

.block { margin-bottom: 18px; }
.block:last-child { margin-bottom: 0; }
.block h3 { font-size: 0.9rem; color: var(--ocean); margin: 0 0 10px; }

.alerts { display: flex; flex-wrap: wrap; gap: 8px; }
.alert {
  font-size: 0.8rem; font-weight: 600;
  color: #b5651d;
  background: #fff3e0;
  border: 1px solid #f0d0a0;
  padding: 6px 12px; border-radius: 12px;
}

.daily { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.daily li {
  display: flex; gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
}
.daily__date { font-size: 0.78rem; font-weight: 700; color: var(--ocean); flex-shrink: 0; min-width: 86px; }
.daily__text { font-size: 0.82rem; color: var(--ink); line-height: 1.45; }

.notes { margin: 0; padding-left: 18px; }
.notes li { font-size: 0.85rem; line-height: 1.6; color: var(--ink); }

.ws-enter-active, .ws-leave-active { transition: opacity 0.2s ease; }
.ws-enter-active .panel, .ws-leave-active .panel { transition: transform 0.22s ease; }
.ws-enter-from, .ws-leave-to { opacity: 0; }
.ws-enter-from .panel, .ws-leave-to .panel { transform: scale(0.95); }
</style>
