<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchPreference, savePreference, fetchVisitPlaceTypes } from '../api/preference'

const router = useRouter()

// 5척도 문항 (1~5). 모델 필드명 그대로.
const SCALES = [
  { key: 'hygiene_sensitivity', label: '위생에 얼마나 민감한가요?', min: '둔감해요', max: '매우 민감해요' },
  { key: 'preparedness', label: '여행 준비는 얼마나 철저한가요?', min: '즉흥적', max: '만반의 준비' },
  { key: 'heat_tolerance', label: '더위를 얼마나 잘 견디나요?', min: '더위에 약함', max: '잘 견딤' },
  { key: 'cold_tolerance', label: '추위를 얼마나 잘 견디나요?', min: '추위에 약함', max: '잘 견딤' },
  { key: 'korean_food_need', label: '여행 중 한식이 얼마나 필요한가요?', min: '없어도 OK', max: '죽어도 한식' },
]

// 단일 선택 문항 (모델 choices 값)
const MOVEMENT = [
  { value: 'walker', label: '워킹맨', desc: '많이 걸어도 좋아요' },
  { value: 'moderate', label: '적당히', desc: '무리 없이' },
  { value: 'minimal', label: '걷는 거 최소', desc: '이동은 짧게' },
]
const CONSUMPTION = [
  { value: 'souvenir', label: '기념품', desc: '쇼핑·기념품 위주' },
  { value: 'value', label: '가성비', desc: '합리적인 소비' },
  { value: 'premium', label: '가심비', desc: '경험에 투자' },
]
const PLANNING = [
  { value: 'spontaneous', label: '즉흥적', desc: '발길 닿는 대로' },
  { value: 'planned', label: '계획적', desc: '동선·일정 계획' },
]

const form = reactive({
  hygiene_sensitivity: 3,
  preparedness: 3,
  heat_tolerance: 3,
  cold_tolerance: 3,
  korean_food_need: 3,
  movement_type: 'moderate',
  consumption_type: 'value',
  planning_type: 'planned',
  visit_place_types: [], // 선택된 PK 배열
})

const visitTypes = ref([]) // [{id, name}]
const loading = ref(true)
const saving = ref(false)
const error = ref('')

function toggleVisit(id) {
  const i = form.visit_place_types.indexOf(id)
  if (i === -1) form.visit_place_types.push(id)
  else form.visit_place_types.splice(i, 1)
}

