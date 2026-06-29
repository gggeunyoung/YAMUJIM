import { ZONE_CONFIG } from './config.js'
import { clampFootprint, getFootprint } from './footprint.js'
import { packBlocks } from './layout.js'

/**
 * zone 아이템 목록 → footprint + 테트리스 배치 결과
 * @param {object[]} items
 * @param {keyof ZONE_CONFIG} zoneKey
 */
export function packZone(items, zoneKey) {
  const config = ZONE_CONFIG[zoneKey]
  const { cols, minRows, cellPx, gap } = config

  const blocks = items.map((item, i) => {
    const fp = clampFootprint(getFootprint({ ...item, zone: zoneKey }), cols)
    return {
      key: item.key || `${zoneKey}-${item.name}-${i}`,
      item,
      w: fp.w,
      h: fp.h,
    }
  })

  const { placed, rows } = packBlocks(blocks, cols)

  return {
    cols,
    rows: Math.max(minRows, rows),
    cellPx,
    gap,
    placed,
    usedCells: placed.reduce((s, p) => s + p.w * p.h, 0),
    capacityCells: cols * Math.max(minRows, rows),
  }
}
