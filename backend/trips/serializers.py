from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import MAX_WEATHER_FORECAST_DAYS, Trip


class TripSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = Trip
        fields = ["id", "country", "country_name", "city", "city_name",
                  "companion_type", "companion_count",
                  "start_date", "end_date", "local_language_ok",
                  "accommodation_type", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        country = attrs.get("country", getattr(self.instance, "country", None))
        city = attrs.get("city", getattr(self.instance, "city", None))
        if country and city and city.country_id != country.id:
            raise serializers.ValidationError(
                {"city": "선택한 도시는 선택한 국가에 속해야 합니다."})
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end_date and end_date > timezone.localdate() + timedelta(
                days=MAX_WEATHER_FORECAST_DAYS):
            raise serializers.ValidationError(
                {"end_date": "날씨 예보는 오늘 기준 약 1.5년 뒤까지만 지원됩니다."})
        return attrs