onMounted(async () => {
  try {
    const [{ data: types }, { data: pref }] = await Promise.all([
      fetchVisitPlaceTypes(),
      fetchPreference(),
    ])
    visitTypes.value = types
    // 기존 취향이 있으면 폼 prefill
    if (pref) {
      for (const k of ['hygiene_sensitivity', 'preparedness', 'heat_tolerance', 'cold_tolerance', 'korean_food_need']) {
        if (pref[k] != null) form[k] = pref[k]
      }
      const s = pref.travel_style || {}
      if (s.movement_type) form.movement_type = s.movement_type
      if (s.consumption_type) form.consumption_type = s.consumption_type
      if (s.planning_type) form.planning_type = s.planning_type
      if (Array.isArray(s.visit_place_types)) form.visit_place_types = [...s.visit_place_types]
    }
  } catch (e) {
    error.value = '취향 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
})

async function submit() {
  error.value = ''
  saving.value = true
  const payload = {
    hygiene_sensitivity: form.hygiene_sensitivity,
    preparedness: form.preparedness,
    heat_tolerance: form.heat_tolerance,
    cold_tolerance: form.cold_tolerance,
    korean_food_need: form.korean_food_need,
    travel_style: {
      movement_type: form.movement_type,
      consumption_type: form.consumption_type,
      planning_type: form.planning_type,
      visit_place_types: form.visit_place_types,
    },
  }
  try {
    await savePreference(payload)
    router.push({ name: 'trip' })
  } catch (e) {
    error.value = '저장에 실패했습니다. 입력값을 확인해주세요.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="pref-page">
    <header class="pref-hero">
      <span class="kicker">STEP 1 · 취향</span>
      <h1>당신은 어떤 여행자인가요?</h1>
      <p>몇 가지만 알려주시면 더 정확한 준비물을 추천해드려요</p>
    </header>

    <div v-if="loading" class="loading">불러오는 중...</div>

    <main v-else class="pref-main">
      <div class="pref-grid">
      <!-- 5척도 -->
      <section class="card card--scale">
        <h2><span class="bar"></span>나는 이런 사람</h2>
        <div v-for="s in SCALES" :key="s.key" class="scale">
          <p class="scale__label">{{ s.label }}</p>
          <div class="scale__row">
            <span class="scale__end">{{ s.min }}</span>
            <div class="scale__dots">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                class="dot"
                :class="{ 'dot--on': form[s.key] === n }"
                @click="form[s.key] = n"
              >{{ n }}</button>
            </div>
            <span class="scale__end">{{ s.max }}</span>
          </div>
        </div>
      </section>

      <!-- 관광 스타일 -->
      <section class="card card--style">
        <h2><span class="bar"></span>여행 스타일</h2>

        <div class="choice-group">
          <p class="choice__title">이동량</p>
          <div class="choice__opts">
            <button
              v-for="o in MOVEMENT"
              :key="o.value"
              type="button"
              class="opt"
              :class="{ 'opt--on': form.movement_type === o.value }"
              @click="form.movement_type = o.value"
            >
              <strong>{{ o.label }}</strong>
              <span>{{ o.desc }}</span>
            </button>
          </div>
        </div>

        <div class="choice-group">
          <p class="choice__title">소비 성향</p>
          <div class="choice__opts">
            <button
              v-for="o in CONSUMPTION"
              :key="o.value"
              type="button"
              class="opt"
              :class="{ 'opt--on': form.consumption_type === o.value }"
              @click="form.consumption_type = o.value"
            >
              <strong>{{ o.label }}</strong>
              <span>{{ o.desc }}</span>
            </button>
          </div>
        </div>

        <div class="choice-group">
          <p class="choice__title">계획 성향</p>
          <div class="choice__opts">
            <button
              v-for="o in PLANNING"
              :key="o.value"
              type="button"
              class="opt"
              :class="{ 'opt--on': form.planning_type === o.value }"
              @click="form.planning_type = o.value"
            >
              <strong>{{ o.label }}</strong>
              <span>{{ o.desc }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- 방문 장소 유형 (다중) -->
      <section class="card card--theme">
        <h2><span class="bar"></span>관심 있는 여행 테마 <span class="muted">(여러 개 선택)</span></h2>
        <div class="chips">
          <button
            v-for="t in visitTypes"
            :key="t.id"
            type="button"
            class="chip"
            :class="{ 'chip--on': form.visit_place_types.includes(t.id) }"
            @click="toggleVisit(t.id)"
          >{{ t.name }}</button>
        </div>
      </section>
      </div>

      <p v-if="error" class="error">⚠️ {{ error }}</p>

      <button class="submit" :disabled="saving" @click="submit">
        {{ saving ? '저장 중...' : '저장하고 여행 정보 입력 →' }}
      </button>
    </main>
  </div>
</template>

<style scoped>
.pref-page {
  max-width: var(--container);
  margin: 0 auto;
  padding: 40px 24px 72px;
}
.pref-hero { margin-bottom: 28px; }
.kicker {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  border: 1px solid var(--line);
  padding: 6px 13px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.pref-hero h1 {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ink);
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
}
.pref-hero p { color: var(--muted); font-size: 1rem; margin: 0; }
.loading { text-align: center; color: var(--muted); padding: 60px 0; }

.pref-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-areas:
    "scale style"
    "scale theme";
  gap: 20px;
  align-items: stretch;
}
.card--scale {
  grid-area: scale;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.card--style { grid-area: style; }
.card--theme { grid-area: theme; }

.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 26px 24px;
  box-shadow: var(--shadow-soft);
}
.card h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ink);
  font-size: 1.15rem;
  font-weight: 800;
  margin: 0 0 20px;
}
.bar {
  width: 5px;
  height: 18px;
  border-radius: 3px;
  background: var(--grad-accent);
  flex-shrink: 0;
}
.muted { color: var(--muted); font-size: 0.8rem; font-weight: 400; }

/* 5척도 */
.scale { margin-bottom: 18px; }
.scale:last-child { margin-bottom: 0; }
.scale__label { font-size: 0.92rem; font-weight: 600; margin: 0 0 8px; }
.scale__row { display: flex; align-items: center; gap: 8px; }
.scale__end { font-size: 0.7rem; color: var(--muted); width: 84px; flex-shrink: 0; word-break: keep-all; line-height: 1.3; }
.scale__end:last-child { text-align: right; }
.scale__dots { display: flex; gap: 6px; flex: 1; justify-content: center; }
.dot {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1.5px solid rgba(26, 83, 92, 0.25);
  background: #fff;
  color: var(--muted);
  font-weight: 700;
  cursor: pointer;
  transition: all 0.12s;
}
.dot--on {
  background: var(--ocean);
  border-color: var(--ocean);
  color: #fff;
  transform: scale(1.08);
}

/* 단일 선택 */
.choice-group { margin-bottom: 16px; }
.choice-group:last-child { margin-bottom: 0; }
.choice__title { font-size: 0.88rem; font-weight: 600; margin: 0 0 8px; }
.choice__opts { display: flex; gap: 8px; }
.opt {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 8px;
  border-radius: 12px;
  border: 1.5px solid rgba(26, 83, 92, 0.18);
  background: #fff;
  cursor: pointer;
  transition: all 0.12s;
}
.opt strong { color: var(--ink); font-size: 0.9rem; }
.opt span { color: var(--muted); font-size: 0.72rem; }
.opt--on {
  border-color: var(--ocean);
  background: rgba(26, 83, 92, 0.06);
}
.opt--on strong { color: var(--ocean); }

/* 칩 */
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  padding: 9px 14px;
  border-radius: 20px;
  border: 1.5px solid rgba(26, 83, 92, 0.2);
  background: #fff;
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.12s;
}
.chip--on {
  background: var(--ocean);
  border-color: var(--ocean);
  color: #fff;
}

.error { color: #c62828; font-size: 0.85rem; text-align: center; margin: 20px 0 0; }
.submit {
  display: block;
  margin: 28px auto 0;
  min-width: 320px;
  background: var(--grad-accent);
  color: #fff;
  border: none;
  border-radius: 16px;
  padding: 17px 32px;
  font-size: 1.05rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: var(--shadow-soft);
  transition: transform 0.15s, box-shadow 0.15s;
}
.submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lift);
}
.submit:disabled { opacity: 0.6; cursor: default; }

@media (max-width: 860px) {
  .pref-grid {
    grid-template-columns: 1fr;
    grid-template-areas: "scale" "style" "theme";
  }
}
@media (max-width: 480px) {
  .pref-page { padding: 28px 16px 56px; }
  .pref-hero h1 { font-size: 1.7rem; }
  .submit { min-width: 0; width: 100%; }
}
</style>
