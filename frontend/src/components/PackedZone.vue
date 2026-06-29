<script setup>
import { computed } from 'vue'
import PackingItem from './PackingItem.vue'

const props = defineProps({
  packed: { type: Object, required: true },
  compact: { type: Boolean, default: false },
  fill: { type: Boolean, default: false },
  emptyLabel: { type: String, default: '비어 있음' },
  animOffset: { type: Number, default: 0 },
  cellScale: { type: Number, default: 1 },
  trimRows: { type: Boolean, default: false },
  itemProgress: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['hover', 'leave', 'toggle-checked', 'item-drag-start', 'item-drag-end'])

const effectiveRows = computed(() => {
  if (!props.trimRows || !props.packed.placed.length) return props.packed.rows
  return Math.max(...props.packed.placed.map((p) => p.row + p.h), 1)
})

function sizeTier(w, h) {
  const area = w * h
  if (area <= 1) return 'xs'
  if (area <= 2) return 'sm'
  if (area <= 4) return 'md'
  return 'lg'
}

function requiredCount(item) {
  const match = String(item?.quantity || '').match(/(\d+)\s*(벌|켤레)/)
  return match ? Math.max(1, Number(match[1]) || 1) : 1
}

function progressCount(item) {
  return Math.min(props.itemProgress[item.key] || 0, requiredCount(item))
}

function isChecked(item) {
  return progressCount(item) >= requiredCount(item)
}
</script>

<template>
  <div
    class="pack-zone"
    :class="{ 'pack-zone--fill': fill }"
    :style="{
      '--cols': packed.cols,
      '--rows': effectiveRows,
      '--cell': `${packed.cellPx * cellScale}px`,
      '--gap': `${packed.gap * cellScale}px`,
    }"
  >
    <PackingItem
      v-for="(p, i) in packed.placed"
      :key="p.key"
      class="pack-zone__item"
      :item="p.item"
      :index="animOffset + i"
      :compact="compact"
      :size-tier="sizeTier(p.w, p.h)"
      fill-cell
      :checked="isChecked(p.item)"
      :packed-count="progressCount(p.item)"
      :required-count="requiredCount(p.item)"
      :style="{
        gridColumn: `${p.col + 1} / span ${p.w}`,
        gridRow: `${p.row + 1} / span ${p.h}`,
      }"
      @hover="emit('hover', $event)"
      @leave="emit('leave')"
      @toggle="emit('toggle-checked', p.item)"
      @drag-start="emit('item-drag-start', $event)"
      @drag-end="emit('item-drag-end', $event)"
    />
    <div v-if="!packed.placed.length" class="zone-empty">{{ emptyLabel }}</div>
  </div>
</template>

<style scoped>
.pack-zone {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  grid-template-rows: repeat(var(--rows), minmax(var(--cell), auto));
  gap: var(--gap);
  width: 100%;
  overflow: visible;
}

.pack-zone--fill {
  flex: 1;
  min-height: 0;
  height: 100%;
  grid-template-rows: repeat(var(--rows), minmax(var(--cell), 1fr));
  align-content: stretch;
}

.pack-zone__item {
  min-width: 0;
  min-height: 0;
  overflow: visible;
}

.zone-empty {
  grid-column: 1 / -1;
  grid-row: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 0.75rem;
  color: var(--muted);
  opacity: 0.5;
  font-style: italic;
}
</style>
