from datetime import date, datetime, timedelta, timezone
import json
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient

from accounts.models import User
from places.models import City, Country
from trips.models import MAX_WEATHER_FORECAST_DAYS, Trip
from trips.serializers import TripSerializer
from trips.weather import get_trip_daily_weather


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "weather-tests",
    }
}


def timestamp(year, month, day):
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())


class WeatherServiceTests(TestCase):
    @override_settings(CACHES=TEST_CACHES, OPEN_WEATHER_KEY="test-key")
    @patch("trips.weather.requests.get")
    def test_get_trip_daily_weather_uses_open_meteo_uv_and_cache(self, mock_get):
        user = User.objects.create_user(social_provider="kakao", social_id="weather-user")
        country = Country.objects.create(name="Japan")
        city = City.objects.create(
            country=country,
            name="Tokyo",
            latitude=35.68,
            longitude=139.76,
        )
        trip = Trip.objects.create(
            user=user,
            country=country,
            city=city,
            companion_type=Trip.Companion.ALONE,
            companion_count=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 2),
            local_language_ok=False,
            accommodation_type=Trip.Accommodation.HOTEL,
        )
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: {
                "timezone_offset": 0,
                "data": [
                    {
                        "dt": timestamp(2026, 7, 1),
                        "temp": {"day": 28.4},
                        "feels_like": {"day": 31.2},
                        "humidity": 72,
                        "uvi": 0,
                        "weather": None,
                        "clouds": 85,
                        "rain": 1.28,
                    },
                    {
                        "dt": timestamp(2026, 7, 2),
                        "temp": {"day": 29.0},
                        "feels_like": {"day": 32.0},
                        "humidity": 70,
                        "uvi": 0,
                        "weather": None,
                        "clouds": 100,
                        "rain": 16.0,
                    },
                ],
            }),
            Mock(status_code=200, json=lambda: {
                "daily": {
                    "time": ["2026-07-01", "2026-07-02"],
                    "uv_index_max": [7.8, 6.4],
                },
            }),
        ]

        first = get_trip_daily_weather(trip)
        second = get_trip_daily_weather(trip)

        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(first["source"], "onecall4_daily")
        self.assertEqual(first["days"][0]["temp_c"], 28.4)
        self.assertEqual(first["days"][0]["feels_like_c"], 31.2)
        self.assertEqual(first["days"][0]["humidity"], 72)
        self.assertEqual(first["days"][0]["uvi"], 7.8)
        self.assertEqual(first["days"][0]["uv_source"], "open_meteo")
        self.assertTrue(first["days"][0]["uv_available"])
        self.assertEqual(first["days"][0]["weather"], "Light rain")
        self.assertEqual(first["days"][0]["weather_description"], "약한 비")
        self.assertTrue(first["days"][0]["weather_inferred"])
        self.assertEqual(first["days"][0]["rain_mm"], 1.28)
        self.assertEqual(first["days"][0]["snow_mm"], 0)
        self.assertEqual(first["days"][0]["clouds"], 85)
        self.assertEqual(first["days"][0]["precipitation_level"], "low")
        self.assertEqual(first["days"][1]["precipitation_level"], "high")
        self.assertEqual(first["missing_dates"], [])
        self.assertEqual(mock_get.call_count, 2)

        weather_params = mock_get.call_args_list[0].kwargs["params"]
        self.assertEqual(weather_params["cnt"], 2)
        self.assertEqual(weather_params["units"], "metric")

        uv_params = mock_get.call_args_list[1].kwargs["params"]
        self.assertEqual(uv_params["daily"], "uv_index_max")
        self.assertEqual(uv_params["timezone"], "auto")


class TripDateValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            social_provider="kakao", social_id="trip-date-user")
        self.country = Country.objects.create(name="Japan")
        self.city = City.objects.create(
            country=self.country, name="Tokyo", latitude=35.68, longitude=139.76)

    def test_serializer_rejects_end_date_beyond_weather_forecast_range(self):
        start_date = django_timezone.localdate() + timedelta(days=1)
        end_date = django_timezone.localdate() + timedelta(
            days=MAX_WEATHER_FORECAST_DAYS + 1)

        serializer = TripSerializer(data={
            "country": self.country.id,
            "city": self.city.id,
            "companion_type": Trip.Companion.ALONE,
            "companion_count": 1,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "local_language_ok": False,
            "accommodation_type": Trip.Accommodation.HOTEL,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("end_date", serializer.errors)

    def test_model_rejects_end_date_beyond_weather_forecast_range(self):
        trip = Trip(
            user=self.user,
            country=self.country,
            city=self.city,
            companion_type=Trip.Companion.ALONE,
            companion_count=1,
            start_date=django_timezone.localdate() + timedelta(days=1),
            end_date=django_timezone.localdate() + timedelta(
                days=MAX_WEATHER_FORECAST_DAYS + 1),
            local_language_ok=False,
            accommodation_type=Trip.Accommodation.HOTEL,
        )

        with self.assertRaises(ValidationError) as exc:
            trip.clean()
        self.assertIn("end_date", exc.exception.message_dict)


class WeatherSummaryApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            social_provider="kakao", social_id="weather-summary-user")
        self.country = Country.objects.create(name="Japan")
        self.city = City.objects.create(
            country=self.country, name="Tokyo", latitude=35.68, longitude=139.76)
        self.trip = Trip.objects.create(
            user=self.user,
            country=self.country,
            city=self.city,
            companion_type=Trip.Companion.ALONE,
            companion_count=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 2),
            local_language_ok=False,
            accommodation_type=Trip.Accommodation.HOTEL,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("trips.weather_summary.requests.post")
    @patch("trips.weather_summary.get_trip_daily_weather")
    def test_weather_ai_summary_returns_weather_and_gms_summary(
            self, mocked_weather, mocked_post):
        mocked_weather.return_value = {
            "trip": self.trip.id,
            "location": {
                "country": "Japan",
                "city": "Tokyo",
                "lat": 35.68,
                "lon": 139.76,
            },
            "source": "onecall4_daily",
            "unit": "metric",
            "days": [
                {
                    "date": "2026-07-01",
                    "temp_c": 29.0,
                    "feels_like_c": 32.0,
                    "humidity": 72,
                    "uvi": 8.1,
                    "uv_available": True,
                    "weather": "Rain",
                    "weather_description": "비",
                    "rain_mm": 4.2,
                    "snow_mm": 0,
                    "precipitation_level": "medium",
                    "clouds": 90,
                }
            ],
            "missing_dates": [],
        }
        mocked_post.return_value = Mock(status_code=200, json=lambda: {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "headline": "비와 강한 자외선에 대비하세요.",
                        "summary": "낮에는 덥고 비가 올 가능성이 있습니다.",
                        "daily": [{
                            "date": "2026-07-01",
                            "summary": "비, 체감 32도, UV 높음",
                        }],
                        "alerts": ["강한 자외선", "비"],
                        "packing_notes": ["우산", "선크림"],
                    }, ensure_ascii=False)
                }
            }]
        })

        with patch.dict("os.environ", {"GMS_KEY": "test-key", "GMS_MODEL": "gpt-5-nano"}):
            response = self.client.get(f"/api/v1/trips/{self.trip.id}/weather/ai-summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["weather"]["source"], "onecall4_daily")
        self.assertEqual(response.data["ai_summary"]["headline"], "비와 강한 자외선에 대비하세요.")

        _, kwargs = mocked_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["model"], "gpt-5-nano")
        self.assertEqual(kwargs["json"]["reasoning_effort"], "low")
        user_payload = json.loads(kwargs["json"]["messages"][1]["content"])
        self.assertEqual(user_payload["trip"]["city"], "Tokyo")
        self.assertEqual(user_payload["weather"]["days"][0]["rain_mm"], 4.2)
        self.assertNotIn("clouds", user_payload["weather"]["days"][0])

    @patch("trips.weather_summary.get_trip_daily_weather")
    def test_weather_ai_summary_requires_gms_key(self, mocked_weather):
        mocked_weather.return_value = {
            "source": "onecall4_daily",
            "unit": "metric",
            "days": [],
            "missing_dates": [],
        }

        with patch.dict("os.environ", {"GMS_KEY": ""}):
            response = self.client.get(f"/api/v1/trips/{self.trip.id}/weather/ai-summary/")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["detail"], "GMS_KEY is not configured.")
