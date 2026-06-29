<script setup>
import { ref, watch, computed } from 'vue'
import { getIllustrationUrl } from '../data/itemIllustrations.js'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const PRESETS = [
  { label: '옷', iconId: 'mdi:tshirt-crew-outline', category: 'clothing' },
  { label: '물병', iconId: 'mdi:bottle-soda-classic-outline', category: 'other' },
  { label: '약', iconId: 'mdi:pill', category: 'health' },
  { label: '세면도구', iconId: 'mdi:hand-wash-outline', category: 'toiletries' },
  { label: '충전기', iconId: 'mdi:cellphone-link', category: 'electronics' },
  { label: '선크림', iconId: 'mdi:white-balance-sunny', category: 'toiletries' },
  { label: '우산', iconId: 'mdi:umbrella-outline', category: 'accessories' },
  { label: '신발', iconId: 'mdi:shoe-sneaker', category: 'accessories' },
  { label: '카메라', iconId: 'mdi:camera-outline', category: 'electronics' },
  { label: '책', iconId: 'mdi:book-outline', category: 'other' },
]

const name = ref('')
const selected = ref(0)
const error = ref('')

const canSubmit = computed(() => name.value.trim().length > 0)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      name.value = ''
      selected.value = 0
      error.value = ''
    }
  },
)

function iconUrl(preset) {
  return getIllustrationUrl(preset.label, preset.category, preset.iconId)
}

function close() {
  emit('close')
}

function submit() {
  error.value = ''
  const nextName = name.value.trim()
  if (!nextName) {
    error.value = '챙길 짐 이름을 알려줘.'
    return
  }
  const preset = PRESETS[selected.value]
  emit('submit', {
    name: nextName,
    iconId: preset.iconId,
    category: preset.category,
  })
}
</script>

<template>
  <Transition name="modal">
    <div v-if="open" class="modal-root">
      <div class="backdrop" @click="close" />
      <div class="panel" role="dialog" aria-labelledby="add-title">
        <header class="panel__head">
          <h2 id="add-title">내가 챙길 짐 추가</h2>
          <button type="button" class="close" aria-label="닫기" @click="close">✕</button>
        </header>

        <p class="desc">어떤 짐인지 골라주고 이름만 적어줘. 내가 캐리어에 넣어둘게.</p>

        <div class="field">
          <span class="label">아이콘</span>
          <div class="icon-grid">
            <button
              v-for="(p, i) in PRESETS"
              :key="p.iconId"
              type="button"
              class="icon-cell"
              :class="{ 'icon-cell--on': selected === i }"
              @click="selected = i"
            >
              <img :src="iconUrl(p)" :alt="p.label" class="icon-img" />
              <span class="icon-label">{{ p.label }}</span>
            </button>
          </div>
        </div>

        <label class="field">
          <span class="label">짐 이름</span>
          <input
            v-model="name"
            type="text"
            class="input"
            maxlength="12"
            placeholder="예) 여분 양말, 멀미약"
            @keyup.enter="submit"
          />
        </label>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="actions">
          <button type="button" class="btn btn--ghost" @click="close">취소</button>
          <button type="button" class="btn" :disabled="!canSubmit" @click="submit">
            챙겨 넣기
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-root {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.backdrop {
  position: absolute;
  inset: 0;
  background: rgba(20, 30, 35, 0.45);
}
.panel {
  position: relative;
  width: min(440px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  background: linear-gradient(180deg, #fdf8f3 0%, var(--sand) 100%);
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 16px 40px rgba(26, 83, 92, 0.2);
}
.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.panel__head h2 {
  margin: 0;
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ocean);
  font-size: 1.25rem;
}
.close {
  border: none;
  background: none;
  color: var(--muted);
  font-size: 1.1rem;
  cursor: pointer;
}
.desc {
  margin: 0 0 16px;
  font-size: 0.85rem;
  color: var(--muted);
}
.field {
  display: block;
  margin-bottom: 16px;
}
.label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ocean);
  margin-bottom: 8px;
}
.icon-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
.icon-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 4px 6px;
  border-radius: 12px;
  border: 1.5px solid rgba(26, 83, 92, 0.18);
  background: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  transition: all 0.12s;
}
.icon-cell--on {
  border-color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
}
.icon-img {
  width: 30px;
  height: 30px;
  object-fit: contain;
  opacity: 0.92;
}
.icon-label {
  font-size: 0.66rem;
  font-weight: 600;
  color: var(--ink);
}
.input {
  width: 100%;
  border: 1px solid rgba(26, 83, 92, 0.2);
  border-radius: 12px;
  padding: 11px 12px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.85);
}
.error {
  color: #c62828;
  font-size: 0.82rem;
  margin: 0 0 12px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
.btn {
  border: none;
  border-radius: 12px;
  background: var(--ocean);
  color: #fff;
  font-weight: 600;
  padding: 11px 18px;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn--ghost {
  background: transparent;
  color: var(--muted);
  border: 1px solid rgba(26, 83, 92, 0.15);
}
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .panel,
.modal-leave-active .panel {
  transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .panel,
.modal-leave-to .panel {
  transform: translateY(12px);
}
</style>
