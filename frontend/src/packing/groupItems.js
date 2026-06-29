/**
 * 비슷한 준비물을 인접 배치·같은 캐리어 칸에 모으기 위한 affinity 그룹.
 */

import { isPocketItem } from './footprint.js'

const AFFINITY_RULES = [
  { id: 'oral', patterns: [/칫솔/, /치약/, /가글/, /치실/, /구강/] },
  { id: 'skincare', patterns: [/클렌저/, /세면/, /로션/, /크림/, /선크림/, /화장/, /스킨/, /토너/] },
  { id: 'documents', patterns: [/여권/, /비자/, /서류/, /신분증/, /항공권/, /증명/] },
  { id: 'charger', patterns: [/충전/, /케이블/, /어댑터/, /배터리/, /멀티콘센트/, /콘센트/] },
  { id: 'clothing_top', patterns: [/상의/, /티셔츠/, /셔츠/, /니트/, /재킷/, /자켓/, /외투/, /코트/] },
  { id: 'clothing_bottom', patterns: [/하의/, /바지/, /치마/, /반바지/] },
  { id: 'clothing_inner', patterns: [/속옷/, /양말/, /잠옷/, /언더/] },
  { id: 'medicine', patterns: [/상비약/, /의약/, /약품/, /진통/, /소화제/] },
  { id: 'rain', patterns: [/우산/, /우비/, /방수/] },
]

const AFFINITY_ORDER = {
  documents: 0,
  charger: 1,
  oral: 2,
  skincare: 3,
  medicine: 4,
  clothing_top: 5,
  clothing_bottom: 6,
  clothing_inner: 7,
  rain: 8,
  other: 99,
}

const CATEGORY_AFFINITY = {
  documents: 'documents',
  electronics: 'charger',
  toiletries: 'skincare',
  health: 'medicine',
  clothing: 'clothing_top',
  accessories: 'other',
  other: 'other',
}

export function getAffinityGroup(item) {
  const name = item.name || ''
  for (const { id, patterns } of AFFINITY_RULES) {
    if (patterns.some((re) => re.test(name))) return id
  }
  return CATEGORY_AFFINITY[item.category] || 'other'
}

export function sortItemsForPacking(items) {
  return [...items]
    .map((item, index) => ({
      ...item,
      affinityGroup: getAffinityGroup(item),
      _index: index,
    }))
    .sort((a, b) => {
      const ga = AFFINITY_ORDER[a.affinityGroup] ?? 50
      const gb = AFFINITY_ORDER[b.affinityGroup] ?? 50
      if (ga !== gb) return ga - gb
      if (a.category !== b.category) return a.category.localeCompare(b.category)
      return a._index - b._index
    })
    .map(({ _index, ...item }) => item)
}

function nextZone(counter, pocket) {
  if (pocket) {
    return counter.pocket++ % 2 === 0 ? 'left_pocket' : 'right_pocket'
  }
  return counter.main++ % 2 === 0 ? 'left' : 'right'
}

/** affinity 그룹이 같은 아이템은 가능한 한 같은 zone에 배치 (포켓/메인은 분리) */
export function assignZones(items) {
  const sorted = sortItemsForPacking(items)
  const zoneByGroup = {}
  const counters = { main: 0, pocket: 0 }

  return sorted.map((it) => {
    const pocket = isPocketItem(it)
    const groupKey = `${it.affinityGroup}:${pocket ? 'pocket' : 'main'}`

    if (zoneByGroup[groupKey]) {
      return { ...it, zone: zoneByGroup[groupKey] }
    }

    const zone = nextZone(counters, pocket)
    zoneByGroup[groupKey] = zone
    return { ...it, zone }
  })
}
