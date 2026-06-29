from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class KakaoLoginTests(TestCase):
    @override_settings(
        KAKAO_API_KEY="rest-api-key",
        KAKAO_REDIRECT_URI="http://localhost:5173/auth/kakao/callback",
    )
    def test_kakao_login_url_returns_authorize_url(self):
        response = APIClient().get(reverse("kakao-login-url"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["redirect_uri"],
            "http://localhost:5173/auth/kakao/callback",
        )

        authorize_url = urlparse(response.data["authorize_url"])
        query = parse_qs(authorize_url.query)
        self.assertEqual(authorize_url.scheme, "https")
        self.assertEqual(authorize_url.netloc, "kauth.kakao.com")
        self.assertEqual(authorize_url.path, "/oauth/authorize")
        self.assertEqual(query["client_id"], ["rest-api-key"])
        self.assertEqual(
            query["redirect_uri"],
            ["http://localhost:5173/auth/kakao/callback"],
        )
        self.assertEqual(query["response_type"], ["code"])

    @override_settings(KAKAO_API_KEY="rest-api-key", KAKAO_CLIENT_SECRET="secret")
    @patch("accounts.kakao.requests.get")
    @patch("accounts.kakao.requests.post")
    def test_kakao_login_creates_user_and_returns_jwt(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"access_token": "kakao-access-token"},
        )
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "id": 12345,
                "kakao_account": {
                    "email": "user@example.com",
                    "profile": {
                        "nickname": "야무진 여행자",
                        "profile_image_url": "https://example.com/profile.jpg",
                    },
                    "gender": "female",
                    "age_range": "20~29",
                },
            },
        )

        response = APIClient().post(
            reverse("kakao-login"),
            {
                "code": "auth-code",
                "redirect_uri": "http://localhost:5173/oauth/kakao/callback",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["is_new_user"])
        self.assertEqual(response.data["user"]["social_provider"], "kakao")
        self.assertEqual(response.data["user"]["name"], "야무진 여행자")
        self.assertTrue(response.data["user"]["nickname"].startswith("야무진 여행자_"))
        self.assertTrue(User.objects.filter(
            social_provider="kakao", social_id="12345").exists())

        token_data = mock_post.call_args.kwargs["data"]
        self.assertEqual(token_data["client_id"], "rest-api-key")
        self.assertEqual(token_data["client_secret"], "secret")


class DevLoginTests(TestCase):
    @override_settings(DEBUG=True)
    def test_dev_login_creates_user_with_username(self):
        response = APIClient().post(
            reverse("dev-login"),
            {"username": "테스터A"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_new_user"])
        self.assertEqual(response.data["user"]["name"], "테스터A")
        self.assertEqual(response.data["user"]["nickname"], "테스터A")
        self.assertFalse(response.data["user"]["profile_complete"])
        self.assertTrue(User.objects.filter(social_id="dev-테스터A").exists())

    @override_settings(DEBUG=True)
    def test_dev_login_reuses_existing_username(self):
        client = APIClient()
        first = client.post(reverse("dev-login"), {"username": "reuse"}, format="json")
        second = client.post(reverse("dev-login"), {"username": "reuse"}, format="json")
        self.assertTrue(first.data["is_new_user"])
        self.assertFalse(second.data["is_new_user"])
        self.assertEqual(User.objects.filter(social_id="dev-reuse").count(), 1)

    @override_settings(DEBUG=False)
    def test_dev_login_disabled_outside_debug(self):
        response = APIClient().post(
            reverse("dev-login"),
            {"username": "blocked"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
