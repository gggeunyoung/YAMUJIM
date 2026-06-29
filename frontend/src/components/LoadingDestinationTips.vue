<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  notes: { type: Object, default: null },
})

const index = ref(0)
let timer = null

const slides = computed(() => {
  if (!props.notes) return []
  const items = []
  if (props.notes.emergencyContact) {
    items.push({
      kind: 'emergency',
      title: '긴급 연락처',
      icon: '🆘',
      body: props.notes.emergencyContact,
    })
  }
  for (const tip of props.notes.culturalTips || []) {
    items.push({
      kind: 'culture',
      title: tip.theme,
      icon: '🌏',
      body: tip.content,
    })
  }
  return items
})

const current = computed(() => slides.value[index.value] || null)

function startRotation() {
  clearInterval(timer)
  if (slides.value.length <= 1) return
  timer = setInterval(() => {
    index.value = (index.value + 1) % slides.value.length
  }, 7000)
}

watch(slides, () => {
  index.value = 0
  startRotation()
})

onMounted(startRotation)
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div v-if="current" class="loading-tips">
    <p class="loading-tips__label">짐 싸는 동안 참고해 보세요</p>
    <article class="loading-tips__card">
      <div class="loading-tips__head">
        <span class="loading-tips__icon">{{ current.icon }}</span>
        <strong>{{ current.title }}</strong>
      </div>
      <p class="loading-tips__body">{{ current.body }}</p>
      <div v-if="slides.length > 1" class="loading-tips__dots">
        <span
          v-for="(_, i) in slides"
          :key="i"
          class="dot"
          :class="{ 'dot--active': i === index }"
        />
      </div>
    </article>
  </div>
</template>

<style scoped>
.loading-tips {
  width: min(440px, 92vw);
  margin-top: 20px;
}

.loading-tips__label {
  margin: 0 0 10px;
  text-align: center;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ocean);
}

.loading-tips__card {
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(26, 83, 92, 0.12);
  box-shadow: 0 8px 24px rgba(26, 83, 92, 0.1);
  animation: fadeSwap 0.45s ease;
}

.loading-tips__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--ocean);
  font-size: 0.88rem;
}

.loading-tips__icon { font-size: 1.1rem; }

.loading-tips__body {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.65;
  color: var(--ink);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
  overflow: hidden;
}

.loading-tips__dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(26, 83, 92, 0.2);
}

.dot--active {
  background: var(--ocean);
  transform: scale(1.15);
}

@keyframes fadeSwap {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
