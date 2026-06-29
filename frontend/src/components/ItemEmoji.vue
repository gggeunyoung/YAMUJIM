<script setup>
import { computed } from 'vue'
import twemoji from 'twemoji'

const props = defineProps({
  emoji: { type: String, default: '📦' },
  size: { type: Number, default: 36 },
})

const TWEMOJI_BASE = 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/'

const iconSrc = computed(() => {
  const parsed = twemoji.parse(props.emoji || '📦', {
    folder: 'svg',
    ext: '.svg',
    base: TWEMOJI_BASE,
  })
  const match = parsed.match(/src="([^"]+)"/)
  return match?.[1] ?? null
})
</script>

<template>
  <img
    v-if="iconSrc"
    class="item-icon"
    :src="iconSrc"
    :alt="emoji"
    :width="size"
    :height="size"
    draggable="false"
    loading="lazy"
  />
  <span v-else class="item-icon-fallback">{{ emoji }}</span>
</template>

<style scoped>
.item-icon {
  display: block;
  flex-shrink: 0;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}

.item-icon-fallback {
  font-size: 1.5rem;
  line-height: 1;
}
</style>
