import client from './client'

// 취향+관광스타일 조회 (없으면 null 반환)
export function fetchPreference() {
  return client.get('/me/preference/')
}

// 취향+관광스타일 저장 (upsert)
export function savePreference(payload) {
  return client.put('/me/preference/', payload)
}

// 방문 장소 유형 선택지 (id/name)
export function fetchVisitPlaceTypes() {
  return client.get('/visit-place-types/')
}
