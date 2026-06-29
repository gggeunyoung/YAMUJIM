# 야무짐 백엔드

## 백엔드 실행 방법

백엔드는 Django 서버와 Redis가 함께 실행되어야 한다. Redis는 날씨 API 응답 캐싱에 사용한다.

### 1. 백엔드 폴더로 이동

```powershell
cd C:\materials\13_pjt\backend
```

### 2. Python 패키지 설치

```powershell
python -m pip install -r requirements.txt
```

### 3. Redis 실행

Docker를 사용하는 경우:

```powershell
docker run --name yamujim-redis -p 6379:6379 -d redis
```

이미 컨테이너를 만든 적이 있다면:

```powershell
docker start yamujim-redis
```

로컬 Redis가 설치되어 있다면:

```powershell
redis-server
```

기본 Redis 연결 주소는 다음과 같다.

```txt
redis://127.0.0.1:6379/1
```

다른 Redis 주소를 쓰려면 `.env`에 `REDIS_URL`을 추가한다.

```env
REDIS_URL=redis://127.0.0.1:6379/1
```

### 4. DB 마이그레이션

```powershell
python manage.py migrate
```

### 5. 시드 데이터 적재

```powershell
python manage.py seed_data
```

`seed_data`는 국가, 도시, 도시 좌표, 건강/안전/문화 데이터, 태그, 아이템 데이터를 적재한다. 도시 좌표가 없으면 OpenWeather Geocoding API로 좌표를 조회하고 `data/dev_assets/city_coordinates.json`에 캐싱한다.

### 6. Django 개발 서버 실행

```powershell
python manage.py runserver
```

기본 주소:

```txt
http://127.0.0.1:8000/
```

### 7. 개발용 JWT 발급

카카오 로그인 없이 Postman에서 인증 API를 테스트하려면 개발용 토큰을 발급한다.

```powershell
python manage.py dev_token
```

출력된 access token을 요청 헤더에 넣는다.

```http
Authorization: Bearer {access_token}
```

### 8. 날씨 API 테스트 예시

먼저 여행을 생성한다.

```http
POST http://127.0.0.1:8000/api/v1/trips/
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "country": 1,
  "city": 1,
  "companion_type": "alone",
  "companion_count": 1,
  "start_date": "2026-07-01",
  "end_date": "2026-07-05",
  "local_language_ok": false,
  "accommodation_type": "hotel"
}
```

응답의 `id`로 날씨를 조회한다.

```http
GET http://127.0.0.1:8000/api/v1/trips/{trip_id}/weather/
Authorization: Bearer {access_token}
```

### 9. Redis 캐시 초기화

날씨 응답은 3시간 캐싱된다. 테스트 중 외부 API 응답을 다시 받고 싶으면 Redis DB를 비운다.

Docker Redis를 쓰는 경우:

```powershell
docker exec yamujim-redis redis-cli -n 1 FLUSHDB
```

로컬 Redis CLI를 쓰는 경우:

```powershell
redis-cli -n 1 FLUSHDB
```

## 여행 날씨 API

여행별 일별 날씨는 아래 엔드포인트에서 조회한다.

```txt
GET /api/v1/trips/{trip_id}/weather/
```

인증이 필요한 API이므로 요청 헤더에 JWT access token을 포함해야 한다.

```http
Authorization: Bearer {access_token}
```

## 날씨 데이터 소스

현재 날씨 응답은 두 API를 조합한다.

| 용도 | API | 이유 |
| --- | --- | --- |
| 기온, 체감온도, 습도, 강수량, 구름량 | OpenWeather One Call 4.0 daily timeline | 최대 약 1.5년 뒤 날짜까지 조회 가능 |
| UV 지수 | Open-Meteo Forecast API | OpenWeather 4.0 응답의 `uvi`가 대부분 0으로 내려와 보정 필요 |

Open-Meteo Forecast API는 가까운 미래 예보 중심이다. 그래서 여행 날짜가 Open-Meteo 예보 범위 밖이면 UV는 제공하지 않고 `uv_available: false`로 표시한다.

## 응답 예시

```json
{
  "trip": 1,
  "location": {
    "country": "일본",
    "city": "도쿄",
    "lat": 35.6768601,
    "lon": 139.7638947
  },
  "source": "onecall4_daily",
  "unit": "metric",
  "days": [
    {
      "date": "2026-07-01",
      "temp_c": 28.4,
      "feels_like_c": 31.2,
      "humidity": 72,
      "uvi": 7.8,
      "uv_source": "open_meteo",
      "uv_available": true,
      "weather": "Light rain",
      "weather_description": "약한 비",
      "weather_inferred": true,
      "rain_mm": 1.28,
      "snow_mm": 0,
      "clouds": 85,
      "precipitation_level": "low"
    }
  ],
  "missing_dates": [],
  "cached": false
}
```

