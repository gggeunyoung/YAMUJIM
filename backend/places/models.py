from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class KoreanJSONEncoder(DjangoJSONEncoder):
    """JSONField 한글을 \\uXXXX 이스케이프 없이 그대로 저장."""
    def __init__(self, *args, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(*args, **kwargs)


class Country(models.Model):
    name = models.CharField(max_length=50, unique=True)
    voltage = models.CharField(max_length=20, null=True, blank=True)     # 전압(V)
    plug_type = models.CharField(max_length=20, null=True, blank=True)   # 플러그 A~O형
    adapter_needed = models.BooleanField(null=True)

    def __str__(self):
        return self.name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=50)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["country", "name"], name="uniq_city_in_country")
        ]

    def __str__(self):
        return f"{self.name}({self.country.name})"


class CountryHealth(models.Model):
    """건강 (백신·식수). 국가 단위 1:1.  → data/dev_assets/health_country.json"""
    country = models.OneToOneField(Country, on_delete=models.CASCADE, related_name="health")
    tap_water_drinkable = models.BooleanField(null=True)
    shower_filter_required = models.BooleanField(null=True)
    yellow_fever_cert_required = models.BooleanField(null=True)
    essential_vaccines = models.JSONField(default=list, blank=True, encoder=KoreanJSONEncoder)  # 목적지 필수 백신만
    vaccine_note = models.CharField(max_length=255, null=True, blank=True)


class CitySafety(models.Model):
    """치안 (Numbeo). 도시 단위 1:1.  → data/dev_assets/safety_city.json"""
    city = models.OneToOneField(City, on_delete=models.CASCADE, related_name="safety")
    crime_index = models.FloatField(null=True)
    safe_alone_day = models.FloatField(null=True)
    safe_alone_night = models.FloatField(null=True)
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)


class CulturalTip(models.Model):
    """문화 팁/금기. 국가 단위 1:N.  → data/dev_assets/cultural_tips_country.json"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cultural_tips")
    theme = models.CharField(max_length=50)    # 식사예절/온천/교통 등
    content = models.TextField()


class TravelTag(models.Model):
    """태그 마스터.  → data/dev_assets/tags.csv (pk, tag_name, class)
    'class'는 파이썬 예약어라 tag_class 로 두고 DB 컬럼명만 class 로 지정."""
    tag_name = models.CharField(max_length=50, unique=True)
    tag_class = models.CharField(max_length=30, db_column="class")  # 성향/테마/환경/지역/스타일
    cities = models.ManyToManyField(City, related_name="travel_tags", blank=True)

    def __str__(self):
        return self.tag_name


class EnvironmentTag(models.Model):
    """도시 환경/지역 태그. TravelTag 마스터를 참조하고 도시 연결만 별도 관리."""
    tag = models.OneToOneField(TravelTag, on_delete=models.CASCADE,
                               related_name="environment_tag")
    cities = models.ManyToManyField(City, related_name="environment_tags", blank=True)

    def __str__(self):
        return self.tag.tag_name
