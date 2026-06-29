<script setup>
// 전체 플로우는 라우터로 분기: 로그인 → 취향 테스트 → 여행 정보 → 추천 결과
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/AppHeader.vue'

const route = useRoute()
const auth = useAuthStore()

const showHeader = computed(
  () => auth.isAuthenticated && !route.meta.public && !route.meta.hideHeader,
)
</script>

<template>
  <AppHeader v-if="showHeader" />

  <RouterView v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>

<style>
/* 페이지 전환 효과 (데모 App.vue에서 가져옴) */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
