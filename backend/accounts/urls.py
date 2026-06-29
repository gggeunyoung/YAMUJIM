from django.urls import path

from .views import (DevLoginView, KakaoLoginUrlView, KakaoLoginView, MeView,
                    PreferenceView, VisitPlaceTypeListView)

urlpatterns = [
    path("auth/kakao/url/", KakaoLoginUrlView.as_view(), name="kakao-login-url"),
    path("auth/kakao/", KakaoLoginView.as_view(), name="kakao-login"),
    path("auth/dev/", DevLoginView.as_view(), name="dev-login"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("visit-place-types/", VisitPlaceTypeListView.as_view(), name="visit-place-types"),
    path("me/preference/", PreferenceView.as_view(), name="preference"),
]
