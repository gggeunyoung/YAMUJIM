/**
 * 백엔드 추천 응답 → OpenSuitcase가 기대하는 item 형태로 변환.
 *
 * 백엔드 item: { item_name, default_tip, category(한글 기능형), priority, reason }
 * general_item: { name, category(한글 자유서술), quantity, reason }
 * OpenSuitcase item: { key, name, category(영문), tip, quantity, emoji?, zone }
 */

import { assignZones } from './groupItems.js'
import { dedupePackingItems } from './itemAffinity.js'

const CATEGORY_RULES = [
  [/문서|서류|여권|비자|증명/, 'documents'],
  [/전자|충전|케이블|배터리|어댑터|기기/, 'electronics'],
  [/의약|약품|상비약/, 'health'],
  [/위생|청결|세면|화장|그루밍|면도|생리/, 'toiletries'],
  [/건강/, 'health'],
  [/안전|비상/, 'health'],
  [/우산|우비|선글라스|모자|비|우기|날씨/, 'accessories'],
  [/의류|옷/, 'clothing'],
  [/액티비티|액세/, 'accessories'],
]

function mapCategory(korean, name = '') {
  const s = `${korean || ''} ${name || ''}`
  for (const [re, en] of CATEGORY_RULES) {
    if (re.test(s)) return en
  }
  return 'other'
}

const PRIORITY_LABEL = {
  required: '필수',
  recommended: '권장',
  optional: '선택',
}

function withKeys(items, prefix) {
  const seen = new Map()
  return items.map((item) => {
    const base = `${prefix}-${item.name}`
    const count = seen.get(base) || 0
    seen.set(base, count + 1)
    const key = count ? `${base}#${count}` : base
    return { ...item, key }
  })
}

export function adaptRecommendation(rec) {
  if (!rec) return []

  const general = withKeys(
    (rec.general_items || []).map((g) => ({
      name: g.name,
      category: mapCategory(g.category, g.name),
      tip: g.reason || '',
      quantity: g.quantity || '',
      priority: 'recommended',
    })),
    'g',
  )

  const catalog = withKeys(
    (rec.items || []).map((it) => ({
      name: it.item_name,
      category: mapCategory(it.category, it.item_name),
      tip: it.reason || it.default_tip || '',
      quantity: PRIORITY_LABEL[it.priority] || '',
      priority: it.priority || 'recommended',
    })),
    'c',
  )

  return assignZones(dedupePackingItems([...general, ...catalog]))
}

/** 추천 응답 → OpenSuitcase 헤더용 안내 메시지 배열(notes.messages). */
export function recommendationMessages(rec) {
  const notes = rec?.notes
  if (notes && Array.isArray(notes.messages)) return notes.messages
  return []
}
