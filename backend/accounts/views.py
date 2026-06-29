from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .dev_auth import login_or_create_dev_user
from .kakao import KakaoLoginError, login_with_kakao_code
from .models import TravelStyle, User, UserPreference, VisitPlaceType
from .serializers import (DevLoginSerializer, KakaoLoginResponseSerializer,
                          KakaoLoginSerializer, NicknameUpdateSerializer,
                          PreferenceSerializer, ProfileImageUpdateSerializer,
                          ProfileUpdateSerializer, UserSerializer,
                          VisitPlaceTypeSerializer)

KAKAO_AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"


def _issue_tokens(user, created):
    """로그인 성공 시 공통 응답: 서비스 JWT + 신규여부 + 유저정보."""
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new_user": created,
        "user": UserSerializer(user).data,
    })


class KakaoLoginUrlView(APIView):
    """GET /api/v1/auth/kakao/url/ — 프론트가 띄울 카카오 인가 URL을 내려준다.

    REST API 키/redirect_uri를 백엔드 .env 한 곳에서만 관리하기 위함.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        if not settings.KAKAO_API_KEY:
            return Response({"detail": "KAKAO_API_KEY is not configured."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not settings.KAKAO_REDIRECT_URI:
            return Response({"detail": "KAKAO_REDIRECT_URI is not configured."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        params = {
            "client_id": settings.KAKAO_API_KEY,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
        }
        return Response({
            "authorize_url": f"{KAKAO_AUTHORIZE_URL}?{urlencode(params)}",
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
        })


class KakaoLoginView(APIView):
    """POST /api/v1/auth/kakao/ 카카오 인가 코드로 서비스 JWT 발급."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        request=KakaoLoginSerializer,
        responses={200: KakaoLoginResponseSerializer},
    )
    def post(self, request):
        serializer = KakaoLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        redirect_uri = serializer.validated_data.get("redirect_uri") or settings.KAKAO_REDIRECT_URI
        if not redirect_uri:
            return Response(
                {"redirect_uri": "redirect_uri is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user, created = login_with_kakao_code(
                serializer.validated_data["code"], redirect_uri)
        except KakaoLoginError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return _issue_tokens(user, created)


class DevLoginView(APIView):
    """POST /api/v1/auth/dev/ — 개발/시연용 사용자명 즉시 로그인 (DEBUG 전용)."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=DevLoginSerializer, responses={200: KakaoLoginResponseSerializer})
    def post(self, request):
        if not settings.DEBUG:
            return Response({"detail": "dev login is disabled."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = DevLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, created = login_or_create_dev_user(serializer.validated_data["username"])
        return _issue_tokens(user, created)


class MeView(APIView):
    """GET/PUT/PATCH /api/v1/auth/me/ — 내 정보·프로필·닉네임."""

    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses={200: UserSerializer})
    def put(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        user.gender = data["gender"]
        user.birth_date = data["birth_date"]
        user.save(update_fields=["gender", "birth_date"])
        return Response(UserSerializer(user).data)

    @extend_schema(request=NicknameUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request):
        if "profile_image" in request.FILES:
            serializer = ProfileImageUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            image = serializer.validated_data["profile_image"]
            ext = image.name.rsplit(".", 1)[-1].lower() if "." in image.name else "jpg"
            path = f"profile_images/{request.user.pk}/{uuid4().hex}.{ext}"
            saved_path = default_storage.save(path, image)
            user = request.user
            user.profile_image_url = request.build_absolute_uri(default_storage.url(saved_path))
            user.save(update_fields=["profile_image_url"])
            return Response(UserSerializer(user).data)

        serializer = NicknameUpdateSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.nickname = serializer.validated_data["nickname"]
        user.save(update_fields=["nickname"])
        return Response(UserSerializer(user).data)


class VisitPlaceTypeListView(APIView):
    """GET /api/v1/visit-place-types/ — 취향 테스트의 방문 장소 유형 선택지."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: VisitPlaceTypeSerializer(many=True)})
    def get(self, request):
        qs = VisitPlaceType.objects.all().order_by("id")
        return Response(VisitPlaceTypeSerializer(qs, many=True).data)


class PreferenceView(APIView):
    """GET/PUT /api/v1/me/preference/ — 취향+관광스타일 조회/저장(upsert)."""

    @extend_schema(responses={200: PreferenceSerializer})
    def get(self, request):
        pref = UserPreference.objects.filter(user=request.user).first()
        if pref is None:
            return Response(None)
        return Response(PreferenceSerializer(pref).data)

    @extend_schema(request=PreferenceSerializer, responses={200: PreferenceSerializer})
    def put(self, request):
        ser = PreferenceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        style_data = data.pop("travel_style")
        visit_types = style_data.pop("visit_place_types", [])

        pref, _ = UserPreference.objects.update_or_create(
            user=request.user, defaults=data)
        style, _ = TravelStyle.objects.update_or_create(
            preference=pref, defaults=style_data)
        style.visit_place_types.set(visit_types)

        return Response(PreferenceSerializer(pref).data)
