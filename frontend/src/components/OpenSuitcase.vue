<script setup>
import { computed, ref, watch } from 'vue'
import PackedZone from './PackedZone.vue'
import TipCard from './TipCard.vue'
import WeatherSummaryButton from './WeatherSummaryButton.vue'
import DestinationNotesButton from './DestinationNotesButton.vue'
import LoadingDestinationTips from './LoadingDestinationTips.vue'
import LoadingPackingMessages from './LoadingPackingMessages.vue'
import AddItemModal from './AddItemModal.vue'
import { packZone } from '../packing/index.js'
import { formatDday } from '../utils/dday.js'

const props = defineProps({
  items: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  summary: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
  fullscreen: { type: Boolean, default: false },
  tripId: { type: [String, Number], default: null },
  startDate: { type: String, default: '' },
  showRegenerate: { type: Boolean, default: false },
  showShare: { type: Boolean, default: false },
  shareDisabled: { type: Boolean, default: false },
  sharing: { type: Boolean, default: false },
  destinationNotes: { type: Object, default: null },
})

const emit = defineEmits(['back', 'regenerate', 'share'])

const ZONE_ALIASES = { lid: 'left_pocket', center: 'left', pouch: 'right_pocket' }

const hoveredItem = ref(null)
const tipPos = ref({ x: 0, y: 0 })
const itemProgress = ref({})
const customItems = ref([])
const removedKeys = ref(new Set())
const addModalOpen = ref(false)
const pendingRemoveKey = ref(null)
const draggingKey = ref(null)
let droppedInside = false

const ddayLabel = computed(() => formatDday(props.startDate))
const cellScale = computed(() => (props.fullscreen ? 0.48 : 1))
const trimZoneRows = computed(() => props.fullscreen)

const storageKey = computed(() =>
  props.tripId ? `yamujim-packed-${props.tripId}` : null,
)
const customStorageKey = computed(() =>
  props.tripId ? `yamujim-custom-${props.tripId}` : null,
)
const removedStorageKey = computed(() =>
  props.tripId ? `yamujim-removed-${props.tripId}` : null,
)

function loadCheckedState() {
  if (!storageKey.value) {
    itemProgress.value = {}
    return
  }
  try {
    const raw = localStorage.getItem(storageKey.value)
    const parsed = raw ? JSON.parse(raw) : null
    if (Array.isArray(parsed)) {
      itemProgress.value = Object.fromEntries(parsed.map((key) => [key, 1]))
    } else if (parsed && typeof parsed === 'object') {
      itemProgress.value = Object.fromEntries(
        Object.entries(parsed)
          .map(([key, value]) => [key, Math.max(0, Number(value) || 0)])
          .filter(([, value]) => value > 0),
      )
    } else {
      itemProgress.value = {}
    }
  } catch {
    itemProgress.value = {}
  }
}

function saveCheckedState() {
  if (!storageKey.value) return
  localStorage.setItem(storageKey.value, JSON.stringify(itemProgress.value))
}

watch(storageKey, loadCheckedState, { immediate: true })
watch(itemProgress, saveCheckedState, { deep: true })

function loadCustomItems() {
  if (!customStorageKey.value) {
    customItems.value = []
    return
  }
  try {
    const raw = localStorage.getItem(customStorageKey.value)
    customItems.value = raw ? JSON.parse(raw) : []
  } catch {
    customItems.value = []
  }
}

function saveCustomItems() {
  if (!customStorageKey.value) return
  localStorage.setItem(customStorageKey.value, JSON.stringify(customItems.value))
}

function loadRemovedKeys() {
  if (!removedStorageKey.value) {
    removedKeys.value = new Set()
    return
  }
  try {
    const raw = localStorage.getItem(removedStorageKey.value)
    removedKeys.value = raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    removedKeys.value = new Set()
  }
}

function saveRemovedKeys() {
  if (!removedStorageKey.value) return
  localStorage.setItem(removedStorageKey.value, JSON.stringify([...removedKeys.value]))
}

