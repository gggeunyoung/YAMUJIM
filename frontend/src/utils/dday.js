/** 출발일 기준 D-day 라벨 (오늘= D-Day, 이후= D-N, 지남= D+N) */
export function formatDday(startDate) {
  if (!startDate) return ''

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const start = new Date(startDate)
  if (Number.isNaN(start.getTime())) return ''
  start.setHours(0, 0, 0, 0)

  const diff = Math.round((start - today) / (1000 * 60 * 60 * 24))
  if (diff > 0) return `D-${diff}`
  if (diff === 0) return 'D-Day'
  return `D+${Math.abs(diff)}`
}
