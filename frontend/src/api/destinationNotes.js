import { fetchCountry, fetchCity } from './places'

/** 국가 문화 팁 + 도시 긴급 연락처 */
export async function fetchDestinationNotes(countryId, cityId) {
  const [countryRes, cityRes] = await Promise.all([
    fetchCountry(countryId),
    fetchCity(cityId),
  ])
  const country = countryRes.data
  const city = cityRes.data

  return {
    countryName: country.name,
    cityName: city.name,
    culturalTips: country.cultural_tips || [],
    emergencyContact: city.safety?.emergency_contact || '',
  }
}
