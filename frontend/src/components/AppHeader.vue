<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { name: 'trip', label: '여행', to: { name: 'trip' } },
  { name: 'community', label: '커뮤니티', to: { name: 'community' } },
  { name: 'mypage', label: '마이페이지', to: { name: 'mypage' } },
]

const activeTab = computed(() => {
  if (route.name === 'result') return 'trip'
  if (route.name === 'home') return null
  return route.name
})

function goHome() {
  if (route.name !== 'home') {
    router.push({ name: 'home' })
  }
}

function go(tab) {
  if (activeTab.value !== tab.name) {
    router.push(tab.to)
  }
}
</script>

<template>
  <header class="app-header">
    <button class="brand" type="button" @click="goHome">
      <span class="brand__emoji">🧳</span>
      <span class="brand__text">야무짐</span>
    </button>
    <nav class="tabs" aria-label="메인 메뉴">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        type="button"
        class="tab"
        :class="{ 'tab--active': activeTab === tab.name }"
        @click="go(tab)"
      >
        {{ tab.label }}
      </button>
    </nav>
  </header>
  <div class="app-header__spacer" aria-hidden="true" />
</template>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(253, 248, 243, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(26, 83, 92, 0.1);
  box-shadow: 0 4px 18px rgba(26, 83, 92, 0.06);
}
.app-header__spacer {
  height: 52px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: none;
  padding: 0;
  cursor: pointer;
}
.brand__emoji { font-size: 1.2rem; }
.brand__text {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ocean);
}
.tabs {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.65);
  padding: 4px;
  border-radius: 999px;
  border: 1px solid rgba(26, 83, 92, 0.1);
}
.tab {
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 7px 12px;
  border-radius: 999px;
  white-space: nowrap;
}
.tab--active {
  background: var(--ocean);
  color: #fff;
  box-shadow: 0 2px 8px rgba(26, 83, 92, 0.25);
}
@media (max-width: 420px) {
  .tab { padding: 7px 9px; font-size: 0.72rem; }
}
</style>
