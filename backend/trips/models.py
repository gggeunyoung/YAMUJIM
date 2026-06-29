from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


MAX_WEATHER_FORECAST_DAYS = 548


class Trip(models.Model):
    """여행 정보 수집."""

    class Companion(models.TextChoices):
        ALONE = "alone", "혼자"
        FRIEND = "friend", "친구"
        FAMILY = "family", "가족"
        COUPLE = "couple", "연인"
        SEEKING = "seeking", "동행 구함"

    class Accommodation(models.TextChoices):
        HOTEL = "hotel", "호텔/리조트/아파트"
        GUESTHOUSE = "guesthouse", "게스트하우스/호스텔"
        CAPSULE = "capsule", "캡슐호텔"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="trips")
    country = models.ForeignKey("places.Country", on_delete=models.PROTECT)
    city = models.ForeignKey("places.City", on_delete=models.PROTECT)
    companion_type = models.CharField(max_length=10, choices=Companion.choices)
    companion_count = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    local_language_ok = models.BooleanField(default=False)
    accommodation_type = models.CharField(max_length=12, choices=Accommodation.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.city_id and self.country_id and self.city.country_id != self.country_id:
            raise ValidationError({"city": "선택한 도시는 선택한 국가에 속해야 합니다."})
        if self.end_date and self.end_date > timezone.localdate() + timedelta(
                days=MAX_WEATHER_FORECAST_DAYS):
            raise ValidationError({"end_date": "날씨 예보는 오늘 기준 약 1.5년 뒤까지만 지원됩니다."})

    def __str__(self):
        return f"{self.user} → {self.city} ({self.start_date}~{self.end_date})"
