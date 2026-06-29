from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.demographics import (
    TOO_YOUNG_MESSAGE,
    calculate_age,
    is_profile_complete,
    resolve_age_bracket,
    validate_birth_date,
)
from accounts.models import User


class DemographicsTests(TestCase):
    def test_age_bracket_mapping(self):
        self.assertEqual(resolve_age_bracket(19), ("under_20", "20대 미만"))
        self.assertEqual(resolve_age_bracket(22), ("early_20s", "20대 초반"))
        self.assertEqual(resolve_age_bracket(25), ("mid_20s", "20대 중반"))
        self.assertEqual(resolve_age_bracket(28), ("late_20s", "20대 후반"))
        self.assertEqual(resolve_age_bracket(33), ("early_30s", "30대 초반"))
        self.assertEqual(resolve_age_bracket(38), ("late_30s", "30대 후반"))
        self.assertEqual(resolve_age_bracket(45), ("40s", "40대"))
        self.assertEqual(resolve_age_bracket(55), ("50s", "50대"))
        self.assertEqual(resolve_age_bracket(62), ("60_plus", "60대 이상"))

    def test_too_young_birth_date(self):
        birth = date.today().replace(year=date.today().year - 8)
        with self.assertRaises(ValidationError) as ctx:
            validate_birth_date(birth)
        self.assertIn(TOO_YOUNG_MESSAGE, str(ctx.exception))

    def test_valid_birth_date(self):
        birth = date.today().replace(year=date.today().year - 25)
        validate_birth_date(birth)
        self.assertEqual(calculate_age(birth), 25)


class ProfileApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            social_provider=User.Provider.KAKAO,
            social_id="profile-user",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_profile_update_enables_profile_complete(self):
        birth = date.today().replace(year=date.today().year - 24)
        response = self.client.put(
            reverse("me"),
            {"gender": "female", "birth_date": birth.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["profile_complete"])
        self.assertEqual(response.data["age_bracket"], "mid_20s")
        self.assertEqual(response.data["gender"], "female")

    def test_profile_update_rejects_too_young(self):
        birth = date.today().replace(year=date.today().year - 7)
        response = self.client.put(
            reverse("me"),
            {"gender": "male", "birth_date": birth.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(TOO_YOUNG_MESSAGE, str(response.data))

    def test_me_includes_profile_complete_false_initially(self):
        response = self.client.get(reverse("me"))
        self.assertFalse(response.data["profile_complete"])
