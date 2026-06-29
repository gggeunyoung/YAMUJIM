import client from './client'

// 내 여행 목록 / 생성 / 상세 / 수정 / 삭제
export function fetchTrips() {
  return client.get('/trips/')
}
export function createTrip(payload) {
  return client.post('/trips/', payload)
}
export function fetchTrip(id) {
  return client.get(`/trips/${id}/`)
}
export function updateTrip(id, payload) {
  return client.patch(`/trips/${id}/`, payload)
}
export function deleteTrip(id) {
  return client.delete(`/trips/${id}/`)
}

// 날씨 (실시간) / 날씨 AI 요약
export function fetchTripWeather(id) {
  return client.get(`/trips/${id}/weather/`)
}
export function fetchTripWeatherSummary(id) {
  return client.get(`/trips/${id}/weather/ai-summary/`)
}