watch(customStorageKey, loadCustomItems, { immediate: true })
watch(customItems, saveCustomItems, { deep: true })
watch(removedStorageKey, loadRemovedKeys, { immediate: true })
watch(removedKeys, saveRemovedKeys, { deep: true })

function requiredCount(item) {
  const match = String(item?.quantity || '').match(/(\d+)\s*(벌|켤레)/)
  return match ? Math.max(1, Number(match[1]) || 1) : 1
}

function progressCount(item) {
  return Math.min(itemProgress.value[item.key] || 0, requiredCount(item))
}

function toggleChecked(item) {
  const required = requiredCount(item)
  const current = progressCount(item)
  const next = { ...itemProgress.value }

  if (current >= required) {
    delete next[item.key]
  } else {
    next[item.key] = current + 1
  }

  itemProgress.value = next
}

const displayItems = computed(() => [
  ...props.items.filter((it) => !removedKeys.value.has(it.key)),
  ...customItems.value,
])

const normalizedItems = computed(() =>
  displayItems.value.map((item) => ({
    ...item,
    zone: ZONE_ALIASES[item.zone] || item.zone,
  })),
)

const zones = computed(() => ({
  left: normalizedItems.value.filter((i) => i.zone === 'left'),
  right: normalizedItems.value.filter((i) => i.zone === 'right'),
  left_pocket: normalizedItems.value.filter((i) => i.zone === 'left_pocket'),
  right_pocket: normalizedItems.value.filter((i) => i.zone === 'right_pocket'),
}))

const packedZones = computed(() => ({
  left: packZone(zones.value.left, 'left'),
  right: packZone(zones.value.right, 'right'),
  left_pocket: packZone(zones.value.left_pocket, 'left_pocket'),
  right_pocket: packZone(zones.value.right_pocket, 'right_pocket'),
}))

const totalItems = computed(() =>
  displayItems.value.reduce((sum, item) => sum + requiredCount(item), 0),
)
const checkedCount = computed(() =>
  displayItems.value.reduce((sum, item) => sum + progressCount(item), 0),
)
const packedPercent = computed(() => {
  if (!totalItems.value) return 0
  return Math.round((checkedCount.value / totalItems.value) * 100)
})

function onItemHover({ item, x, y }) {
  hoveredItem.value = item
  tipPos.value = { x, y }
}

function openAddModal() {
  addModalOpen.value = true
}

function onAddItem({ name, iconId, category }) {
  const zone = customItems.value.length % 2 === 0 ? 'left' : 'right'
  customItems.value = [
    ...customItems.value,
    {
      key: `custom-${Date.now()}`,
      name,
      category: category || 'other',
      tip: '내가 직접 챙긴 짐이야 🙂',
      quantity: '직접 추가',
      iconId,
      zone,
      custom: true,
    },
  ]
  addModalOpen.value = false
}

function onItemDragStart(key) {
  draggingKey.value = key
  droppedInside = false
  hoveredItem.value = null
}

function onCarrierDrop() {
  droppedInside = true
}

function onItemDragEnd() {
  const key = draggingKey.value
  draggingKey.value = null
  if (key && !droppedInside) {
    pendingRemoveKey.value = key
  }
  droppedInside = false
}

const pendingRemoveItem = computed(
  () => displayItems.value.find((it) => it.key === pendingRemoveKey.value) || null,
)

function confirmRemove() {
  const key = pendingRemoveKey.value
  if (!key) return
  if (String(key).startsWith('custom-')) {
    customItems.value = customItems.value.filter((it) => it.key !== key)
  } else {
    const next = new Set(removedKeys.value)
    next.add(key)
    removedKeys.value = next
  }
  if (itemProgress.value[key]) {
    const nextProgress = { ...itemProgress.value }
    delete nextProgress[key]
    itemProgress.value = nextProgress
  }
  pendingRemoveKey.value = null
}

