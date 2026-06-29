/**
 * 백엔드 item_affinity.py와 동일한 키워드 그룹 — UI 최종 중복 제거.
 * general 항목이 catalog보다 앞에 오면 서버 확정 항목이 우선 유지됩니다.
 */

const AFFINITY_RULES = [
  ['menstrual', ['생리']],
  ['razor', ['면도', '쉐이빙']],
  ['sunscreen', ['선크림', 'SPF', '자외선 차단']],
  ['umbrella', ['우산']],
  ['raincoat', ['우비']],
  ['makeup', ['메이크업']],
  ['skincare', ['스킨케어', '기초 화장', '화장품', '클렌저', '로션', '토너', '세럼']],
  ['beauty_case', ['화장품 파우치', '뷰티 파우치', '화장 파우치']],
  ['toiletries', ['세면도구', '미니 세면', '칫솔', '치약']],
  ['documents', ['여권', '신분증', '항공권', '비자', '증명']],
  ['power_bank', ['보조 배터리', '보조배터리']],
  ['charger', ['충전기', '충전 케이블', '케이블']],
  ['power_strip', ['멀티콘센트', '멀티탭']],
  ['adapter', ['어댑터', '플러그 변환']],
  ['medicine', ['상비약', '의약', '약품', '진통', '소화제', '고산병']],
  ['hair_styler', ['고데기']],
  ['hair_care', ['헤어팩', '드라이 샴푸', '헤어 트리트먼트']],
  ['hair_style', ['왁스', '포마드', '스타일링']],
  ['wet_wipes', ['물티슈']],
  ['slippers', ['슬리퍼']],
  ['sleep', ['귀마개', '안대']],
  ['lock', ['자물쇠', '잠금장치', '잠금']],
  ['anti_theft', ['도난방지', 'RFID', '스트랩']],
  ['dry_bag', ['드라이백', '방수 드라이백']],
  ['phone_waterproof', ['방수 파우치', '방수케이스']],
  ['korean_food', ['고추장']],
  ['sleep_liner', ['침낭 라이너']],
  ['shower_filter', ['필터 샤워기', '샤워 필터']],
  ['glasses', ['돋보기', '다초점', '렌즈']],
  ['mask', ['방진 마스크', '마스크']],
  ['insect_repellent', ['모기 기피', '기피제']],
  ['towel', ['스포츠 타월', '타월']],
  ['thermos_bag', ['텀블러 백']],
]

const AFFINITY_PREFIX = 'affinity:'

export function itemAffinityKey(name) {
  const text = String(name || '').trim()
  if (!text) return text
  for (const [key, parts] of AFFINITY_RULES) {
    if (parts.some((part) => text.includes(part))) {
      return `${AFFINITY_PREFIX}${key}`
    }
  }
  return text
}

export function dedupePackingItems(items) {
  const seenNames = new Set()
  const seenAffinities = new Set()
  const result = []

  for (const item of items) {
    const name = String(item.name || '').trim()
    if (!name || seenNames.has(name)) continue
    const affinity = itemAffinityKey(name)
    if (affinity.startsWith(AFFINITY_PREFIX)) {
      if (seenAffinities.has(affinity)) continue
      seenAffinities.add(affinity)
    }
    seenNames.add(name)
    result.push(item)
  }

  return result
}
