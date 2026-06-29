<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  defaultTitle: { type: String, default: '' },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const title = ref('')
const body = ref('')
const error = ref('')

const canSubmit = computed(
  () => title.value.trim() && body.value.trim() && !props.submitting,
)

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    title.value = props.defaultTitle
    body.value = ''
    error.value = ''
  }
})

function close() {
  if (props.submitting) return
  emit('close')
}

function submit() {
  error.value = ''
  const nextTitle = title.value.trim()
  const nextBody = body.value.trim()
  if (!nextTitle) {
    error.value = '제목을 입력해주세요.'
    return
  }
  if (!nextBody) {
    error.value = '내용을 입력해주세요.'
    return
  }
  emit('submit', { title: nextTitle, body: nextBody })
}
</script>

<template>
  <Transition name="modal">
    <div v-if="open" class="modal-root">
      <div class="backdrop" @click="close" />
      <div class="panel" role="dialog" aria-labelledby="share-title">
        <header class="panel__head">
          <h2 id="share-title">커뮤니티에 공유</h2>
          <button type="button" class="close" aria-label="닫기" @click="close">✕</button>
        </header>

        <p class="desc">제목과 내용을 작성하면 짐 리스트와 함께 게시됩니다.</p>

        <label class="field">
          <span class="label">제목</span>
          <input
            v-model="title"
            type="text"
            class="input"
            maxlength="80"
            placeholder="예) 도쿄 3박4일 짐 리스트 공유해요"
          />
        </label>

        <label class="field">
          <span class="label">내용</span>
          <textarea
            v-model="body"
            class="textarea"
            maxlength="2000"
            rows="5"
            placeholder="여행 팁이나 짐 리스트에 대한 이야기를 적어주세요"
          />
        </label>

        <p v-if="error" class="error">{{ error }}</p>

        <div class="actions">
          <button type="button" class="btn btn--ghost" :disabled="submitting" @click="close">
            취소
          </button>
          <button type="button" class="btn" :disabled="!canSubmit" @click="submit">
            {{ submitting ? '공유 중...' : '공유하기' }}
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
.field { display: block; margin-bottom: 14px; }
.label {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ocean);
  margin-bottom: 6px;
}
.input,
.textarea {
  width: 100%;
  border: 1px solid rgba(26, 83, 92, 0.2);
  border-radius: 12px;
  padding: 11px 12px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.85);
  resize: vertical;
}
.textarea { min-height: 120px; }
.error { color: #c62828; font-size: 0.82rem; margin: 0 0 12px; }
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
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn--ghost {
  background: transparent;
  color: var(--muted);
  border: 1px solid rgba(26, 83, 92, 0.15);
}
.modal-enter-active,
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-active .panel,
.modal-leave-active .panel { transition: transform 0.2s ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-from .panel,
.modal-leave-to .panel { transform: translateY(12px); }
</style>