## UV 처리 정책

OpenWeather One Call 4.0 daily 응답의 `uvi` 값은 실제 테스트에서 대부분 0으로 내려왔다. 그래서 백엔드는 Open-Meteo Forecast API의 `uv_index_max`를 날짜 기준으로 매칭해 `uvi`에 덮어쓴다.

Open-Meteo 요청 형식:

```txt
https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=uv_index_max&timezone=auto
```

UV 필드 의미:

| 필드 | 의미 |
| --- | --- |
| `uvi` | 최종 UV 지수. Open-Meteo 값이 있으면 그 값을 사용한다. |
| `uv_source` | `open_meteo`, `openweather`, `unavailable` 중 하나 |
| `uv_available` | 해당 날짜에 사용할 수 있는 UV 값이 있으면 `true` |

현재 정책상 Open-Meteo 값이 없으면 `uvi`를 `null`로 내려준다.

```json
{
  "uvi": null,
  "uv_source": "unavailable",
  "uv_available": false
}
```

## 날씨 상태 추론 정책

OpenWeather One Call 4.0 daily 응답은 `weather: null`을 자주 반환한다. 그래서 백엔드는 원본 `weather`가 없을 때 `snow`, `rain`, `clouds` 수치로 여행 준비물 추천에 필요한 날씨 상태를 추론한다.

`weather_inferred` 필드 의미:

| 값 | 의미 |
| --- | --- |
| `false` | OpenWeather가 제공한 원본 `weather` 값을 사용 |
| `true` | 원본 `weather`가 없어 백엔드가 수치형 데이터로 추론 |

추론 우선순위는 다음과 같다.

1. 눈
2. 비
3. 구름량

비나 눈이 오는 날은 구름량도 높게 나오는 경우가 많으므로, 강수 정보를 구름량보다 먼저 본다.

## 비 기준

OpenWeather의 `rain` 값은 일 단위 강수량 mm로 사용한다.

| rain_mm | weather | weather_description | precipitation_level |
| --- | --- | --- | --- |
| `>= 20` | `Heavy rain` | `폭우성 비` | `very_high` |
| `>= 10` | `Heavy rain` | `많은 비` | `high` |
| `>= 3` | `Rain` | `비` | `medium` |
| `>= 0.5` | `Light rain` | `약한 비` | `low` |
| `> 0` | 구름량 기준 | 구름량 기준 | `trace` |
| `0` 또는 없음 | 구름량 기준 | 구름량 기준 | `none` |

`0.05mm`, `0.19mm` 같은 아주 작은 강수량은 비로 단정하지 않는다. 값은 `rain_mm`에 보존하지만 화면 표시용 날씨는 구름량 기준으로 정한다. 이렇게 해야 매우 약한 강수 때문에 우산이나 우비를 과하게 추천하지 않는다.

## 눈 기준

| snow_mm | weather | weather_description |
| --- | --- | --- |
| `>= 3` | `Snow` | `눈` |
| `> 0` | `Light snow` | `약한 눈` |

눈도 `precipitation_level`은 비와 같은 기준을 사용한다.

## 구름량 기준

비나 눈이 의미 있게 잡히지 않을 때만 구름량으로 날씨를 추론한다.

| clouds | weather | weather_description |
| --- | --- | --- |
| `>= 85` | `Clouds` | `흐림` |
| `>= 40` | `Partly cloudy` | `구름 많음` |
| `< 40` | `Clear` | `맑음` |

## 추천 로직에서의 사용 기준

준비물 추천에서는 `weather` 텍스트보다 `precipitation_level`을 우선해서 쓰는 것이 좋다.

| precipitation_level | 추천 기준 |
| --- | --- |
| `trace` | 우산 필수 추천은 하지 않고, 약한 강수 가능성 메모 정도만 사용 |
| `low` | 접이식 우산, 방수 파우치 선택 추천 |
| `medium` | 우산, 여분 양말, 방수 파우치 추천 |
| `high` | 우산, 우비, 가방 방수 커버 강하게 추천 |
| `very_high` | 강한 비 대비와 일정 조정 안내까지 고려 |

## 캐싱

날씨 응답은 Redis에 3시간 캐싱한다.

캐시 키에는 여행 id, 도시 id, 여행 시작일, 여행 종료일이 포함된다.

```txt
yamujim:weather:v2:trip:{trip_id}:city:{city_id}:{start_date}:{end_date}
```

동일한 여행 일정으로 다시 요청하면 외부 API를 다시 호출하지 않고 캐시된 응답을 반환한다.