function cancelRemove() {
  pendingRemoveKey.value = null
}
</script>

<template>
  <div class="suitcase-scene" :class="{ 'suitcase-scene--fullscreen': fullscreen }">
    <div v-if="loading" class="state">
      <button v-if="fullscreen" type="button" class="back-btn" @click="emit('back')">← 돌아가기</button>
      <LoadingPackingMessages />
      <p class="state__sub">꼼꼼히 챙기느라 1~2분 걸려, 조금만 기다려</p>
      <LoadingDestinationTips :notes="destinationNotes" />
    </div>

    <div v-else-if="errorMessage || !items.length" class="state">
      <button v-if="fullscreen" type="button" class="back-btn" @click="emit('back')">← 돌아가기</button>
      <div class="state__icon">😅</div>
      <p class="state__text">앗, 이건 내가 깜빡했다</p>
      <p v-if="errorMessage" class="state__sub state__sub--error">{{ errorMessage }}</p>
      <p v-else class="state__sub">다시 시도하거나 입력 화면으로 돌아가 줄래?</p>
    </div>

    <div v-else class="wrap">
      <header class="header">
        <button v-if="fullscreen" type="button" class="back-btn back-btn--inline" @click="emit('back')">
          ← 돌아가기
        </button>
        <div class="header__main">
          <div class="header__top">
            <div class="header__identity">
              <span class="badge badge--open">🧳 OPEN</span>
              <h2 class="title">{{ title }}</h2>
            </div>
            <div class="header__commands">
              <span v-if="ddayLabel" class="badge badge--dday">{{ ddayLabel }}</span>
              <button
                v-if="showRegenerate"
                type="button"
                class="badge add-btn"
                @click="openAddModal"
              >
                + 짐 추가
              </button>
              <button
                v-if="showRegenerate"
                type="button"
                class="badge regenerate-btn"
                @click="emit('regenerate')"
              >
                짐 다시 쌀까?
              </button>
              <button
                v-if="showShare"
                type="button"
                class="badge share-btn"
                :class="{ 'share-btn--done': shareDisabled }"
                :disabled="sharing || shareDisabled"
                @click="emit('share')"
              >
                {{
                  sharing
                    ? '공유 중...'
                    : shareDisabled
                      ? '공유 완료'
                      : '커뮤니티에 공유'
                }}
              </button>
            </div>
          </div>
          <div class="header__bottom">
            <div v-if="tripId || destinationNotes" class="header__support">
              <DestinationNotesButton
                v-if="destinationNotes"
                :notes="destinationNotes"
              />
              <WeatherSummaryButton v-if="tripId" :trip-id="tripId" />
            </div>
            <div class="header__status">
              <span class="badge">{{ totalItems }}개</span>
              <span v-if="checkedCount" class="badge badge--packed">{{ checkedCount }}개 챙김</span>
              <span class="badge badge--fill">캐리어 {{ packedPercent }}%</span>
            </div>
          </div>
        </div>
      </header>

      <div class="luggage" @dragover.prevent @drop.prevent="onCarrierDrop">
        <div class="luggage__handle">
          <div class="handle-bar" />
          <div class="handle-pole handle-pole--l" />
          <div class="handle-pole handle-pole--r" />
        </div>

        <div class="luggage__zip">
          <span v-for="n in 28" :key="n" class="zip-tooth" />
        </div>

        <div class="luggage__body">
          <div class="body-side body-side--l">
            <div class="mesh-pocket">
              <span class="zone-tag">뚜껑 메쉬 포켓</span>
              <PackedZone
                :packed="packedZones.left_pocket"
                compact
                fill
                :cell-scale="cellScale"
                :trim-rows="trimZoneRows"
                empty-label="소형 짐"
                :item-progress="itemProgress"
                @hover="onItemHover"
                @leave="hoveredItem = null"
                @toggle-checked="toggleChecked"
                @item-drag-start="onItemDragStart"
                @item-drag-end="onItemDragEnd"
              />
            </div>
            <div class="main-compartment">
              <span class="zone-tag zone-tag--main">왼쪽 칸</span>
              <div class="strap" />
              <PackedZone
                :packed="packedZones.left"
                fill
                :cell-scale="cellScale"
                :trim-rows="trimZoneRows"
                :anim-offset="zones.left_pocket.length + zones.right_pocket.length"
                :item-progress="itemProgress"
                @hover="onItemHover"
                @leave="hoveredItem = null"
                @toggle-checked="toggleChecked"
                @item-drag-start="onItemDragStart"
                @item-drag-end="onItemDragEnd"
              />
            </div>
          </div>

          <div class="body-spine">
            <div class="body-spine__line" />
          </div>

          <div class="body-side body-side--r">
            <div class="mesh-pocket">
              <span class="zone-tag">뚜껑 메쉬 포켓</span>
              <PackedZone
                :packed="packedZones.right_pocket"
                compact
                fill
                :cell-scale="cellScale"
                :trim-rows="trimZoneRows"
                empty-label="소형 짐"
                :anim-offset="zones.left_pocket.length"
                :item-progress="itemProgress"
                @hover="onItemHover"
                @leave="hoveredItem = null"
                @toggle-checked="toggleChecked"
                @item-drag-start="onItemDragStart"
                @item-drag-end="onItemDragEnd"
              />
            </div>
            <div class="main-compartment">
              <span class="zone-tag zone-tag--main">오른쪽 칸</span>
              <div class="strap" />
              <PackedZone
                :packed="packedZones.right"
                fill
                :cell-scale="cellScale"
                :trim-rows="trimZoneRows"
                :anim-offset="zones.left_pocket.length + zones.right_pocket.length + zones.left.length"
                :item-progress="itemProgress"
                @hover="onItemHover"
                @leave="hoveredItem = null"
                @toggle-checked="toggleChecked"
                @item-drag-start="onItemDragStart"
                @item-drag-end="onItemDragEnd"
              />
            </div>
          </div>
        </div>

        <div class="luggage__edge" />

        <div class="luggage__wheels">
          <div v-for="n in 4" :key="n" class="wheel">
            <div class="wheel__hub" />
          </div>
        </div>

        <div class="luggage__shadow" />
      </div>

      <p class="hint"><strong>클릭</strong>해서 챙기고 · <strong>캐리어 밖으로 끌면</strong> 빼줄게 · 마우스 올리면 <strong>왜 챙겼는지</strong> 알려줄게</p>
    </div>

    <TipCard
      :item="hoveredItem"
      :x="tipPos.x"
      :y="tipPos.y"
      :visible="!!hoveredItem"
    />

    <Transition name="fade">
      <div v-if="draggingKey" class="drag-hint">캐리어 밖에 놓으면 짐을 빼줄게 🗑️</div>
    </Transition>

    <AddItemModal
      :open="addModalOpen"
      @close="addModalOpen = false"
      @submit="onAddItem"
    />

    <Transition name="fade">
      <div v-if="pendingRemoveItem" class="confirm-root">
        <div class="confirm-backdrop" @click="cancelRemove" />
        <div class="confirm-panel" role="dialog" aria-label="짐 빼기 확인">
          <p class="confirm-title">이건 안 챙겨도 되지?</p>
          <p class="confirm-item">{{ pendingRemoveItem.name }}</p>
          <div class="confirm-actions">
            <button type="button" class="confirm-btn confirm-btn--ghost" @click="cancelRemove">
              아니, 둘래
            </button>
            <button type="button" class="confirm-btn" @click="confirmRemove">
              응, 빼줘
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.suitcase-scene {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
}

