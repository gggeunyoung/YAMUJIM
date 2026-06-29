from rest_framework import serializers

from .demographics import (
    calculate_age,
    is_profile_complete,
    resolve_age_bracket,
    validate_birth_date,
)
from .models import TravelStyle, User, UserPreference, VisitPlaceType
from .nickname import USER_NICKNAME_MAX_LENGTH, validate_user_nickname


class UserSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    age_bracket = serializers.SerializerMethodField()
    age_bracket_label = serializers.SerializerMethodField()
    profile_complete = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "social_provider",
            "name",
            "nickname",
            "email",
            "profile_image_url",
            "gender",
            "birth_date",
            "age_range",
            "age",
            "age_bracket",
            "age_bracket_label",
            "profile_complete",
        ]
        read_only_fields = fields

    def get_age(self, obj):
        return calculate_age(obj.birth_date)

    def get_age_bracket(self, obj):
        key, _ = resolve_age_bracket(calculate_age(obj.birth_date))
        return key

    def get_age_bracket_label(self, obj):
        _, label = resolve_age_bracket(calculate_age(obj.birth_date))
        return label

    def get_profile_complete(self, obj):
        return is_profile_complete(obj)


class ProfileUpdateSerializer(serializers.Serializer):
    gender = serializers.ChoiceField(choices=User.Gender.choices)
    birth_date = serializers.DateField()

    def validate_birth_date(self, value):
        validate_birth_date(value)
        return value


class NicknameUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=USER_NICKNAME_MAX_LENGTH)

    def validate_nickname(self, value):
        user = self.context.get("user")
        exclude_id = user.pk if user else None
        return validate_user_nickname(value, exclude_user_id=exclude_id)


class ProfileImageUpdateSerializer(serializers.Serializer):
    profile_image = serializers.ImageField()

    def validate_profile_image(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("프로필 이미지는 2MB 이하만 업로드할 수 있습니다.")
        return value


class VisitPlaceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitPlaceType
        fields = ["id", "name"]


class TravelStyleSerializer(serializers.ModelSerializer):
    visit_place_types = serializers.PrimaryKeyRelatedField(
        many=True, queryset=VisitPlaceType.objects.all(), required=False)

    class Meta:
        model = TravelStyle
        fields = ["movement_type", "consumption_type", "planning_type", "visit_place_types"]


class PreferenceSerializer(serializers.ModelSerializer):
    travel_style = TravelStyleSerializer()

    class Meta:
        model = UserPreference
        fields = ["hygiene_sensitivity", "preparedness", "heat_tolerance",
                  "cold_tolerance", "korean_food_need", "travel_style"]


class KakaoLoginSerializer(serializers.Serializer):
    code = serializers.CharField()
    redirect_uri = serializers.URLField(required=False, allow_blank=True)


class DevLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30, trim_whitespace=True)

    def validate_username(self, value):
        import re

        text = value.strip()
        if not text:
            raise serializers.ValidationError("사용자명을 입력해주세요.")
        if not re.match(r"^[\w가-힣]+$", text, re.UNICODE):
            raise serializers.ValidationError(
                "사용자명은 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.")
        return text


class KakaoLoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    is_new_user = serializers.BooleanField()
    user = UserSerializer()
