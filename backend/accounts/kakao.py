import requests
from django.conf import settings

from .models import User
from .nickname import generate_unique_nickname


TOKEN_URL = "https://kauth.kakao.com/oauth/token"
USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoLoginError(Exception):
    pass


def login_with_kakao_code(code, redirect_uri):
    kakao_token = _request_token(code, redirect_uri)
    profile = _request_user_info(kakao_token["access_token"])
    return _upsert_user(profile)


def _request_token(code, redirect_uri):
    if not settings.KAKAO_API_KEY:
        raise KakaoLoginError("KAKAO_API_KEY is not configured.")

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_API_KEY,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    if settings.KAKAO_CLIENT_SECRET:
        data["client_secret"] = settings.KAKAO_CLIENT_SECRET

    response = requests.post(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        timeout=5,
    )
    if response.status_code != 200:
        raise KakaoLoginError("Failed to exchange Kakao authorization code.")
    return response.json()


def _request_user_info(access_token):
    response = requests.get(
        USER_INFO_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        timeout=5,
    )
    if response.status_code != 200:
        raise KakaoLoginError("Failed to fetch Kakao user profile.")
    return response.json()


def _upsert_user(profile):
    social_id = str(profile["id"])
    kakao_account = profile.get("kakao_account") or {}
    kakao_profile = kakao_account.get("profile") or {}
    properties = profile.get("properties") or {}
    kakao_name = kakao_profile.get("nickname") or properties.get("nickname")

    user, created = User.objects.get_or_create(
        social_provider=User.Provider.KAKAO,
        social_id=social_id,
        defaults={
            "name": kakao_name,
            "nickname": generate_unique_nickname(),
            "email": kakao_account.get("email"),
            "profile_image_url": (
                kakao_profile.get("profile_image_url") or properties.get("profile_image")
            ),
            "gender": _normalize_gender(kakao_account.get("gender")),
            "age_range": kakao_account.get("age_range"),
        },
    )
    if created:
        return user, True

    user.name = kakao_name or user.name
    user.email = kakao_account.get("email") or user.email
    user.profile_image_url = (
        kakao_profile.get("profile_image_url")
        or properties.get("profile_image")
        or user.profile_image_url
    )
    user.gender = _normalize_gender(kakao_account.get("gender")) or user.gender
    user.age_range = kakao_account.get("age_range") or user.age_range
    if not user.nickname:
        user.nickname = generate_unique_nickname()
    user.save()
    return user, False


def _normalize_gender(value):
    if value in {User.Gender.MALE, User.Gender.FEMALE}:
        return value
    return None
