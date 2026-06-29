<script setup>
defineProps({
  notes: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <div class="notes-panel" :class="{ 'notes-panel--compact': compact }">
    <p v-if="!compact" class="notes-panel__lead">
      {{ notes.cityName }}·{{ notes.countryName }} 여행 전에 알아두면 좋은 현지 정보예요.
    </p>

    <section v-if="notes.emergencyContact" class="block block--emergency">
      <h3>🆘 긴급 연락처</h3>
      <p class="emergency">{{ notes.emergencyContact }}</p>
    </section>

    <section v-if="notes.culturalTips?.length" class="block">
      <h3>🌏 현지 문화 꿀팁</h3>
      <ul class="tips">
        <li v-for="(tip, i) in notes.culturalTips" :key="i" class="tip-card">
          <span class="tip-card__theme">{{ tip.theme }}</span>
          <p class="tip-card__content">{{ tip.content }}</p>
        </li>
      </ul>
    </section>

    <p
      v-if="!notes.emergencyContact && !notes.culturalTips?.length"
      class="empty"
    >
      이 목적지에 등록된 참고 정보가 아직 없어요.
    </p>
  </div>
</template>

<style scoped>
.notes-panel__lead {
  margin: 0 0 16px;
  font-size: 0.88rem;
  line-height: 1.55;
  color: var(--ink);
}

.block { margin-bottom: 18px; }
.block:last-child { margin-bottom: 0; }
.block h3 {
  font-size: 0.9rem;
  color: var(--ocean);
  margin: 0 0 10px;
}

.block--emergency .emergency {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff5f5;
  border: 1px solid #f0c0c0;
  font-size: 0.82rem;
  line-height: 1.65;
  color: #5c2020;
  word-break: keep-all;
}

.tips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tip-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(26, 83, 92, 0.1);
}

.tip-card__theme {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  padding: 3px 8px;
  border-radius: 8px;
  margin-bottom: 6px;
}

.tip-card__content {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.6;
  color: var(--ink);
}

.notes-panel--compact .tip-card {
  padding: 10px 12px;
}

.empty {
  margin: 0;
  text-align: center;
  color: var(--muted);
  font-size: 0.85rem;
}
</style>
