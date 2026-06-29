<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import OpenSuitcase from '../components/OpenSuitcase.vue'
import SharePostModal from '../components/SharePostModal.vue'
import { fetchLatestRecommendation, createRecommendation } from '../api/recommendations'
import { fetchTrip } from '../api/trips'
import { fetchDestinationNotes } from '../api/destinationNotes'
import { fetchShareStatus, shareToCommunity } from '../api/community'
import { adaptRecommendation } from '../packing/adaptRecommendation'

const router = useRouter()
const route = useRoute()
const tripId = route.params.tripId

const label = ref(history.state?.tripLabel || '')
const advancedModel = history.state?.advancedModel
  || (history.state?.advancedMode === true ? 'gemini-2.5-flash-lite' : '')
const startDate = ref('')
const destinationNotes = ref(null)
const recommendationId = ref(null)

const items = ref([])
const loading = ref(true)
const errorMessage = ref('')
const sharing = ref(false)
const shareMessage = ref('')
const shareModalOpen = ref(false)
const alreadyShared = ref(false)

const title = computed(() => label.value || '맞춤 준비물 추천')
const summary = computed(() => (items.value.length ? `AI가 골라드린 준비물 ${items.value.length}종` : ''))
const shareDefaultTitle = computed(() => {
  if (!label.value) return '나의 여행 짐 리스트'
  return `${label.value} 짐 리스트`
})

async function loadDestinationNotesForTrip(trip) {
  if (!trip?.country || !trip?.city) return
  try {
    destinationNotes.value = await fetchDestinationNotes(trip.country, trip.city)
  } catch {
    destinationNotes.value = null
  }
}

async function syncShareStatus(recId) {
  if (!recId) {
    alreadyShared.value = false
    return
  }
  try {
    const { data } = await fetchShareStatus(recId)
    alreadyShared.value = data.shared === true
  } catch {
    alreadyShared.value = false
  }
}

async function applyRecommendation(rec) {
  recommendationId.value = rec?.id ?? null
  items.value = adaptRecommendation(rec)
  await syncShareStatus(recommendationId.value)
}

async function fetchRecommendation() {
  let rec = null
  try {
    const { data } = await fetchLatestRecommendation(tripId)
    rec = data
  } catch (e) {
    if (e.response && e.response.status !== 404) throw e
  }
  if (!rec) {
    const { data } = await createRecommendation(tripId, { advancedModel })
    rec = data
  }
  return rec
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    let trip = null
    try {
      const { data } = await fetchTrip(tripId)
      trip = data
      if (!label.value && trip.city_name && trip.country_name) {
        label.value = `${trip.country_name} · ${trip.city_name}`
      }
      startDate.value = trip.start_date || ''
    } catch {
      // 여행 메타 없어도 추천은 시도
    }

    const notesPromise = trip ? loadDestinationNotesForTrip(trip) : Promise.resolve()
    const [rec] = await Promise.all([fetchRecommendation(), notesPromise])

    await applyRecommendation(rec)
    if (!items.value.length) {
      errorMessage.value = '추천 결과가 비어 있어요. 다시 시도해주세요.'
    }
  } catch (e) {
    errorMessage.value = e.response?.data?.detail
      || '짐 추천을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}

async function regenerate() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await createRecommendation(tripId, { advancedModel })
    await applyRecommendation(data)
    if (!items.value.length) {
      errorMessage.value = '추천 결과가 비어 있어요. 다시 시도해주세요.'
    }
  } catch (e) {
    errorMessage.value = e.response?.data?.detail
      || '짐 추천을 다시 생성하지 못했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}

function retry() {
  load()
}

function openShareModal() {
  if (alreadyShared.value || sharing.value || !recommendationId.value) return
  shareMessage.value = ''
  shareModalOpen.value = true
}

function closeShareModal() {
  if (sharing.value) return
  shareModalOpen.value = false
}

async function submitShare({ title, body }) {
  if (!recommendationId.value || sharing.value || alreadyShared.value) return
  sharing.value = true
  shareMessage.value = ''
  try {
    await shareToCommunity({
      recommendationId: recommendationId.value,
      title,
      body,
    })
    alreadyShared.value = true
    shareModalOpen.value = false
    shareMessage.value = '커뮤니티에 공유했어요!'
    setTimeout(() => { shareMessage.value = '' }, 3000)
  } catch (e) {
    const detail = e.response?.data
    const recErr = detail?.recommendation_id?.[0]
    shareMessage.value = recErr || detail?.detail || '공유에 실패했습니다.'
    if (recErr && recErr.includes('이미')) {
      alreadyShared.value = true
      shareModalOpen.value = false
    }
  } finally {
    sharing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="result-page">
    <OpenSuitcase
      fullscreen
      :items="items"
      :title="title"
      :summary="summary"
      :loading="loading"
      :error-message="errorMessage"
      :trip-id="tripId"
      :start-date="startDate"
      :destination-notes="destinationNotes"
      :show-regenerate="!errorMessage && items.length > 0"
      :show-share="!errorMessage && items.length > 0"
      :share-disabled="alreadyShared"
      :sharing="sharing"
      @back="router.push({ name: 'trip' })"
      @regenerate="regenerate"
      @share="openShareModal"
    />

    <SharePostModal
      :open="shareModalOpen"
      :default-title="shareDefaultTitle"
      :submitting="sharing"
      @close="closeShareModal"
      @submit="submitShare"
    />

    <p v-if="shareMessage" class="share-toast">{{ shareMessage }}</p>
    <button v-if="!loading && errorMessage" class="retry" @click="retry">다시 시도</button>
  </div>
</template>

<style scoped>
.result-page {
  height: calc(100vh - 52px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.retry {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--ocean);
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 700;
  cursor: pointer;
  z-index: 20;
}
.share-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
  padding: 12px 20px;
  background: rgba(26, 83, 92, 0.92);
  color: #fff;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  z-index: 25;
  box-shadow: 0 8px 24px rgba(26, 83, 92, 0.25);
}
</style>
