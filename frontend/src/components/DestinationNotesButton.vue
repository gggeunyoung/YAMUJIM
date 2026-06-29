<script setup>
import { ref } from 'vue'
import DestinationNotesPanel from './DestinationNotesPanel.vue'

defineProps({
  notes: { type: Object, required: true },
})

const open = ref(false)
</script>

<template>
  <button class="notes-btn" type="button" @click="open = true">
    <span class="notes-btn__icon">💡</span>
    <span class="notes-btn__label">현지 꿀팁</span>
  </button>

  <Transition name="dn">
    <div v-if="open" class="dn-root">
      <div class="backdrop" @click="open = false" />
      <div class="panel">
        <header class="panel__head">
          <h2>참고사항</h2>
          <button class="close" type="button" aria-label="닫기" @click="open = false">✕</button>
        </header>
        <DestinationNotesPanel :notes="notes" />
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.notes-btn {
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
.notes-btn:hover { background: #fff; transform: translateY(-1px); }
.notes-btn__icon { font-size: 1rem; }

.dn-root {
  position: fixed;
  inset: 0;
  z-index: 110;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.backdrop { position: absolute; inset: 0; background: rgba(20, 30, 35, 0.5); }
.panel {
  position: relative;
  width: 100%;
  max-width: 480px;
  max-height: 84vh;
  overflow-y: auto;
  background: linear-gradient(180deg, #fdf8f3 0%, var(--sand) 100%);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  padding: 22px;
  box-sizing: border-box;
}
.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.panel__head h2 {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ocean);
  font-size: 1.25rem;
  margin: 0;
}
.close {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: var(--muted);
  cursor: pointer;
}

.dn-enter-active, .dn-leave-active { transition: opacity 0.2s ease; }
.dn-enter-active .panel, .dn-leave-active .panel { transition: transform 0.22s ease; }
.dn-enter-from, .dn-leave-to { opacity: 0; }
.dn-enter-from .panel, .dn-leave-to .panel { transform: scale(0.95); }
</style>
