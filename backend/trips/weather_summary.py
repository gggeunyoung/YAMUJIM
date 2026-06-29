import json
import os

import requests

from .weather import get_trip_daily_weather


GMS_CHAT_COMPLETIONS_URL = (
    "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
)


class WeatherSummaryError(Exception):
    pass


def summarize_trip_weather_with_ai(trip):
    weather = get_trip_daily_weather(trip)
    return {
        "weather": weather,
        "ai_summary": _ask_gms_for_weather_summary(trip, weather),
    }


def _ask_gms_for_weather_summary(trip, weather):
    api_key = os.getenv("GMS_KEY")
    if not api_key:
        raise WeatherSummaryError("GMS_KEY is not configured.")

    try:
        response = requests.post(
            os.getenv("GMS_CHAT_COMPLETIONS_URL", GMS_CHAT_COMPLETIONS_URL),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": os.getenv("GMS_MODEL", "gpt-5-nano"),
                "reasoning_effort": "low",
                "messages": [
                    {"role": "developer", "content": _system_prompt()},
                    {"role": "user", "content": json.dumps(
                        _summary_payload(trip, weather), ensure_ascii=False)},
                ],
            },
            timeout=float(os.getenv("GMS_TIMEOUT_SECONDS", "180")),
        )
    except requests.RequestException as exc:
        raise WeatherSummaryError("GMS weather summary request failed.") from exc

    if response.status_code != 200:
        raise WeatherSummaryError("GMS weather summary request failed.")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_llm_content(content)
    except (KeyError, ValueError, TypeError) as exc:
        raise WeatherSummaryError("GMS weather summary response was invalid.") from exc


def _system_prompt():
    return (
        "Answer in Korean. You summarize travel weather forecasts for Yamujim. "
        "Use only the supplied weather data. Be concise and practical for a traveler. "
        "Mention rain, snow, strong UV, heat, cold, and major day-to-day changes when relevant. "
        "Return JSON only with this schema: "
        '{"headline":string,"summary":string,'
        '"daily":[{"date":string,"summary":string}],'
        '"alerts":[string],"packing_notes":[string]}'
    )


def _summary_payload(trip, weather):
    return {
        "trip": {
            "country": trip.country.name,
            "city": trip.city.name,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
        },
        "weather": {
            "source": weather.get("source"),
            "unit": weather.get("unit"),
            "missing_dates": weather.get("missing_dates", []),
            "days": [_compact_day(day) for day in weather.get("days", [])],
        },
    }


def _compact_day(day):
    return {
        "date": day.get("date"),
        "temp_c": day.get("temp_c"),
        "feels_like_c": day.get("feels_like_c"),
        "humidity": day.get("humidity"),
        "uvi": day.get("uvi"),
        "uv_available": day.get("uv_available"),
        "weather": day.get("weather"),
        "weather_description": day.get("weather_description"),
        "rain_mm": day.get("rain_mm"),
        "snow_mm": day.get("snow_mm"),
        "precipitation_level": day.get("precipitation_level"),
    }


def _parse_llm_content(content):
    if isinstance(content, dict):
        return content

    text = str(content).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("Weather summary must be a JSON object.")
    return result
