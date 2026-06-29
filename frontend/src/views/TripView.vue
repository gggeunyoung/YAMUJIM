<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCountries, fetchCities } from '../api/places'
import { createTrip } from '../api/trips'

const router = useRouter()

const COMPANIONS = [
  { value: 'alone', label: '혼자', emoji: '🧍' },
  { value: 'friend', label: '친구', emoji: '👫' },
  { value: 'family', label: '가족', emoji: '👨‍👩‍👧' },
  { value: 'couple', label: '연인', emoji: '💑' },
  { value: 'seeking', label: '동행 구함', emoji: '🙋' },
]
const ACCOMMODATIONS = [
  { value: 'hotel', label: '호텔/리조트/아파트', emoji: '🏨' },
  { value: 'guesthouse', label: '게스트하우스/호스텔', emoji: '🛏️' },
  { value: 'capsule', label: '캡슐호텔', emoji: '📦' },
]

// 기본 날짜: 2주 뒤 출발, 3박 4일
function isoAfter(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

const form = reactive({
  country: '',
  city: '',
  companion_type: 'friend',
  companion_count: 2,
  start_date: isoAfter(14),
  end_date: isoAfter(17),
  local_language_ok: false,
  accommodation_type: 'hotel',
})

const countries = ref([])
const cities = ref([])
const countryQuery = ref('')
const countryPickerOpen = ref(false)
const loadingCities = ref(false)
const submitting = ref(false)
const error = ref('')
const advancedModel = ref('')
const ADVANCED_MODELS = [
  { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
  { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
]

const isAlone = computed(() => form.companion_type === 'alone')
const filteredCountries = computed(() => {
  const query = countryQuery.value.trim().toLocaleLowerCase()
  if (!query) return countries.value
  return countries.value.filter((country) =>
    country.name.toLocaleLowerCase().startsWith(query),
  )
})

function handleCountryInput() {
  form.country = ''
  countryPickerOpen.value = true
}

function selectCountry(country) {
  form.country = country.id
  countryQuery.value = country.name
  countryPickerOpen.value = false
}

// 혼자면 인원 1로 고정
watch(isAlone, (v) => { if (v) form.companion_count = 1 })

// 국가 변경 시 도시 목록 갱신 + 도시 선택 초기화
watch(() => form.country, async (countryId) => {
  form.city = ''
  cities.value = []
  if (!countryId) return
  loadingCities.value = true
  try {
    const { data } = await fetchCities(countryId)
    cities.value = data
  } catch (e) {
    error.value = '도시 목록을 불러오지 못했습니다.'
  } finally {
    loadingCities.value = false
  }
})

onMounted(async () => {
  try {
    const { data } = await fetchCountries()
    countries.value = data
  } catch (e) {
    error.value = '국가 목록을 불러오지 못했습니다.'
  }
})

const canSubmit = computed(() =>
  form.country && form.city && form.start_date && form.end_date
  && form.start_date <= form.end_date,
)

async function submit() {
  error.value = ''
  if (!form.country || !form.city) {
    error.value = '여행 국가와 도시를 선택해주세요.'
    return
  }
  if (form.start_date > form.end_date) {
    error.value = '도착일이 출발일보다 빠를 수 없습니다.'
    return
  }
  submitting.value = true
  try {
    const { data } = await createTrip({
      country: Number(form.country),
      city: Number(form.city),
      companion_type: form.companion_type,
      companion_count: form.companion_count,
      start_date: form.start_date,
      end_date: form.end_date,
      local_language_ok: form.local_language_ok,
      accommodation_type: form.accommodation_type,
    })
    // 결과 페이지 헤더용 라벨(도시 + 박수). 새로고침 시엔 사라지므로 표시용으로만.
    const cityName = cities.value.find((c) => c.id === Number(form.city))?.name || ''
    const nights = Math.max(0, Math.round(
      (new Date(form.end_date) - new Date(form.start_date)) / 86400000))
    const tripLabel = cityName ? `${cityName} ${nights}박 ${nights + 1}일` : ''

    // 생성된 여행 id로 추천 결과 페이지 이동 → 거기서 실제 추천 생성
    router.push({
      name: 'result',
      params: { tripId: data.id },
      state: { tripLabel, advancedModel: advancedModel.value },
    })
  } catch (e) {
    const d = e.response?.data
    error.value = (d && (d.city || d.end_date || d.detail))
      || '여행 정보 저장에 실패했습니다. 입력값을 확인해주세요.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="trip-page">
    <header class="trip-hero">
      <span class="kicker">STEP 2 · 여행 정보</span>
      <h1>어디로, 누구랑 갈 거야?</h1>
      <p>언제 가는지도 알려줄래?</p>
    </header>

    <main class="trip-main">
      <div class="trip-grid">
      <!-- 목적지 -->
      <section class="card">
        <h2><span class="bar"></span>목적지</h2>
        <label class="field">
          <span>국가</span>
          <div class="country-combobox">
            <input
              v-model="countryQuery"
              type="text"
              placeholder="국가를 선택하세요"
              autocomplete="off"
              @focus="countryPickerOpen = true"
              @input="handleCountryInput"
              @blur="countryPickerOpen = false"
              @keydown.enter.prevent="filteredCountries[0] && selectCountry(filteredCountries[0])"
              @keydown.escape="countryPickerOpen = false"
            >
            <div v-if="countryPickerOpen" class="country-options">
              <button
                v-for="c in filteredCountries"
                :key="c.id"
                type="button"
                @mousedown.prevent="selectCountry(c)"
              >
                {{ c.name }}
              </button>
              <p v-if="!filteredCountries.length">일치하는 국가가 없어요</p>
            </div>
          </div>
        </label>
        <label class="field">
          <span>도시</span>
          <select v-model="form.city" :disabled="!form.country || loadingCities">
            <option value="" disabled>
              {{ !form.country ? '국가를 먼저 선택' : (loadingCities ? '불러오는 중...' : '도시를 선택하세요') }}
            </option>
            <option v-for="c in cities" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
      </section>

      <!-- 동행 -->
      <section class="card">
        <h2><span class="bar"></span>동행</h2>
        <div class="opts opts--wrap">
          <button
            v-for="o in COMPANIONS"
            :key="o.value"
            type="button"
            class="opt"
            :class="{ 'opt--on': form.companion_type === o.value }"
            @click="form.companion_type = o.value"
          >
            <span class="opt__emoji">{{ o.emoji }}</span>
            <strong>{{ o.label }}</strong>
          </button>
        </div>
        <label class="field field--inline" v-if="!isAlone">
          <span>총 인원</span>
          <div class="stepper">
            <button type="button" @click="form.companion_count = Math.max(1, form.companion_count - 1)">−</button>
            <span class="stepper__val">{{ form.companion_count }}</span>
            <button type="button" @click="form.companion_count++">+</button>
          </div>
        </label>
      </section>

      <!-- 기간 -->
      <section class="card">
        <h2><span class="bar"></span>여행 기간</h2>
        <div class="dates">
          <label class="field">
            <span>출발일</span>
            <input type="date" v-model="form.start_date" />
          </label>
          <label class="field">
            <span>도착일</span>
            <input type="date" v-model="form.end_date" :min="form.start_date" />
          </label>
        </div>
      </section>

      <!-- 숙소 -->
      <section class="card">
        <h2><span class="bar"></span>숙소 형태</h2>
        <div class="opts opts--wrap">
          <button
            v-for="o in ACCOMMODATIONS"
            :key="o.value"
            type="button"
            class="opt opt--wide"
            :class="{ 'opt--on': form.accommodation_type === o.value }"
            @click="form.accommodation_type = o.value"
          >
            <span class="opt__emoji">{{ o.emoji }}</span>
            <strong>{{ o.label }}</strong>
          </button>
        </div>
      </section>

      <!-- 현지어 -->
      <section class="card card--full">
        <label class="toggle">
          <span>
            <strong>현지 언어로 소통 가능</strong>
            <em>(현지어/영어로 의사소통에 무리가 없어요)</em>
          </span>
          <input type="checkbox" v-model="form.local_language_ok" />
        </label>
      </section>
      </div>

      <p v-if="error" class="error">⚠️ {{ error }}</p>

      <div class="submit-row">
        <button class="submit" :disabled="!canSubmit || submitting" @click="submit">
          {{ submitting ? '챙기는 중...' : '이제 내가 챙겨줄게 →' }}
        </button>
        <label class="advanced-select">
          <span>모델 선택</span>
          <select v-model="advancedModel">
            <option value="">기본 모델</option>
            <option v-for="model in ADVANCED_MODELS" :key="model.value" :value="model.value">
              {{ model.label }}
            </option>
          </select>
        </label>
      </div>
    </main>
  </div>
</template>

<style scoped>
.trip-page { max-width: var(--container); margin: 0 auto; padding: 40px 24px 72px; }
.trip-hero { margin-bottom: 28px; }
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
.trip-hero h1 {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ink);
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
}
.trip-hero p { color: var(--muted); font-size: 1rem; margin: 0; }

.trip-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}
.card--full { grid-column: 1 / -1; }

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
  margin: 0 0 18px;
}
.bar {
  width: 5px;
  height: 18px;
  border-radius: 3px;
  background: var(--grad-accent);
  flex-shrink: 0;
}

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.field:last-child { margin-bottom: 0; }
.field > span { font-size: 0.85rem; font-weight: 600; }
.field select, .field input[type="date"], .field input[type="text"] {
  padding: 12px;
  border-radius: 10px;
  border: 1.5px solid rgba(26, 83, 92, 0.2);
  background: #fff;
  font-size: 0.95rem;
  font-family: inherit;
  color: var(--ink);
}
.field select:disabled { background: #f3f3f3; color: var(--muted); }
.country-combobox {
  position: relative;
}
.country-combobox input {
  width: 100%;
}
.country-options {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  max-height: 220px;
  overflow-y: auto;
  padding: 6px;
  border: 1.5px solid rgba(26, 83, 92, 0.16);
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(12, 36, 40, 0.14);
}
.country-options button {
  width: 100%;
  border: 0;
  border-radius: 8px;
  padding: 10px;
  background: transparent;
  color: var(--ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.country-options button:hover {
  background: rgba(26, 83, 92, 0.07);
}
.country-options p {
  margin: 0;
  padding: 10px;
  color: var(--muted);
  font-size: 0.9rem;
}

.dates { display: flex; gap: 12px; }
.dates .field { flex: 1; margin-bottom: 0; }

.opts { display: flex; gap: 8px; }
.opts--wrap { flex-wrap: wrap; }
.opt {
  flex: 1;
  min-width: 88px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: 12px;
  border: 1.5px solid rgba(26, 83, 92, 0.18);
  background: #fff;
  cursor: pointer;
  transition: all 0.12s;
}
.opt--wide { min-width: 140px; }
.opt__emoji { font-size: 1.4rem; }
.opt strong { font-size: 0.82rem; color: var(--ink); }
.opt--on { border-color: var(--ocean); background: rgba(26, 83, 92, 0.06); }
.opt--on strong { color: var(--ocean); }

.field--inline { flex-direction: row; align-items: center; justify-content: space-between; margin-top: 16px; }
.stepper { display: flex; align-items: center; gap: 14px; }
.stepper button {
  width: 34px; height: 34px;
  border-radius: 50%;
  border: 1.5px solid rgba(26, 83, 92, 0.25);
  background: #fff;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ocean);
  cursor: pointer;
}
.stepper__val { font-size: 1.1rem; font-weight: 700; min-width: 20px; text-align: center; }

.toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; cursor: pointer; }
.toggle span { display: flex; flex-direction: column; gap: 2px; }
.toggle strong { font-size: 0.92rem; }
.toggle em { font-size: 0.74rem; color: var(--muted); font-style: normal; }
.toggle input[type="checkbox"] { width: 22px; height: 22px; accent-color: var(--ocean); cursor: pointer; }

.error { color: #c62828; font-size: 0.85rem; text-align: center; margin: 22px 0 0; }
.submit-row {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 16px;
  margin-top: 28px;
  flex-wrap: wrap;
}
.submit {
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
.advanced-select {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.advanced-select span {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ocean);
}
.advanced-select select {
  background: #fff;
  color: var(--ocean);
  border: 1.5px solid rgba(26, 83, 92, 0.22);
  border-radius: 14px;
  padding: 13px 16px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
}
.advanced-select select:focus {
  outline: none;
  border-color: var(--ocean);
  box-shadow: 0 0 0 3px rgba(26, 83, 92, 0.12);
}

@media (max-width: 760px) {
  .trip-grid { grid-template-columns: 1fr; }
}
@media (max-width: 480px) {
  .trip-page { padding: 28px 16px 56px; }
  .trip-hero h1 { font-size: 1.7rem; }
  .submit { min-width: 0; width: 100%; }
  .submit-row { flex-direction: column; align-items: stretch; }
}
</style>
