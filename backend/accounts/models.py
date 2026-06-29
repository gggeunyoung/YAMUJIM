from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, social_provider, social_id, **extra):
        if not social_id:
            raise ValueError("social_id 는 필수입니다.")
        user = self.model(social_provider=social_provider, social_id=social_id, **extra)
        user.set_unusable_password()  # 소셜 로그인이라 비밀번호 미사용
        user.save(using=self._db)
        return user

    def create_superuser(self, social_provider, social_id, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(social_provider, social_id, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """소셜 로그인 사용자. 식별키 = (social_provider, social_id)."""

    class Provider(models.TextChoices):
        KAKAO = "kakao", "카카오"
        GOOGLE = "google", "구글"
        DEV = "dev", "개발"

    class Gender(models.TextChoices):
        MALE = "male", "남성"
        FEMALE = "female", "여성"

    social_provider = models.CharField(max_length=10, choices=Provider.choices)
    social_id = models.CharField(max_length=64, unique=True)  # USERNAME_FIELD, 전역 유니크
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    nickname = models.CharField(max_length=50, null=True, blank=True, unique=True)
    profile_image_url = models.URLField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, null=True, blank=True)
    age_range = models.CharField(max_length=20, null=True, blank=True)  # 카카오 age_range (레거시)
    birth_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "social_id"
    REQUIRED_FIELDS = ["social_provider"]

    def __str__(self):
        return f"{self.get_social_provider_display()}:{self.nickname or self.social_id}"


class VisitPlaceType(models.Model):
    """방문 장소 유형 (맛집/자연경관/유원지/유적지/박물관미술관/액티비티)."""
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class UserPreference(models.Model):
    """취향 정보 수집 — 5단계 척도. User 와 1:1."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="preference")
    hygiene_sensitivity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])   # 위생 민감도 1~5
    preparedness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])          # 상황 대비성 1~5
    heat_tolerance = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])        # 더위 인내 1~5
    cold_tolerance = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])        # 추위 인내 1~5
    korean_food_need = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])      # 죽어도 한식 1~5

    def __str__(self):
        return f"{self.user} 취향"


class TravelStyle(models.Model):
    """관광스타일 — 취향(UserPreference)에 포함되는 하위 그룹. 1:1."""

    class Movement(models.TextChoices):
        WALKER = "walker", "워킹맨"
        MODERATE = "moderate", "적당히"
        MINIMAL = "minimal", "걷는거 최소"

    class Consumption(models.TextChoices):
        SOUVENIR = "souvenir", "기념품"
        VALUE = "value", "가성비"
        PREMIUM = "premium", "가심비"

    class Planning(models.TextChoices):
        SPONTANEOUS = "spontaneous", "즉흥적"
        PLANNED = "planned", "계획적"

    preference = models.OneToOneField(UserPreference, on_delete=models.CASCADE,
                                      related_name="travel_style")
    movement_type = models.CharField(max_length=12, choices=Movement.choices)
    consumption_type = models.CharField(max_length=12, choices=Consumption.choices)
    planning_type = models.CharField(max_length=12, choices=Planning.choices)
    visit_place_types = models.ManyToManyField(VisitPlaceType, blank=True)  # 방문장소유형 다중선택
