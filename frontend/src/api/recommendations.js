import client from './client'

// 추천 생성 (동기, LLM 호출 ~24초+). trip_id 기준.
export function createRecommendation(tripId, options = {}) {
  const payload = options.advancedModel
    ? { advanced_model: options.advancedModel }
    : (options.advancedMode ? { advanced_mode: true } : undefined)
  return client.post(`/trips/${tripId}/recommendations/`, payload)
}

// 해당 여행의 최신 추천
export function fetchLatestRecommendation(tripId) {
  return client.get(`/trips/${tripId}/recommendations/latest/`)
}

// 추천 상세
export function fetchRecommendation(recommendationId) {
  return client.get(`/recommendations/${recommendationId}/`)
}