.suitcase-scene--fullscreen {
  max-width: none;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px 36px 6px;
  box-sizing: border-box;
  overflow: hidden;
}

.back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  border: 1px solid rgba(26, 83, 92, 0.2);
  background: rgba(255, 255, 255, 0.9);
  color: var(--ocean);
  font-size: 0.85rem;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.back-btn:hover {
  background: #fff;
}

.back-btn--inline {
  position: static;
  flex-shrink: 0;
}

.state {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 60vh;
  gap: 10px;
  color: var(--muted);
}

.suitcase-scene--fullscreen .state {
  min-height: 100%;
}

.state__icon {
  font-size: 4.5rem;
  animation: bob 1.2s ease-in-out infinite;
}

.state__text {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--ocean);
}

.state__sub {
  margin: 0;
  font-size: 0.9rem;
}

.state__sub--error {
  max-width: 420px;
  line-height: 1.5;
  color: #c62828;
}

@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.wrap {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: visible;
}

.suitcase-scene--fullscreen .wrap {
  height: 100%;
}

.suitcase-scene--fullscreen .header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  column-gap: 12px;
  row-gap: 4px;
  margin-bottom: 0;
}

.suitcase-scene--fullscreen .header__main {
  display: contents;
}

.suitcase-scene--fullscreen .header__top {
  grid-column: 1 / -1;
  grid-row: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
}

