import { FOOTPRINT_OVERRIDES } from './overrides.js'

const POCKET_ZONES = new Set(['left_pocket', 'right_pocket'])

const CATEGORY_BASE = {
  clothing: { w: 2, h: 2 },
  toiletries: { w: 1, h: 2 },
  electronics: { w: 1, h: 1 },
  documents: { w: 1, h: 1 },
  accessories: { w: 1, h: 1 },
  health: { w: 1, h: 1 },
  other: { w: 1, h: 1 },
}

export const SMALL_KEYWORDS = [
  '미니',
  '접이',
  '동전',
  '포켓',
  '튜브',
  '일회용',
  '귀마개',
  '안대',
  '이어폰',
  '케이블',
  '충전',
  '어댑터',
  '면도',
  '칫솔',
  '치약',
  '립',
  '콤팩',
]
export const LARGE_KEYWORDS = [
  '긴',
  '린넨',
  '바지',
  '자켓',
  '수영복',
  '우비',
  '돗자리',
  '압축팩',
  '침낭',
  '슬리퍼',
  '타월',
  '세트',
  '파우치',
  '키트',
]

function clamp(n, min, max) {
  return Math.min(Math.max(n, min), max)
}

/**
 * @param {{ name: string, category?: string, zone?: string }} item
 * @returns {{ w: number, h: number }}
 */
export function getFootprint(item) {
  if (FOOTPRINT_OVERRIDES[item.name]) {
    return { ...FOOTPRINT_OVERRIDES[item.name] }
  }

  if (POCKET_ZONES.has(item.zone)) {
    return { w: 1, h: 1 }
  }

  const base = CATEGORY_BASE[item.category] || CATEGORY_BASE.other
  let { w, h } = base
  const name = item.name || ''

  if (SMALL_KEYWORDS.some((kw) => name.includes(kw))) {
    w = 1
    h = 1
  }

  if (LARGE_KEYWORDS.some((kw) => name.includes(kw))) {
    w = Math.max(w, 2)
    h = Math.max(h, 2)
  }

  if (name.length > 9) w = Math.max(w, 2)
  if (name.length > 13) h = Math.max(h, 2)

  const quantity = item.quantity || ''
  if (quantity.length > 6) w = Math.max(w, 2)
  if (quantity.length > 10) h = Math.max(h, 2)

  return { w: clamp(w, 1, 3), h: clamp(h, 1, 3) }
}

/** 뚜껑 메쉬 포켓에 넣을 소형 짐인지 판별 (짧은 라벨만) */
export function isPocketItem(item) {
  const category = item.category || 'other'
  const name = (item.name || '').trim()
  const quantity = (item.quantity || '').trim()
  const label = `${name} ${quantity}`

  if (category === 'clothing') return false
  if (LARGE_KEYWORDS.some((kw) => name.includes(kw))) return false
  if (/보조\s*배터리|배터리|멀티콘센트|멀티탭|mAh|파워뱅크|충전기\s*·|케이블\s*세트/.test(label)) {
    return false
  }

  const POCKET_MAX_NAME = 7
  const POCKET_MAX_QTY = 4
  if (name.length > POCKET_MAX_NAME) return false
  if (quantity.length > POCKET_MAX_QTY) return false

  if (category === 'documents') return true

  if (category === 'electronics') {
    return name.length <= 4
  }

  if (category === 'health') return name.length <= POCKET_MAX_NAME

  if (category === 'accessories') return name.length <= 6

  if (SMALL_KEYWORDS.some((kw) => name.includes(kw))) return true

  if (category === 'toiletries') {
    const mainFp = getFootprint({ ...item, zone: 'left' })
    if (mainFp.w === 1 && mainFp.h === 1) return true
    if (/세면|위생|생리|면도|물티슈|손난로|핫팩|선크림/.test(name) && mainFp.w === 1) return true
    return false
  }

  const mainFp = getFootprint({ ...item, zone: 'left' })
  return mainFp.w === 1 && mainFp.h === 1
}

/** zone 너비에 맞게 footprint 클램프 */
export function clampFootprint(footprint, maxCols) {
  let { w, h } = footprint
  w = clamp(w, 1, maxCols)
  h = clamp(h, 1, 4)
  if (w > maxCols) w = maxCols
  return { w, h }
}
