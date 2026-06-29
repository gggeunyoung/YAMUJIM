from datetime import datetime, time, timedelta, timezone

import requests
from django.conf import settings
from django.core.cache import cache


ONE_CALL_DAILY_URL = "https://api.openweathermap.org/data/4.0/onecall/timeline/1day"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL = 60 * 60 * 3
ONE_CALL_DAILY_LIMIT = 10


class WeatherError(Exception):
    pass


def get_trip_daily_weather(trip):
    cache_key = (
        f"yamujim:weather:v2:trip:{trip.id}:city:{trip.city_id}:"
        f"{trip.start_date}:{trip.end_date}"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        cached["cached"] = True
        return cached

    coords = _get_city_coordinates(trip.city)
    result = _fetch_one_call_daily_weather(trip, coords)
    _apply_open_meteo_uv(result, coords)

    result["cached"] = False
    cache.set(cache_key, result, CACHE_TTL)
    return result


def _get_city_coordinates(city):
    if city.latitude is None or city.longitude is None:
        raise WeatherError("City coordinates are not configured. Run seed_data first.")
    return {"lat": city.latitude, "lon": city.longitude}


def _fetch_one_call_daily_weather(trip, coords):
    by_date = {}
    requested = _date_range(trip.start_date, trip.end_date)
    for start in range(0, len(requested), ONE_CALL_DAILY_LIMIT):
        chunk = requested[start:start + ONE_CALL_DAILY_LIMIT]
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "start": _start_timestamp(chunk[0]),
            "cnt": len(chunk),
            "units": "metric",
            "lang": "kr",
            "appid": _api_key(),
        }
        response = requests.get(ONE_CALL_DAILY_URL, params=params, timeout=5)
        if response.status_code != 200:
            raise WeatherError("OpenWeather One Call 4.0 daily API request failed.")

        payload = response.json()
        timezone_offset = payload.get("timezone_offset", 0)
        for row in payload.get("data", []):
            day = _local_date(row["dt"], timezone_offset)
            weather = _parse_weather(row)
            by_date[day] = {
                "date": day.isoformat(),
                "temp_c": row.get("temp", {}).get("day"),
                "feels_like_c": row.get("feels_like", {}).get("day"),
                "humidity": row.get("humidity"),
                "uvi": row.get("uvi"),
                "uv_source": "openweather",
                "uv_available": row.get("uvi") is not None,
                "weather": weather["main"],
                "weather_description": weather["description"],
                "weather_inferred": weather["inferred"],
                "rain_mm": _amount(row.get("rain")),
                "snow_mm": _amount(row.get("snow")),
                "clouds": row.get("clouds"),
                "precipitation_level": weather["precipitation_level"],
            }

    return _build_response(trip, coords, "onecall4_daily", by_date)


def _apply_open_meteo_uv(result, coords):
    uv_by_date = _fetch_open_meteo_uv(coords)
    for day in result["days"]:
        uv = uv_by_date.get(day["date"])
        if uv is None:
            day["uvi"] = None
            day["uv_source"] = "unavailable"
            day["uv_available"] = False
        else:
            day["uvi"] = uv
            day["uv_source"] = "open_meteo"
            day["uv_available"] = True


def _fetch_open_meteo_uv(coords):
    response = requests.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "daily": "uv_index_max",
            "timezone": "auto",
        },
        timeout=5,
    )
    if response.status_code != 200:
        return {}

    daily = response.json().get("daily") or {}
    times = daily.get("time") or []
    values = daily.get("uv_index_max") or []
    return dict(zip(times, values))


def _build_response(trip, coords, source, by_date):
    requested = _date_range(trip.start_date, trip.end_date)
    days = [by_date[day] for day in requested if day in by_date]
    missing = [day.isoformat() for day in requested if day not in by_date]
    return {
        "trip": trip.id,
        "location": {
            "country": trip.country.name,
            "city": trip.city.name,
            "lat": coords["lat"],
            "lon": coords["lon"],
        },
        "source": source,
        "unit": "metric",
        "days": days,
        "missing_dates": missing,
    }


def _api_key():
    if not settings.OPEN_WEATHER_KEY:
        raise WeatherError("OPEN_WEATHER_KEY is not configured.")
    return settings.OPEN_WEATHER_KEY


def _date_range(start, end):
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _local_date(timestamp, timezone_offset):
    tz = timezone(timedelta(seconds=timezone_offset))
    return datetime.fromtimestamp(timestamp, tz).date()


def _start_timestamp(day):
    return int(datetime.combine(day, time.min, tzinfo=timezone.utc).timestamp())


def _parse_weather(row):
    original = row.get("weather")
    if original:
        weather = original[0]
        return {
            "main": weather.get("main"),
            "description": weather.get("description"),
            "inferred": False,
            "precipitation_level": _precipitation_level(row),
        }

    main, description = _infer_weather(row)
    return {
        "main": main,
        "description": description,
        "inferred": True,
        "precipitation_level": _precipitation_level(row),
    }


def _infer_weather(row):
    rain = _amount(row.get("rain"))
    snow = _amount(row.get("snow"))
    clouds = row.get("clouds")

    if snow >= 3:
        return "Snow", "눈"
    if snow > 0:
        return "Light snow", "약한 눈"

    if rain >= 20:
        return "Heavy rain", "폭우성 비"
    if rain >= 10:
        return "Heavy rain", "많은 비"
    if rain >= 3:
        return "Rain", "비"
    if rain >= 0.5:
        return "Light rain", "약한 비"

    return _cloud_weather(clouds)


def _cloud_weather(clouds):
    if clouds is None:
        return None, None
    if clouds >= 85:
        return "Clouds", "흐림"
    if clouds >= 40:
        return "Partly cloudy", "구름 많음"
    return "Clear", "맑음"


def _precipitation_level(row):
    rain = _amount(row.get("rain"))
    snow = _amount(row.get("snow"))
    amount = max(rain, snow)

    if amount >= 20:
        return "very_high"
    if amount >= 10:
        return "high"
    if amount >= 3:
        return "medium"
    if amount >= 0.5:
        return "low"
    if amount > 0:
        return "trace"
    return "none"


def _amount(value):
    return value or 0