.suitcase-scene--fullscreen .back-btn--inline {
  grid-column: 1;
  grid-row: 1;
  z-index: 1;
}

.suitcase-scene--fullscreen .header__identity {
  grid-column: 2;
  justify-self: center;
  flex: none;
}

.suitcase-scene--fullscreen .header__commands {
  grid-column: 3;
  justify-self: end;
}

.suitcase-scene--fullscreen .header__bottom {
  grid-column: 1 / -1;
  grid-row: 2;
}

.suitcase-scene--fullscreen .title {
  font-size: 1.48rem;
  min-width: 0;
  flex: none;
}

.suitcase-scene--fullscreen .badge {
  font-size: 0.68rem;
  padding: 4px 10px;
}

.suitcase-scene--fullscreen .badge--open {
  font-size: 0.78rem;
  padding: 5px 12px;
}

.header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.header__main {
  display: flex;
  flex-direction: column;
  flex: 1;
  align-items: stretch;
  gap: 8px;
  min-width: 0;
}

.header__top,
.header__bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.header__identity {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.header__commands,
.header__status,
.header__support {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-start;
}

.header__commands,
.header__status {
  justify-content: flex-end;
}

.header__status {
  margin-left: auto;
}

.header :deep(.header__weather) {
  flex-shrink: 0;
}

.title {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ocean);
  margin: 0;
  flex: 1;
  min-width: 120px;
}

.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--muted);
  white-space: nowrap;
}

