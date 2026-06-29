import client from './client'

// 국가 목록 / 상세 (읽기전용 공개)
export function fetchCountries() {
  return client.get('/countries/')
}
export function fetchCountry(id) {
  return client.get(`/countries/${id}/`)
}

// 도시 목록(국가별 필터) / 상세
export function fetchCities(countryId) {
  return client.get('/cities/', { params: countryId ? { country: countryId } : {} })
}
export function fetchCity(id) {
  return client.get(`/cities/${id}/`)
}
