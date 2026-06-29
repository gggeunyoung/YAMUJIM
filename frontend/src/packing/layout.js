/**
 * Skyline 기반 2D bin packing — 테트리스식 빼곡 배치
 * @param {Array<{ key: string, w: number, h: number, item: object }>} blocks
 * @param {number} cols
 * @returns {{ placed: Array, rows: number }}
 */
export function packBlocks(blocks, cols) {
  const sorted = [...blocks].sort(
    (a, b) => b.w * b.h - a.w * b.h || b.h - a.h || b.w - a.w,
  )

  const skyline = new Array(cols).fill(0)
  const placed = []

  for (const block of sorted) {
    const w = Math.min(block.w, cols)
    const h = block.h

    let bestCol = 0
    let bestY = Infinity

    for (let col = 0; col <= cols - w; col += 1) {
      const y = Math.max(...skyline.slice(col, col + w))
      if (y < bestY) {
        bestY = y
        bestCol = col
      }
    }

    for (let c = bestCol; c < bestCol + w; c += 1) {
      skyline[c] = bestY + h
    }

    placed.push({
      ...block,
      w,
      h,
      col: bestCol,
      row: bestY,
    })
  }

  const rows = placed.length ? Math.max(...placed.map((p) => p.row + p.h)) : 0
  return { placed, rows }
}