.badge--open { background: var(--ocean); color: #fff; }
.badge--dday { color: var(--ocean); background: rgba(26, 83, 92, 0.12); border: 1px solid rgba(26, 83, 92, 0.2); font-weight: 700; }
.badge--packed { color: #4a4a4a; background: rgba(0, 0, 0, 0.06); }
.badge--fill { color: var(--ocean); background: rgba(26, 83, 92, 0.1); border: 1px solid rgba(26, 83, 92, 0.15); }
.regenerate-btn {
  border: 1px solid rgba(26, 83, 92, 0.22);
  color: var(--ocean);
  cursor: pointer;
  font-family: inherit;
}
.regenerate-btn:hover {
  background: rgba(26, 83, 92, 0.08);
}
.add-btn {
  border: 1px solid rgba(26, 83, 92, 0.22);
  color: var(--ocean);
  cursor: pointer;
  font-family: inherit;
}
.add-btn:hover {
  background: rgba(26, 83, 92, 0.08);
}
.share-btn {
  border: 1px solid rgba(255, 107, 107, 0.35);
  color: #e53935;
  cursor: pointer;
  font-family: inherit;
}
.share-btn:hover:not(:disabled) {
  background: rgba(229, 57, 53, 0.08);
}
.share-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.share-btn--done {
  border-color: rgba(26, 83, 92, 0.25);
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
}

.luggage {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  margin-top: 18px;
  padding: 0 4px 28px;
  overflow: visible;
}

.suitcase-scene--fullscreen .luggage {
  flex: 1;
  width: 100%;
  max-width: 1780px;
  align-self: center;
  margin-top: -2px;
  padding-bottom: 12px;
  overflow: hidden;
}

.suitcase-scene--fullscreen .luggage__handle {
  height: 26px;
  margin-bottom: 0;
}

.suitcase-scene--fullscreen .handle-pole {
  width: 10px;
  height: 18px;
}

.suitcase-scene--fullscreen .handle-pole--l { left: calc(50% - 40px); }
.suitcase-scene--fullscreen .handle-pole--r { right: calc(50% - 40px); }

.suitcase-scene--fullscreen .handle-bar {
  bottom: 14px;
  left: calc(50% - 46px);
  width: 92px;
  height: 9px;
}

.suitcase-scene--fullscreen .luggage__zip {
  gap: 2px;
  padding: 3px 0;
}

.suitcase-scene--fullscreen .zip-tooth {
  width: 7px;
  height: 8px;
}

.luggage__handle {
  position: relative;
  height: 36px;
  margin-bottom: 2px;
  z-index: 1;
  pointer-events: none;
  flex-shrink: 0;
}

.handle-pole {
  position: absolute;
  bottom: 0;
  width: 12px;
  height: 24px;
  background: linear-gradient(90deg, #666, #aaa, #666);
  border-radius: 4px 4px 0 0;
  border: 1px solid #555;
}
.handle-pole--l { left: calc(50% - 48px); }
.handle-pole--r { right: calc(50% - 48px); }

.handle-bar {
  position: absolute;
  bottom: 18px;
  left: calc(50% - 56px);
  width: 112px;
  height: 12px;
  background: linear-gradient(180deg, #ddd, #888);
  border-radius: 7px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}

.luggage__zip {
  display: flex;
  justify-content: center;
  gap: 3px;
  padding: 4px 0;
  background: #5c3a20;
  margin: 0 10px;
  border-radius: 4px 4px 0 0;
  position: relative;
  z-index: 2;
  flex-shrink: 0;
}

.zip-tooth {
  width: 8px;
  height: 10px;
  background: linear-gradient(180deg, #d4a853, #b8923a);
  border-radius: 1px;
  clip-path: polygon(20% 0%, 80% 0%, 100% 50%, 80% 100%, 20% 100%, 0% 50%);
}

.luggage__body {
  display: grid;
  grid-template-columns: 1fr 14px 1fr;
  margin: 0 6px;
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow: visible;
  align-items: stretch;
}

.suitcase-scene--fullscreen .luggage__body {
  margin: 0 10px;
}

.body-side {
  background: linear-gradient(180deg, #faf3eb 0%, #ede0d0 100%);
  border: 5px solid #5c3a20;
  border-top: none;
  display: flex;
  flex-direction: column;
  overflow: visible;
  min-height: 0;
  height: 100%;
  box-shadow:
    inset 0 6px 20px rgba(139, 94, 60, 0.06),
    0 4px 0 #3d2810;
}

.suitcase-scene--fullscreen .body-side {
  border-width: 6px;
  border-bottom: 0;
  box-shadow: inset 0 6px 20px rgba(139, 94, 60, 0.06);
}

.body-side--l {
  border-radius: 0 0 0 18px;
  border-right: 2px solid #6b4423;
}

.body-side--r {
  border-radius: 0 0 18px 0;
  border-left: 2px solid #6b4423;
}

.suitcase-scene--fullscreen .body-side--l,
.suitcase-scene--fullscreen .body-side--r {
  border-radius: 0;
}

.mesh-pocket {
  flex: 0 0 22%;
  min-height: 130px;
  padding: 8px 10px 10px;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 50% 50%, rgba(26, 83, 92, 0.1) 1px, transparent 1px),
    linear-gradient(180deg, rgba(200, 220, 240, 0.45) 0%, rgba(200, 220, 240, 0.2) 100%);
  background-size: 6px 6px, auto;
  border-bottom: 2px dashed rgba(26, 83, 92, 0.22);
  overflow: visible;
}

.suitcase-scene--fullscreen .mesh-pocket {
  flex-basis: 20%;
  min-height: 82px;
  padding: 5px 7px 6px;
}

.suitcase-scene--fullscreen .mesh-pocket .zone-tag {
  margin-bottom: 3px;
}

.mesh-pocket .zone-tag {
  font-size: 0.58rem;
  padding: 2px 6px;
  margin-bottom: 4px;
  flex-shrink: 0;
}

.main-compartment {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px 10px 16px;
  min-height: 0;
  overflow: visible;
}

.suitcase-scene--fullscreen .main-compartment {
  padding: 7px 7px 8px;
}

.body-spine {
  background: linear-gradient(180deg, #5c3a20, #4a2e18, #5c3a20);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
  z-index: 0;
}

.body-spine__line {
  width: 2px;
  height: 80%;
  background: rgba(255, 255, 255, 0.15);
}

.strap {
  height: 8px;
  background: linear-gradient(90deg, #a08060, #c4a882, #a08060);
  border-radius: 4px;
  margin: 6px 0 10px;
  position: relative;
  opacity: 0.5;
  flex-shrink: 0;
}

.suitcase-scene--fullscreen .strap {
  height: 6px;
  margin: 4px 0 6px;
}

.suitcase-scene--fullscreen .strap::before,
.suitcase-scene--fullscreen .strap::after {
  top: -4px;
  width: 12px;
  height: 12px;
  border-width: 1px;
}
.strap::before, .strap::after {
  content: '';
  position: absolute;
  top: -5px;
  width: 16px;
  height: 16px;
  background: #777;
  border-radius: 4px;
  border: 2px solid #555;
}
.strap::before { left: 12px; }
.strap::after { right: 12px; }

.luggage__edge {
  height: 14px;
  margin: 0 2px;
  background: linear-gradient(180deg, #5c3a20, #3d2810);
  border-radius: 0 0 12px 12px;
  box-shadow: 0 6px 0 #2a1a08;
  flex-shrink: 0;
  position: relative;
  z-index: 3;
}

.suitcase-scene--fullscreen .luggage__edge {
  height: 10px;
  margin: 0 10px;
  border-radius: 0 0 18px 18px;
  box-shadow: 0 5px 0 #2a1a08;
}

.luggage__wheels {
  display: flex;
  justify-content: space-between;
  padding: 8px 20px 0;
  flex-shrink: 0;
}

.suitcase-scene--fullscreen .luggage__wheels {
  padding: 5px 18px 0;
}

.wheel {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #555, #1a1a1a);
  border: 3px solid #333;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.suitcase-scene--fullscreen .wheel {
  width: 18px;
  height: 18px;
  border-width: 2px;
}

.suitcase-scene--fullscreen .wheel__hub {
  width: 6px;
  height: 6px;
}

.wheel__hub {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #888;
}

.luggage__shadow {
  position: absolute;
  bottom: 0;
  left: 5%;
  right: 5%;
  height: 20px;
  background: radial-gradient(ellipse, rgba(0, 0, 0, 0.18) 0%, transparent 70%);
  z-index: -1;
  pointer-events: none;
}

.zone-tag {
  display: inline-block;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #7a5c3a;
  background: rgba(255, 255, 255, 0.5);
  padding: 3px 8px;
  border-radius: 6px;
  margin-bottom: 4px;
  flex-shrink: 0;
}

.zone-tag--main {
  font-size: 0.75rem;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
}

.hint {
  text-align: center;
  font-size: 0.72rem;
  color: var(--muted);
  margin: 8px 0 0;
  flex-shrink: 0;
}

.suitcase-scene--fullscreen .hint {
  font-size: 0.64rem;
  margin-top: 4px;
}

.suitcase-scene--fullscreen :deep(.packing-item) {
  gap: 3px;
  padding: 6px 6px;
  border-width: 1.5px;
  border-radius: 8px;
}

.suitcase-scene--fullscreen :deep(.packing-item--row) {
  gap: 5px;
  padding: 5px 7px;
}

.suitcase-scene--fullscreen :deep(.packing-item--row .item-visual) {
  width: 100%;
  height: 100%;
}

.suitcase-scene--fullscreen :deep(.packing-item--row.packing-item--xs .item-visual) {
  width: 100%;
  height: 100%;
}

.suitcase-scene--fullscreen :deep(.packing-item--md .item-visual) {
  max-height: none;
}

.suitcase-scene--fullscreen :deep(.packing-item--lg .item-visual) {
  max-height: none;
}

.suitcase-scene--fullscreen :deep(.packing-item--fill.packing-item--md .item-visual) {
  max-height: none;
}

.suitcase-scene--fullscreen :deep(.packing-item--fill.packing-item--lg .item-visual) {
  max-height: none;
}

.suitcase-scene--fullscreen :deep(.item-name) {
  font-size: 0.66rem;
  line-height: 1.22;
}

.suitcase-scene--fullscreen :deep(.packing-item--row .item-name) {
  font-size: 0.62rem;
}

.suitcase-scene--fullscreen :deep(.packing-item--lg .item-name) {
  font-size: 0.72rem;
}

.suitcase-scene--fullscreen :deep(.item-qty) {
  font-size: 0.55rem;
  padding: 1px 6px;
}

.drag-hint {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 60;
  background: rgba(229, 57, 53, 0.92);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 700;
  padding: 10px 18px;
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(229, 57, 53, 0.3);
  pointer-events: none;
}

.confirm-root {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.confirm-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(20, 30, 35, 0.45);
}
.confirm-panel {
  position: relative;
  width: min(340px, 100%);
  background: linear-gradient(180deg, #fdf8f3 0%, var(--sand) 100%);
  border-radius: 18px;
  padding: 24px 22px 18px;
  text-align: center;
  box-shadow: 0 16px 40px rgba(26, 83, 92, 0.2);
}
.confirm-title {
  margin: 0 0 6px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ocean);
}
.confirm-item {
  margin: 0 0 18px;
  font-size: 0.9rem;
  color: var(--muted);
}
.confirm-actions {
  display: flex;
  gap: 8px;
}
.confirm-btn {
  flex: 1;
  border: none;
  border-radius: 12px;
  background: var(--coral);
  color: #fff;
  font-weight: 700;
  padding: 11px;
  cursor: pointer;
}
.confirm-btn--ghost {
  background: transparent;
  color: var(--muted);
  border: 1px solid rgba(26, 83, 92, 0.18);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 800px) {
  .suitcase-scene--fullscreen {
    padding: 8px 20px 12px;
  }

  .suitcase-scene--fullscreen .header {
    display: flex;
  }

  .suitcase-scene--fullscreen .header__main {
    display: flex;
  }

  .suitcase-scene--fullscreen .header__top {
    display: flex;
  }

  .luggage__body {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    gap: 0;
  }

  .body-spine {
    height: 12px;
    width: 100%;
  }

  .mesh-pocket {
    flex: 0 0 auto;
    min-height: 120px;
  }

  .title {
    font-size: 1.1rem;
  }

  .header__main {
    flex-direction: column;
    align-items: stretch;
  }

  .header__top,
  .header__bottom {
    flex-direction: column;
    align-items: stretch;
  }

  .header__commands,
  .header__status,
  .header__support {
    justify-content: flex-start;
    margin-left: 0;
  }

  .header :deep(.header__weather) {
    align-self: flex-end;
  }
}
</style>
