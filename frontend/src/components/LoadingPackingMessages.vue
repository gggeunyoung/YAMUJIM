<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const MESSAGES = [
  { emoji: '✈️', text: '어디 가는지 살펴보는 중...' },
  { emoji: '🧳', text: '빠진 거 없나 챙기는 중...' },
  { emoji: '🔍', text: '깜빡한 거 없나 다시 보는 중...' },
  { emoji: '🌤️', text: '날씨까지 생각해서 챙기는 중...' },
  { emoji: '✨', text: '자기 거 야무지게 챙기는 중...' },
]

const index = ref(0)
let timer = null

const current = computed(() => MESSAGES[index.value])

onMounted(() => {
  timer = setInterval(() => {
    index.value = (index.value + 1) % MESSAGES.length
  }, 2800)
})

onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="packing-loading">
    <Transition name="msg" mode="out-in">
      <div :key="index" class="packing-loading__slide">
        <div class="packing-loading__emoji">{{ current.emoji }}</div>
        <p class="packing-loading__text">{{ current.text }}</p>
      </div>
    </Transition>
    <div class="packing-loading__dots">
      <span
        v-for="(_, i) in MESSAGES"
        :key="i"
        class="dot"
        :class="{ 'dot--active': i === index }"
      />
    </div>
  </div>
</template>

<style scoped>
.packing-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 88px;
}
.packing-loading__slide {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.packing-loading__emoji {
  font-size: 2.4rem;
  line-height: 1;
  margin-bottom: 10px;
}
.packing-loading__text {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--ocean);
}
.packing-loading__dots {
  display: flex;
  gap: 6px;
  margin-top: 14px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(26, 83, 92, 0.2);
  transition: background 0.2s, transform 0.2s;
}
.dot--active {
  background: var(--ocean);
  transform: scale(1.2);
}
.msg-enter-active,
.msg-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.msg-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
