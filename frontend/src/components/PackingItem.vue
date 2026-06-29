<script setup>
import { computed, ref, watch } from 'vue'
import { CATEGORY_ICONS, CATEGORY_STYLES, getIconId, getIllustrationUrl, getItemImageUrl } from '../data/itemIllustrations.js'

const props = defineProps({
  item: { type: Object, required: true },
  index: { type: Number, default: 0 },
  compact: { type: Boolean, default: false },
  fillCell: { type: Boolean, default: false },
  checked: { type: Boolean, default: false },
  packedCount: { type: Number, default: 0 },
  requiredCount: { type: Number, default: 1 },
  sizeTier: { type: String, default: 'md' },
})

const emit = defineEmits(['hover', 'leave', 'toggle', 'drag-start', 'drag-end'])

const style = CATEGORY_STYLES[props.item.category] || CATEGORY_STYLES.other
const activeIconId = ref(props.item.iconId || getIconId(props.item.name, props.item.category))
const useCategoryFallback = ref(false)

const imgUrl = computed(() => {
  if (!useCategoryFallback.value) {
    const itemImage = getItemImageUrl(props.item.name)
    if (itemImage) return itemImage
  }
  return getIllustrationUrl(
    props.item.name,
    props.item.category,
    useCategoryFallback.value
      ? (CATEGORY_ICONS[props.item.category] || CATEGORY_ICONS.other)
      : activeIconId.value,
  )
})

watch(
  () => [props.item.name, props.item.category],
  () => {
    activeIconId.value = props.item.iconId || getIconId(props.item.name, props.item.category)
    useCategoryFallback.value = false
  },
)

const tier = computed(() => {
  if (props.compact) return 'xs'
  return props.sizeTier
})

const isRowLayout = computed(() => tier.value === 'xs' || tier.value === 'sm')
const priorityClass = computed(() =>
  ['required', 'recommended', 'optional'].includes(props.item.priority)
    ? `packing-item--priority-${props.item.priority}`
    : '',
)
const quantityLabel = computed(() => {
  if (props.requiredCount > 1 && props.packedCount > 0 && !props.checked) {
    return `${props.packedCount}/${props.requiredCount} · ${props.item.quantity}`
  }
  return props.item.quantity
})

const entered = ref(false)

function onAnimEnd(e) {
  if (e.animationName === 'dropIn') entered.value = true
}

function onImgError() {
  if (!useCategoryFallback.value) {
    useCategoryFallback.value = true
    return
  }
  activeIconId.value = CATEGORY_ICONS.other
}

function onEnter(e) {
  emit('hover', { item: props.item, x: e.clientX, y: e.clientY })
}
function onMove(e) {
  emit('hover', { item: props.item, x: e.clientX, y: e.clientY })
}
function onClick() {
  entered.value = true
  emit('toggle', props.item.key)
}
function onDragStart(e) {
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', props.item.key)
  }
  emit('leave')
  emit('drag-start', props.item.key)
}
function onDragEnd() {
  emit('drag-end', props.item.key)
}
</script>

<template>
  <div
    class="packing-item"
    :class="[
      `packing-item--${tier}`,
      priorityClass,
      {
        'packing-item--fill': fillCell,
        'packing-item--checked': checked,
        'packing-item--entered': entered,
        'packing-item--row': isRowLayout,
      },
    ]"
    :style="{
      '--delay': `${index * 0.06}s`,
      '--bg': style.bg,
      '--border': style.border,
    }"
    role="button"
    :aria-pressed="checked"
    :aria-label="`${item.name}${checked ? ', 챙김' : packedCount ? `, ${packedCount}/${requiredCount} 챙김` : ''}`"
    draggable="true"
    tabindex="0"
    @click="onClick"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @animationend="onAnimEnd"
    @mouseenter="onEnter"
    @mousemove="onMove"
    @mouseleave="emit('leave')"
  >
    <span class="packing-item__check" aria-hidden="true">✓</span>

    <div class="item-visual">
      <img
        class="item-img"
        :src="imgUrl"
        :alt="item.name"
        loading="lazy"
        @error="onImgError"
      />
    </div>

    <div class="item-text">
      <p class="item-name">{{ item.name }}</p>
      <span class="item-qty">{{ quantityLabel }}</span>
    </div>
  </div>
