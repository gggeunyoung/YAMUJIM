<script setup>
const emit = defineEmits(['submit'])

const form = defineModel({
  default: () => ({
    destination: '',
    days: 3,
    season: '여름',
    trip_type: '관광',
  }),
})

const seasons = ['봄', '여름', '가을', '겨울']
const tripTypes = ['관광', '비즈니스', '백패킹', '해변', '스키', '캠핑']

function handleSubmit() {
  if (!form.value.destination.trim()) return
  emit('submit', { ...form.value })
}
</script>

<template>
  <form class="trip-form" @submit.prevent="handleSubmit">
    <div class="form-row">
      <label class="field field--main">
        <span class="field-label">✈️ 어디로 떠나시나요?</span>
        <input
          v-model="form.destination"
          type="text"
          placeholder="예: 제주도, 도쿄, 파리..."
          required
        />
      </label>
    </div>

    <div class="form-row form-row--grid">
      <label class="field">
        <span class="field-label">📅 며칠?</span>
        <div class="days-control">
          <button type="button" class="days-btn" @click="form.days = Math.max(1, form.days - 1)">−</button>
          <span class="days-value">{{ form.days }}일</span>
          <button type="button" class="days-btn" @click="form.days = Math.min(30, form.days + 1)">+</button>
        </div>
      </label>

      <label class="field">
        <span class="field-label">🌤️ 계절</span>
        <div class="chip-group">
          <button
            v-for="s in seasons"
            :key="s"
            type="button"
            class="chip"
            :class="{ 'chip--active': form.season === s }"
            @click="form.season = s"
          >
            {{ s }}
          </button>
        </div>
      </label>

      <label class="field">
        <span class="field-label">🎒 여행 스타일</span>
        <select v-model="form.trip_type">
          <option v-for="t in tripTypes" :key="t" :value="t">{{ t }}</option>
        </select>
      </label>
    </div>

    <button type="submit" class="submit-btn" :disabled="!form.destination.trim()">
      <span class="submit-icon">🧳</span>
      짐 싸기 시작!
    </button>
  </form>
</template>

<style scoped>
.trip-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row--grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ocean);
}

.field input,
.field select {
  padding: 12px 16px;
  border: 2px solid var(--sand-dark);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  color: var(--ink);
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}

.field input:focus,
.field select:focus {
  border-color: var(--ocean);
  box-shadow: 0 0 0 3px rgba(26, 83, 92, 0.15);
}

.field--main input {
  font-size: 1.15rem;
  padding: 14px 18px;
}

.days-control {
  display: flex;
  align-items: center;
  gap: 0;
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid var(--sand-dark);
  border-radius: 12px;
  overflow: hidden;
}

.days-btn {
  width: 40px;
  height: 44px;
  border: none;
  background: transparent;
  font-size: 1.2rem;
  color: var(--ocean);
  transition: background 0.15s;
}

.days-btn:hover {
  background: var(--sand);
}

.days-value {
  flex: 1;
  text-align: center;
  font-weight: 700;
  font-size: 1rem;
}

.chip-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  padding: 8px 14px;
  border: 2px solid var(--sand-dark);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
  transition: all 0.2s;
}

.chip:hover {
  border-color: var(--ocean-light);
}

.chip--active {
  background: var(--ocean);
  border-color: var(--ocean);
  color: white;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--coral) 0%, var(--coral-soft) 100%);
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow:
    0 8px 24px rgba(255, 107, 107, 0.35),
    0 2px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 12px 32px rgba(255, 107, 107, 0.45),
    0 4px 8px rgba(0, 0, 0, 0.12);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-icon {
  font-size: 1.3rem;
}

@media (max-width: 700px) {
  .form-row--grid {
    grid-template-columns: 1fr;
  }
}
</style>
