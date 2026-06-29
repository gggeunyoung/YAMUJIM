from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from places.models import City, Country
from recommendations.services import create_recommendation_for_trip
from trips.models import Trip

from .models import CommunityPost

User = get_user_model()


class CommunityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            social_provider="kakao",
            social_id="u1",
            nickname="여행자1",
        )
        self.other = User.objects.create_user(
            social_provider="kakao",
            social_id="u2",
            nickname="여행자2",
        )
        country = Country.objects.create(name="일본")
        city = City.objects.create(country=country, name="도쿄")
        self.trip = Trip.objects.create(
            user=self.user,
            country=country,
            city=city,
            companion_type=Trip.Companion.FRIEND,
            companion_count=2,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 4),
            accommodation_type=Trip.Accommodation.HOTEL,
        )
        self.client.force_authenticate(self.user)

    def _create_recommendation(self):
        return create_recommendation_for_trip(self.trip)

    def _post_payload(self, recommendation):
        return {
            "recommendation_id": recommendation.id,
            "title": "도쿄 3박4일 짐 공유",
            "body": "이번 여행 짐 리스트입니다!",
        }

    def test_create_post_from_recommendation(self):
        rec = self._create_recommendation()
        res = self.client.post("/api/v1/community/posts/", self._post_payload(rec))
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["title"], "도쿄 3박4일 짐 공유")
        self.assertEqual(res.data["body"], "이번 여행 짐 리스트입니다!")
        self.assertEqual(res.data["city_name"], "도쿄")
        self.assertIn("packing_snapshot", res.data)
        self.assertTrue(CommunityPost.objects.filter(user=self.user).exists())

    def test_duplicate_share_blocked(self):
        rec = self._create_recommendation()
        payload = self._post_payload(rec)
        first = self.client.post("/api/v1/community/posts/", payload)
        self.assertEqual(first.status_code, 201)
        second = self.client.post("/api/v1/community/posts/", payload)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(CommunityPost.objects.filter(recommendation=rec).count(), 1)

    def test_share_status_endpoint(self):
        rec = self._create_recommendation()
        before = self.client.get(
            "/api/v1/community/posts/share-status/",
            {"recommendation_id": rec.id},
        )
        self.assertEqual(before.status_code, 200)
        self.assertFalse(before.data["shared"])

        post = self.client.post("/api/v1/community/posts/", self._post_payload(rec)).data
        after = self.client.get(
            "/api/v1/community/posts/share-status/",
            {"recommendation_id": rec.id},
        )
        self.assertTrue(after.data["shared"])
        self.assertEqual(after.data["post_id"], post["id"])

    def test_like_toggle(self):
        rec = self._create_recommendation()
        post = self.client.post("/api/v1/community/posts/", self._post_payload(rec)).data
        res = self.client.post(f"/api/v1/community/posts/{post['id']}/like/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["liked"])
        res2 = self.client.post(f"/api/v1/community/posts/{post['id']}/like/")
        self.assertFalse(res2.data["liked"])

    def test_comment_and_reply(self):
        rec = self._create_recommendation()
        post_id = self.client.post(
            "/api/v1/community/posts/", self._post_payload(rec)).data["id"]
        parent = self.client.post(
            f"/api/v1/community/posts/{post_id}/comments/",
            {"content": "좋은 짐 리스트네요"},
        ).data
        reply = self.client.post(
            f"/api/v1/community/posts/{post_id}/comments/",
            {"content": "감사합니다", "parent_id": parent["id"]},
        )
        self.assertEqual(reply.status_code, 201)
        nested = self.client.post(
            f"/api/v1/community/posts/{post_id}/comments/",
            {"content": "불가", "parent_id": reply.data["id"]},
        )
        self.assertEqual(nested.status_code, 400)

    def test_only_author_deletes_post(self):
        rec = self._create_recommendation()
        post_id = self.client.post(
            "/api/v1/community/posts/", self._post_payload(rec)).data["id"]
        self.client.force_authenticate(self.other)
        res = self.client.delete(f"/api/v1/community/posts/{post_id}/")
        self.assertEqual(res.status_code, 403)