</template>

<style scoped>
.packing-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 6px;
  border-radius: 10px;
  background: var(--bg);
  border: 2px solid var(--border);
  box-shadow:
    0 2px 6px rgba(60, 40, 20, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  cursor: pointer;
  overflow: hidden;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.packing-item:not(.packing-item--entered) {
  animation: dropIn 0.45s cubic-bezier(0.34, 1.45, 0.64, 1) both;
  animation-delay: var(--delay);
}

.packing-item--entered {
  animation: none;
}

.packing-item--fill {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.packing-item--checked {
  opacity: 0.35;
}

.packing-item--priority-required {
  box-shadow:
    0 2px 6px rgba(60, 40, 20, 0.1),
    inset 0 0 0 2px rgba(199, 155, 38, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.packing-item--priority-recommended {
  box-shadow:
    0 2px 6px rgba(60, 40, 20, 0.1),
    inset 0 0 0 1px rgba(26, 83, 92, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.packing-item--priority-optional {
  border-style: dashed;
}

.packing-item__check {
  position: absolute;
  top: 5px;
  right: 6px;
  z-index: 2;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1;
  color: var(--ocean, #1a535c);
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.2s ease, transform 0.2s ease;
  pointer-events: none;
  user-select: none;
}

.packing-item--checked .packing-item__check {
  opacity: 1;
  transform: scale(1);
}

.packing-item--row {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 6px;
}

.packing-item--row .item-visual {
  flex: 1 1 auto;
  width: 100%;
  height: 100%;
  max-height: none;
}

.packing-item--row.packing-item--xs .item-visual {
  width: 100%;
  height: 100%;
}

.packing-item--row .item-img {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
}

.packing-item--row .item-text {
  align-items: center;
}

.packing-item:hover:not(.packing-item--checked) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 16px rgba(60, 40, 20, 0.14);
  z-index: 5;
}

.packing-item--checked:hover {
  transform: none;
}

.item-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1 1 auto;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.item-img {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  flex-shrink: 0;
  opacity: 0.92;
}

.packing-item--md .item-visual {
  max-height: none;
}

.packing-item--lg .item-visual {
  max-height: none;
}

.packing-item--fill.packing-item--md .item-visual { max-height: none; }
.packing-item--fill.packing-item--lg .item-visual { max-height: none; }

.item-text {
  position: absolute;
  left: 6px;
  right: 6px;
  bottom: 6px;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 6px 6px 5px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(20, 20, 20, 0.12);
  opacity: 0;
  transform: translateY(5px);
  transition: opacity 0.16s ease, transform 0.16s ease;
  pointer-events: none;
}

.packing-item:hover .item-text,
.packing-item:focus-visible .item-text {
  opacity: 1;
  transform: translateY(0);
}

.item-name {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: #1a1a1a;
  text-align: center;
  line-height: 1.35;
  word-break: keep-all;
  overflow-wrap: anywhere;
  width: 100%;
  flex-shrink: 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.packing-item--row .item-name {
  font-size: 0.7rem;
}

.packing-item--row.packing-item--xs .item-name {
  font-size: 0.64rem;
}

.packing-item--lg .item-name {
  font-size: 0.85rem;
}

.item-qty {
  font-size: 0.62rem;
  font-weight: 600;
  color: #555;
  background: rgba(255, 255, 255, 0.85);
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.packing-item--row .item-qty {
  font-size: 0.58rem;
  padding: 1px 7px;
}

@keyframes dropIn {
  from {
    opacity: 0;
    transform: translateY(-16px) scale(0.75);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
