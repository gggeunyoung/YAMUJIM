<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getIllustrationUrl } from '../data/itemIllustrations.js'

const props = defineProps({
  item: { type: Object, required: true },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  visible: { type: Boolean, default: false },
})

const tipRef = ref(null)
const placement = ref('top')
const position = ref({ x: props.x, y: props.y })

const tipStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`,
  '--tip-transform': placement.value === 'bottom'
    ? 'translate(-50%, 0)'
    : 'translate(-50%, -100%)',
  '--tip-enter-transform': placement.value === 'bottom'
    ? 'translate(-50%, -8px) scale(0.95)'
    : 'translate(-50%, calc(-100% - 8px)) scale(0.95)',
}))

function updatePosition() {
  if (!props.visible) return

  const margin = 12
  const gap = 16
  const width = tipRef.value?.offsetWidth || 280
  const height = tipRef.value?.offsetHeight || 180
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const clampedX = Math.min(
    Math.max(props.x, margin + width / 2),
    viewportWidth - margin - width / 2,
  )
  const hasTopSpace = props.y - height - gap >= margin
  const hasBottomSpace = props.y + height + gap <= viewportHeight - margin

  if (!hasTopSpace && hasBottomSpace) {
    placement.value = 'bottom'
    position.value = { x: clampedX, y: props.y + gap }
    return
  }

  placement.value = 'top'
  position.value = { x: clampedX, y: Math.max(props.y - gap, margin + height) }
}

watch(
  () => [props.visible, props.x, props.y, props.item],
  async () => {
    await nextTick()
    updatePosition()
  },
  { immediate: true },
)

onMounted(() => window.addEventListener('resize', updatePosition))
onBeforeUnmount(() => window.removeEventListener('resize', updatePosition))
</script>

<template>
  <Transition name="tip">
    <div
      v-if="visible && item"
      ref="tipRef"
      class="tip-card"
      :class="`tip-card--${placement}`"
      :style="tipStyle"
    >
      <div class="tip-card__header">
        <img
          class="tip-card__img"
          :src="getIllustrationUrl(item.name, item.category)"
          :alt="item.name"
        />
        <div>
          <strong class="tip-card__name">{{ item.name }}</strong>
          <span class="tip-card__qty">{{ item.quantity }}</span>
        </div>
      </div>
      <p class="tip-card__text">{{ item.tip || '여행에 꼭 필요한 준비물이에요.' }}</p>
      <div class="tip-card__arrow" />
    </div>
  </Transition>
</template>

<style scoped>
.tip-card {
  position: fixed;
  z-index: 9999;
  width: min(280px, calc(100vw - 32px));
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid rgba(26, 83, 92, 0.15);
  border-radius: 14px;
  box-shadow:
    0 12px 40px rgba(26, 83, 92, 0.18),
    0 2px 8px rgba(0, 0, 0, 0.06);
  pointer-events: none;
  transform: var(--tip-transform);
  backdrop-filter: blur(8px);
}

.tip-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.tip-card__img {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #f5f0eb;
  padding: 6px;
  object-fit: contain;
}

.tip-card__name {
  display: block;
  font-size: 0.85rem;
  color: var(--ocean);
  line-height: 1.3;
}

.tip-card__qty {
  font-size: 0.7rem;
  color: var(--muted);
}

.tip-card__text {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.55;
  color: var(--ink);
}

.tip-card__arrow {
  position: absolute;
  left: 50%;
  width: 14px;
  height: 14px;
  background: white;
  transform: translateX(-50%) rotate(45deg);
}

.tip-card--top .tip-card__arrow {
  bottom: -7px;
  border-right: 1px solid rgba(26, 83, 92, 0.12);
  border-bottom: 1px solid rgba(26, 83, 92, 0.12);
}

.tip-card--bottom .tip-card__arrow {
  top: -7px;
  border-left: 1px solid rgba(26, 83, 92, 0.12);
  border-top: 1px solid rgba(26, 83, 92, 0.12);
}

.tip-enter-active,
.tip-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.tip-enter-from,
.tip-leave-to {
  opacity: 0;
  transform: var(--tip-enter-transform);
}
</style>
