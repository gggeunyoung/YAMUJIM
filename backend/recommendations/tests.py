import json
from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import TravelStyle, User, UserPreference, VisitPlaceType
from places.models import City, Country, CountryHealth, CitySafety, EnvironmentTag, TravelTag
from trips.models import Trip

from .models import Item, Recommendation
from .services import (FALLBACK_CATALOG_LIMIT, LLM_CANDIDATE_LIMIT,
                       MIN_CATALOG_ITEMS, _ask_llm_for_recommendation,
                       _ensure_minimum_catalog_rows,
                       _llm_payload, _signal_tags, build_clothing_general_items,
                       build_item_catalog, build_recommendation_context,
                       collect_candidates, fallback_general_items, fallback_rows,
                       validate_general_items, validate_llm_rows)
from .demographics import build_demographic_general_items
from .item_affinity import (dedupe_catalog_rows, filter_catalog_rows_against_general,
                            merge_general_items)


class RecommendationTestData:
    def setUp(self):
        self.user = User.objects.create_user(
            social_provider=User.Provider.KAKAO,
            social_id="kakao-1",
        )
        self.country = Country.objects.create(
            name="Japan",
            voltage="100V",
            plug_type="A",
            adapter_needed=True,
        )
        self.city = City.objects.create(
            country=self.country,
            name="Tokyo",
            latitude=35.6,
            longitude=139.7,
        )
        CountryHealth.objects.create(
            country=self.country,
            tap_water_drinkable=True,
            shower_filter_required=False,
            yellow_fever_cert_required=False,
            essential_vaccines=[],
        )
        CitySafety.objects.create(
            city=self.city,
            crime_index=30,
            safe_alone_day=80,
            safe_alone_night=70,
            emergency_contact="110",
        )
        self.hygiene = TravelTag.objects.create(tag_name="위생", tag_class="개인 성향/조건")
        self.prepared = TravelTag.objects.create(tag_name="상황대비", tag_class="환경/안전")
        self.electronics = TravelTag.objects.create(tag_name="전자기기", tag_class="개인 성향/조건")
        self.food = TravelTag.objects.create(tag_name="한식 선호", tag_class="개인 성향/조건")

        self.wipes = Item.objects.create(name="휴대용 물티슈", default_tip="손을 닦습니다.")
        self.wipes.tags.add(self.hygiene)
        self.power = Item.objects.create(name="미니 멀티콘센트", default_tip="충전에 씁니다.")
        self.power.tags.add(self.electronics, self.prepared)
        self.gochujang = Item.objects.create(name="튜브형 고추장", default_tip="한식이 필요할 때 씁니다.")
        self.gochujang.tags.add(self.food)

        preference = UserPreference.objects.create(
            user=self.user,
            hygiene_sensitivity=5,
            preparedness=4,
            heat_tolerance=3,
            cold_tolerance=3,
            korean_food_need=5,
        )
        visit_type = VisitPlaceType.objects.create(name="미식")
        style = TravelStyle.objects.create(
            preference=preference,
            movement_type=TravelStyle.Movement.MODERATE,
            consumption_type=TravelStyle.Consumption.VALUE,
            planning_type=TravelStyle.Planning.PLANNED,
        )
        style.visit_place_types.add(visit_type)

        self.trip = Trip.objects.create(
            user=self.user,
            country=self.country,
            city=self.city,
            companion_type=Trip.Companion.ALONE,
            companion_count=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 3),
            local_language_ok=False,
            accommodation_type=Trip.Accommodation.HOTEL,
        )

    def test_collect_candidates_uses_preference_and_trip_signals(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 31,
                    "feels_like_c": 33,
                    "uvi": 8,
                    "uv_source": "open_meteo",
                    "uv_available": True,
                    "clouds": 90,
                    "rain_mm": 3,
                    "precipitation_level": "medium",
                }]
            },
            "notes": [],
        }

        candidates = collect_candidates(context)
        item_ids = {candidate.item.id for candidate in candidates}

        self.assertIn(self.wipes.id, item_ids)
        self.assertIn(self.power.id, item_ids)
        self.assertIn(self.gochujang.id, item_ids)

    def test_parent_tags_expand_for_candidate_matching(self):
        west_europe = TravelTag.objects.create(tag_name="서유럽", tag_class="여행 지역")
        europe = TravelTag.objects.create(tag_name="유럽", tag_class="여행 지역")
        limestone = TravelTag.objects.create(tag_name="석회수", tag_class="환경/안전")
        weak_water = TravelTag.objects.create(tag_name="수질 취약", tag_class="환경/안전")
        self.city.environment_tags.add(
            EnvironmentTag.objects.create(tag=west_europe),
            EnvironmentTag.objects.create(tag=limestone),
        )

        rfid_wallet = Item.objects.create(name="RFID 지갑", default_tip="카드를 보호합니다.")
        rfid_wallet.tags.add(europe)
        shower_filter = Item.objects.create(name="필터 샤워기", default_tip="물 환경에 대비합니다.")
        shower_filter.tags.add(weak_water)

        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": list(self.city.environment_tags.select_related("tag")),
            "weather": None,
            "notes": [],
        }

        item_ids = {candidate.item.id for candidate in collect_candidates(context)}

        self.assertIn(rfid_wallet.id, item_ids)
        self.assertIn(shower_filter.id, item_ids)

    def test_weighted_tags_score_strong_environment_signals_higher(self):
        coin_usage = TravelTag.objects.create(tag_name="동전 사용 많음", tag_class="환경/안전")
        shopping = TravelTag.objects.create(tag_name="쇼핑", tag_class="여행 테마")
        self.city.environment_tags.add(EnvironmentTag.objects.create(tag=coin_usage))
        self.city.travel_tags.add(shopping)

        coin_wallet = Item.objects.create(name="동전 지갑", default_tip="동전을 분류합니다.")
        coin_wallet.tags.add(coin_usage)
        shopping_bag = Item.objects.create(name="쇼핑백", default_tip="쇼핑 물품을 담습니다.")
        shopping_bag.tags.add(shopping)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": list(self.city.travel_tags.all()),
            "environment_tags": list(self.city.environment_tags.select_related("tag")),
            "weather": None,
            "notes": [],
        }

        candidates = {candidate.item.id: candidate for candidate in collect_candidates(context)}

        self.assertGreater(candidates[coin_wallet.id].score,
                           candidates[shopping_bag.id].score)
        self.assertEqual(candidates[coin_wallet.id].priority, "optional")

    def test_numeric_user_preference_adds_weighted_tag_bonus(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": [],
            "weather": None,
            "notes": [],
        }

        candidates = {
            candidate.item.id: candidate
            for candidate in build_item_catalog(context)
        }

        self.assertEqual(candidates[self.gochujang.id].score, 3.5)

    def test_selected_user_preference_tags_add_default_bonus(self):
        selected_tag = TravelTag.objects.create(tag_name="custom museum", tag_class="test")
        selected_type = VisitPlaceType.objects.create(name="custom museum")
        self.user.preference.travel_style.visit_place_types.add(selected_type)
        selected_item = Item.objects.create(name="Selected preference item")
        selected_item.tags.add(selected_tag)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": [],
            "weather": None,
            "notes": [],
        }

        candidates = {
            candidate.item.id: candidate
            for candidate in build_item_catalog(context)
        }

        self.assertEqual(candidates[selected_item.id].score, 4)

    def test_weather_bonus_prioritizes_rain_uv_and_clothing_items(self):
        rain = TravelTag.objects.create(tag_name="비", tag_class="날씨")
        heavy_rain = TravelTag.objects.create(tag_name="폭우", tag_class="날씨")
        waterproof = TravelTag.objects.create(tag_name="방수 필요", tag_class="날씨")
        sunscreen_needed = TravelTag.objects.create(tag_name="선크림 필요", tag_class="날씨")
        strong_uv = TravelTag.objects.create(tag_name="강한 자외선", tag_class="날씨")
        summer_clothes = TravelTag.objects.create(tag_name="초여름 의류", tag_class="날씨")
        snow = TravelTag.objects.create(tag_name="눈", tag_class="날씨")
        cold = TravelTag.objects.create(tag_name="추위", tag_class="날씨")

        umbrella = Item.objects.create(name="우산")
        umbrella.tags.add(rain, heavy_rain, self.prepared)
        raincoat = Item.objects.create(name="경량 우비")
        raincoat.tags.add(waterproof)
        waterproof_gloves = Item.objects.create(name="방수 장갑")
        waterproof_gloves.tags.add(snow, cold)
        sunscreen = Item.objects.create(name="선크림")
        sunscreen.tags.add(sunscreen_needed, strong_uv)
        clothing = Item.objects.create(name="초여름 의류 세트")
        clothing.tags.add(summer_clothes)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 24,
                    "feels_like_c": 24,
                    "uvi": 9,
                    "rain_mm": 12,
                    "precipitation_level": "high",
                }]
            },
            "notes": [],
        }

        candidates = {
            candidate.item.id: candidate
            for candidate in build_item_catalog(context)
        }

        self.assertGreater(candidates[umbrella.id].score,
                           candidates[raincoat.id].score)
        self.assertNotIn(waterproof_gloves.id, candidates)
        self.assertGreaterEqual(candidates[sunscreen.id].score, 16)
        self.assertGreaterEqual(candidates[clothing.id].score, 11)
        self.assertEqual(build_item_catalog(context, limit=1)[0].item.id, clothing.id)

    def test_warm_weather_excludes_cold_only_catalog_items(self):
        cold_climate = TravelTag.objects.create(tag_name="한랭 기후", tag_class="환경/안전")
        cold = TravelTag.objects.create(tag_name="추위", tag_class="날씨")
        snow = TravelTag.objects.create(tag_name="눈", tag_class="날씨")
        nature = TravelTag.objects.create(tag_name="자연경관", tag_class="여행 테마")
        festival = TravelTag.objects.create(tag_name="축제", tag_class="여행 테마")
        summer_clothes = TravelTag.objects.create(tag_name="초여름 의류", tag_class="날씨")
        heavy_rain = TravelTag.objects.create(tag_name="폭우", tag_class="날씨")
        waterproof = TravelTag.objects.create(tag_name="방수 필요", tag_class="날씨")
        self.city.environment_tags.add(EnvironmentTag.objects.create(tag=cold_climate))
        self.city.travel_tags.add(nature, festival)

        hotpack = Item.objects.create(name="핫팩 및 손난로")
        hotpack.tags.add(cold, cold_climate, nature, festival)
        winter_clothes = Item.objects.create(name="한겨울 의류 세트")
        winter_clothes.tags.add(TravelTag.objects.create(tag_name="한겨울 의류", tag_class="날씨"))
        waterproof_shoes = Item.objects.create(name="방수 신발")
        waterproof_shoes.tags.add(snow, heavy_rain, waterproof)
        clothing = Item.objects.create(name="초여름 의류 세트")
        clothing.tags.add(summer_clothes)

        warm_context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": list(self.city.travel_tags.all()),
            "environment_tags": list(self.city.environment_tags.select_related("tag")),
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 24,
                    "feels_like_c": 24,
                    "uvi": 7,
                    "rain_mm": 12,
                    "precipitation_level": "high",
                }]
            },
            "notes": [],
        }
        cold_context = {**warm_context, "weather": None}

        warm_catalog = {
            candidate.item.id: candidate
            for candidate in build_item_catalog(warm_context)
        }
        stale_catalog = build_item_catalog(cold_context)
        rows = validate_llm_rows([
            {
                "item_id": hotpack.id,
                "category": "날씨 대응",
                "priority": "recommended",
                "reason": "추위 대비입니다.",
            },
        ], stale_catalog, warm_context)

        self.assertNotIn(hotpack.id, warm_catalog)
        self.assertNotIn(winter_clothes.id, warm_catalog)
        self.assertIn(waterproof_shoes.id, warm_catalog)
        self.assertIn(clothing.id, warm_catalog)
        self.assertNotIn(hotpack.id, {row["item_id"] for row in rows})

    def test_rain_weather_does_not_add_preparedness_signal(self):
        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 24,
                    "feels_like_c": 24,
                    "uvi": 3,
                    "rain_mm": 3,
                    "precipitation_level": "medium",
                }]
            },
            "notes": [],
        }

        self.assertNotIn("상황대비", _signal_tags(context))

        context["preference"] = self.user.preference
        self.user.preference.preparedness = 4
        self.assertIn("상황대비", _signal_tags(context))

    def test_build_item_catalog_excludes_zero_score_items_from_llm_payload(self):
        matched_tag = TravelTag.objects.create(tag_name="llm-match", tag_class="test")
        unmatched_tag = TravelTag.objects.create(tag_name="llm-unmatched", tag_class="test")
        matched_item = Item.objects.create(name="Matched catalog item", default_tip="Keep out")
        matched_item.tags.add(matched_tag)
        zero_item = Item.objects.create(name="Zero score item", default_tip="Keep out")
        zero_item.tags.add(unmatched_tag)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [matched_tag],
            "environment_tags": [],
            "weather": None,
            "notes": [],
        }

        catalog = build_item_catalog(context)
        payload = _llm_payload(context, catalog)
        payload_ids = {row["item_id"] for row in payload["item_catalog"]}

        self.assertIn(matched_item.id, payload_ids)
        self.assertNotIn(zero_item.id, payload_ids)
        self.assertTrue(all(row["signal_score"] > 0 for row in payload["item_catalog"]))

    def test_llm_payload_uses_top_scoring_candidate_limit(self):
        self.country.adapter_needed = False
        self.trip.country.adapter_needed = False
        self.trip.local_language_ok = True
        total_candidates = LLM_CANDIDATE_LIMIT + 3
        tags = [
            TravelTag.objects.create(tag_name=f"rank-tag-{index}", tag_class="test")
            for index in range(total_candidates)
        ]
        items = []
        for index in range(total_candidates):
            item = Item.objects.create(
                name=f"Ranked catalog item {index}",
                default_tip="Keep out",
            )
            item.tags.add(*tags[:index + 1])
            items.append(item)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": tags,
            "environment_tags": [],
            "weather": None,
            "notes": [],
        }

        catalog = build_item_catalog(context)
        payload = _llm_payload(context, catalog)
        expected_ids = [
            item.id
            for item in reversed(items[-LLM_CANDIDATE_LIMIT:])
        ]

        self.assertEqual(len(payload["item_catalog"]), LLM_CANDIDATE_LIMIT)
        self.assertEqual(
            [row["item_id"] for row in payload["item_catalog"]],
            expected_ids,
        )
        self.assertEqual(
            [row["signal_score"] for row in payload["item_catalog"]],
            list(range(total_candidates, total_candidates - LLM_CANDIDATE_LIMIT, -1)),
        )

    def test_validate_llm_rows_rejects_unknown_items_and_bad_priority(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 31,
                    "feels_like_c": 33,
                    "uvi": 8,
                    "uv_source": "open_meteo",
                    "uv_available": True,
                    "clouds": 90,
                    "rain_mm": 3,
                    "precipitation_level": "medium",
                }]
            },
            "notes": [],
        }
        candidates = collect_candidates(context)

        rows = validate_llm_rows([
            {
                "item_id": self.power.id,
                "category": "전자기기",
                "priority": "required",
                "reason": "어댑터와 충전 수요 때문입니다.",
            },
            {
                "item_id": 9999,
                "category": "전자기기",
                "priority": "required",
                "reason": "없는 아이템입니다.",
            },
            {
                "item_id": self.wipes.id,
                "category": "위생/건강",
                "priority": "must",
                "reason": "잘못된 우선순위입니다.",
            },
        ], candidates)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["item_id"], self.power.id)
        self.assertEqual(row["item_name"], self.power.name)
        self.assertEqual(row["category"], "전자기기")
        self.assertEqual(row["priority"], "recommended")
        self.assertIn("충전", row["reason"])
        self.assertGreater(len(row["reason"]), 40)

    def test_validate_llm_rows_corrects_priority_and_forces_core_items(self):
        rain = TravelTag.objects.create(tag_name="비", tag_class="날씨")
        heavy_rain = TravelTag.objects.create(tag_name="폭우", tag_class="날씨")
        snow = TravelTag.objects.create(tag_name="눈", tag_class="날씨")
        waterproof = TravelTag.objects.create(tag_name="방수 필요", tag_class="날씨")
        sunscreen_needed = TravelTag.objects.create(tag_name="선크림 필요", tag_class="날씨")
        strong_uv = TravelTag.objects.create(tag_name="강한 자외선", tag_class="날씨")
        summer_clothes = TravelTag.objects.create(tag_name="초여름 의류", tag_class="날씨")

        umbrella = Item.objects.create(name="우산")
        umbrella.tags.add(rain, heavy_rain)
        shoes = Item.objects.create(name="방수 신발")
        shoes.tags.add(snow, heavy_rain, waterproof)
        sunscreen = Item.objects.create(name="선크림")
        sunscreen.tags.add(sunscreen_needed, strong_uv)
        clothing = Item.objects.create(name="초여름 의류 세트")
        clothing.tags.add(summer_clothes)

        context = {
            "trip": self.trip,
            "preference": None,
            "style": None,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "environment_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 24,
                    "feels_like_c": 24,
                    "uvi": 9,
                    "rain_mm": 12,
                    "snow_mm": 1,
                    "weather": "Snow",
                    "weather_description": "눈",
                    "precipitation_level": "high",
                }]
            },
            "notes": [],
        }
        catalog = build_item_catalog(context)

        rows = validate_llm_rows([
            {
                "item_id": umbrella.id,
                "category": "날씨 대응",
                "priority": "optional",
                "reason": "비 예보 때문입니다.",
            },
        ], catalog, context)
        by_id = {row["item_id"]: row for row in rows}

        self.assertEqual(by_id[umbrella.id]["priority"], "required")
        self.assertIn(shoes.id, by_id)
        self.assertIn(sunscreen.id, by_id)
        self.assertIn(clothing.id, by_id)

    def test_validate_llm_rows_downgrades_heavy_items_for_light_hotel_resort(self):
        resort = TravelTag.objects.create(tag_name="휴양/힐링", tag_class="여행 테마")
        beach = TravelTag.objects.create(tag_name="해변/해양", tag_class="여행 테마")
        heavy_rain = TravelTag.objects.create(tag_name="폭우", tag_class="날씨")
        waterproof = TravelTag.objects.create(tag_name="방수 필요", tag_class="날씨")
        pickpocket = TravelTag.objects.create(tag_name="소매치기 빈번", tag_class="환경/안전")
        self.city.travel_tags.add(resort, beach)
        self.user.preference.preparedness = 1
        self.user.preference.save()

        shoes = Item.objects.create(name="방수 신발")
        shoes.tags.add(heavy_rain, waterproof)
        rfid = Item.objects.create(name="RFID 지갑")
        rfid.tags.add(pickpocket)

        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": list(self.city.travel_tags.all()) + [pickpocket],
            "environment_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 29,
                    "feels_like_c": 31,
                    "uvi": 8,
                    "rain_mm": 12,
                    "precipitation_level": "high",
                }]
            },
            "notes": [],
        }
        catalog = build_item_catalog(context)

        rows = validate_llm_rows([
            {
                "item_id": shoes.id,
                "category": "날씨 대응",
                "priority": "required",
                "reason": "폭우 대비입니다.",
            },
            {
                "item_id": rfid.id,
                "category": "안전/비상",
                "priority": "required",
                "reason": "보안 대비입니다.",
            },
        ], catalog, context)
        by_id = {row["item_id"]: row for row in rows}

        self.assertEqual(by_id[shoes.id]["priority"], "recommended")
        self.assertEqual(by_id[rfid.id]["priority"], "recommended")

    def test_fallback_rows_are_save_ready(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 31,
                    "feels_like_c": 33,
                    "uvi": 8,
                    "uv_source": "open_meteo",
                    "uv_available": True,
                    "clouds": 90,
                    "rain_mm": 3,
                    "precipitation_level": "medium",
                }]
            },
            "notes": [],
        }

        rows = fallback_rows(collect_candidates(context))

        self.assertTrue(rows)
        self.assertTrue(all(row["priority"] in {"required", "recommended", "optional"}
                            for row in rows))

    def test_fallback_general_items_excludes_clothing(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": None,
            "notes": [],
        }

        rows = fallback_general_items(context)

        self.assertTrue(rows)
        self.assertNotIn("의류", {row["category"] for row in rows})
        self.assertIn("세면도구", {row["name"] for row in rows})

    def test_build_clothing_general_items_uses_trip_days(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 31,
                    "feels_like_c": 33,
                }]
            },
            "notes": [],
        }

        rows = build_clothing_general_items(context)
        by_name = {row["name"]: row for row in rows}

        self.assertEqual(len(rows), 5)
        self.assertEqual(by_name["속옷"]["quantity"], "3벌")
        self.assertEqual(by_name["양말"]["quantity"], "3켤레")
        self.assertEqual(by_name["상의(티셔츠·셔츠)"]["quantity"], "3벌")
        self.assertIn("한여름", by_name["속옷"]["reason"])

    def test_demographic_general_items_for_female_long_trip(self):
        self.user.gender = User.Gender.FEMALE
        self.user.birth_date = date(1998, 6, 1)
        self.user.save()
        self.trip.end_date = self.trip.start_date + timedelta(days=30)
        self.trip.save()
        context = build_recommendation_context(self.trip)
        rows = build_demographic_general_items(context)
        names = {row["name"] for row in rows}
        self.assertIn("기초 화장품·스킨케어", names)
        self.assertIn("생리대·생리용품", names)
        menstrual = next(row for row in rows if row["name"] == "생리대·생리용품")
        self.assertEqual(menstrual["quantity"], "2회분")

    def test_merge_general_items_dedupes_menstrual(self):
        merged = merge_general_items(
            [{
                "name": "생리대·생리용품",
                "category": "여성 위생",
                "quantity": "2회분",
                "reason": "서버",
            }],
            [{
                "name": "생리용품 파우치",
                "category": "위생",
                "quantity": "1개",
                "reason": "LLM",
            }],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["name"], "생리대·생리용품")

    def test_filter_catalog_rows_removes_menstrual_overlap(self):
        general = [{
            "name": "생리대·생리용품",
            "category": "여성 위생",
            "quantity": "2회분",
            "reason": "서버",
        }]
        rows = filter_catalog_rows_against_general([
            {
                "item_id": 1,
                "item_name": "생리용품 파우치",
                "category": "위생/건강",
                "priority": "recommended",
                "reason": "카탈로그",
            },
            {
                "item_id": 2,
                "item_name": "우산",
                "category": "날씨 대응",
                "priority": "recommended",
                "reason": "비",
            },
        ], general)
        names = {row["item_name"] for row in rows}
        self.assertNotIn("생리용품 파우치", names)
        self.assertIn("우산", names)

    def test_merge_general_items_dedupes_toiletries(self):
        merged = merge_general_items(
            [{
                "name": "세면도구",
                "category": "위생",
                "quantity": "1세트",
                "reason": "fallback",
            }],
            [{
                "name": "미니 세면도구",
                "category": "위생",
                "quantity": "1세트",
                "reason": "LLM",
            }],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["name"], "세면도구")

    def test_merge_general_items_dedupes_razor(self):
        merged = merge_general_items(
            [{
                "name": "면도기·면도크림",
                "category": "그루밍",
                "quantity": "1세트",
                "reason": "서버",
            }],
            [{
                "name": "휴대용 면도 세트",
                "category": "그루밍",
                "quantity": "1개",
                "reason": "LLM",
            }],
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["name"], "면도기·면도크림")

    def test_dedupe_catalog_rows_removes_sunscreen_duplicates(self):
        rows = dedupe_catalog_rows([
            {"item_id": 8, "item_name": "친환경 선크림"},
            {"item_id": 46, "item_name": "SPF100선크림"},
            {"item_id": 58, "item_name": "선크림"},
            {"item_id": 59, "item_name": "우산"},
        ])
        names = [row["item_name"] for row in rows]
        self.assertEqual(len([n for n in names if "선크림" in n or "SPF" in n]), 1)
        self.assertIn("우산", names)

    def test_filter_catalog_rows_removes_beauty_case_overlap(self):
        general = [{
            "name": "기초 화장품·스킨케어",
            "category": "위생/화장",
            "quantity": "1세트",
            "reason": "서버",
        }]
        rows = filter_catalog_rows_against_general([
            {
                "item_id": 100,
                "item_name": "미니 화장품 파우치",
                "category": "위생",
                "priority": "recommended",
                "reason": "카탈로그",
            },
            {
                "item_id": 33,
                "item_name": "미니 세면도구",
                "category": "위생",
                "priority": "recommended",
                "reason": "카탈로그",
            },
        ], general)
        names = {row["item_name"] for row in rows}
        self.assertNotIn("미니 화장품 파우치", names)
        self.assertIn("미니 세면도구", names)

    def test_demographic_general_items_for_male(self):
        self.user.gender = User.Gender.MALE
        self.user.birth_date = date(1990, 3, 15)
        self.user.save()
        context = build_recommendation_context(self.trip)
        rows = build_demographic_general_items(context)
        names = {row["name"] for row in rows}
        self.assertIn("면도기·면도크림", names)

    def test_ensure_minimum_catalog_rows_backfills_from_catalog(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": None,
            "notes": [],
        }
        catalog = build_item_catalog(context)
        if len(catalog) < MIN_CATALOG_ITEMS:
            self.skipTest("catalog too small for minimum backfill test")

        sparse = validate_llm_rows([
            {
                "item_id": catalog[0].item.id,
                "category": catalog[0].category,
                "priority": "recommended",
                "reason": "테스트",
            },
        ], catalog, context)
        filled = _ensure_minimum_catalog_rows(sparse, catalog, context)

        self.assertGreaterEqual(len(filled), MIN_CATALOG_ITEMS)
        self.assertEqual(filled[0]["item_id"], catalog[0].item.id)

    def test_validate_general_items_normalizes_ai_rows(self):
        rows = validate_general_items([
            {
                "name": "상의",
                "category": "의류",
                "quantity": "4벌",
                "reason": "3일 여행에 맞춘 수량입니다.",
            },
            {"name": "상의", "category": "의류", "quantity": "99벌"},
            {
                "name": "여권",
                "category": "서류",
                "quantity": "1개",
                "reason": "출국에 필요합니다.",
            },
            {
                "name": "여행 서류 보관용 방수 파우치",
                "category": "문서/서류",
                "quantity": "1개",
                "reason": "방수 보관용입니다.",
            },
            {
                "name": "수하물 잠금장치",
                "category": "보안",
                "quantity": "1개",
                "reason": "보안용입니다.",
            },
            {
                "name": "상비약",
                "category": "안전/비상",
                "quantity": "1세트",
                "reason": "개인 의약품입니다.",
            },
            {"name": ""},
        ])

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "여권")
        self.assertEqual(rows[1]["name"], "상비약")
        self.assertGreater(len(rows[0]["reason"]), 40)
        self.assertIn("출국", rows[0]["reason"])

    def test_llm_request_uses_gms_chat_completions(self):
        context = {
            "trip": self.trip,
            "preference": self.user.preference,
            "style": self.user.preference.travel_style,
            "country_health": self.country.health,
            "city_safety": self.city.safety,
            "city_tags": [],
            "weather": {
                "days": [{
                    "date": "2026-07-01",
                    "temp_c": 31,
                    "feels_like_c": 33,
                    "uvi": 8,
                    "uv_source": "open_meteo",
                    "uv_available": True,
                    "clouds": 90,
                    "rain_mm": 3,
                    "precipitation_level": "medium",
                }]
            },
            "notes": [],
        }
        catalog = build_item_catalog(context)
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        '{"general_items":[{"name":"여권","category":"서류",'
                        '"quantity":"1개","reason":"출국에 필요합니다."}],'
                        '"catalog_items":[{"item_id":%d,"category":"전자기기",'
                        '"priority":"required","reason":"충전 수요 때문입니다."}]}'
                    ) % catalog[0].item.id
                }
            }]
        }

        with patch.dict("os.environ", {"GMS_KEY": "test-key", "GMS_MODEL": "gpt-5-nano"}):
            with patch("recommendations.services.requests.post", return_value=response) as post:
                result = _ask_llm_for_recommendation(context, catalog)

        self.assertEqual(result["catalog_items"][0]["item_id"], catalog[0].item.id)
        self.assertEqual(result["general_items"][0]["name"], "여권")
        _, kwargs = post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["model"], "gpt-5-nano")
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "developer")
        user_payload = json.loads(kwargs["json"]["messages"][1]["content"])
        self.assertIn("item_catalog", user_payload)
        self.assertNotIn("default_tip", user_payload["item_catalog"][0])
        self.assertNotIn("raw_days", user_payload["weather_summary"])
        self.assertIn("Do not include clothing", kwargs["json"]["messages"][0]["content"])
        self.assertIn("traveler.gender", kwargs["json"]["messages"][0]["content"])
        self.assertIn("traveler", user_payload)

    def test_advanced_llm_request_uses_gms_gemini_with_same_payload(self):
        context = build_recommendation_context(self.trip)
        catalog = build_item_catalog(context)
        response = Mock(status_code=200)
        response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            '{"general_items":[{"name":"여권","category":"서류",'
                            '"quantity":"1개","reason":"출국에 필요합니다."}],'
                            '"catalog_items":[{"item_id":%d,"category":"전자기기",'
                            '"priority":"recommended","reason":"충전 수요 때문입니다."}]}'
                        ) % catalog[0].item.id
                    }]
                },
            }]
        }

        with patch.dict("os.environ", {"GMS_KEY": "test-key", "GMS_MODEL": "gpt-5-nano"}):
            with patch("recommendations.services.requests.post", return_value=response) as post:
                result = _ask_llm_for_recommendation(
                    context, catalog, advanced_model="gemini-3.5-flash")

        self.assertEqual(result["catalog_items"][0]["item_id"], catalog[0].item.id)
        self.assertEqual(result["general_items"][0]["name"], "여권")
        url, = post.call_args.args
        _, kwargs = post.call_args
        self.assertIn("gemini-3.5-flash:generateContent", url)
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "test-key")
        self.assertNotIn("Authorization", kwargs["headers"])
        prompt = kwargs["json"]["contents"][0]["parts"][0]["text"]
        self.assertIn("Yamujim's travel packing recommendation engine", prompt)
        self.assertIn('"item_catalog"', prompt)
        self.assertIn('"weather_summary"', prompt)

    def test_advanced_llm_request_uses_gms_anthropic_with_same_payload(self):
        context = build_recommendation_context(self.trip)
        catalog = build_item_catalog(context)
        response = Mock(status_code=200)
        response.json.return_value = {
            "content": [{
                "type": "text",
                "text": (
                    '{"general_items":[{"name":"passport","category":"docs",'
                    '"quantity":"1","reason":"Needed for departure."}],'
                    '"catalog_items":[{"item_id":%d,"category":"electronics",'
                    '"priority":"recommended","reason":"Useful for charging."}]}'
                ) % catalog[0].item.id,
            }]
        }

        with patch.dict("os.environ", {"GMS_KEY": "test-key"}):
            with patch("recommendations.services.requests.post", return_value=response) as post:
                result = _ask_llm_for_recommendation(
                    context, catalog,
                    advanced_model="claude-haiku-4-5-20251001")

        self.assertEqual(result["catalog_items"][0]["item_id"], catalog[0].item.id)
        self.assertEqual(result["general_items"][0]["name"], "passport")
        url, = post.call_args.args
        _, kwargs = post.call_args
        self.assertIn("api.anthropic.com/v1/messages", url)
        self.assertEqual(kwargs["headers"]["x-api-key"], "test-key")
        self.assertEqual(kwargs["headers"]["anthropic-version"], "2023-06-01")
        self.assertNotIn("Authorization", kwargs["headers"])
        self.assertEqual(
            kwargs["json"]["model"], "claude-haiku-4-5-20251001")
        self.assertIn(
            "Yamujim's travel packing recommendation engine",
            kwargs["json"]["system"])
        prompt = kwargs["json"]["messages"][0]["content"]
        self.assertIn('"item_catalog"', prompt)
        self.assertIn('"weather_summary"', prompt)


class RecommendationServiceTests(RecommendationTestData, TestCase):
    pass


class RecommendationApiTests(TestCase):
    def setUp(self):
        RecommendationTestData.setUp(self)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("recommendations.services._ask_llm_for_recommendation")
    @patch("recommendations.services.get_trip_daily_weather")
    def test_create_recommendation_saves_items(self, mocked_weather, mocked_llm):
        mocked_weather.return_value = {
            "days": [{
                "date": "2026-07-01",
                "temp_c": 31,
                "feels_like_c": 33,
                "uvi": 8,
                "precipitation_level": "none",
            }]
        }
        mocked_llm.return_value = {
            "general_items": [{
                "name": "상의",
                "category": "의류",
                "quantity": "4벌",
                "reason": "3일 일정에 맞춘 수량입니다.",
            }],
            "catalog_items": [{
                "item_id": self.power.id,
                "category": "전자기기",
                "priority": "required",
                "reason": "어댑터와 충전 수요 때문입니다.",
            }],
        }

        response = self.client.post(f"/api/v1/trips/{self.trip.id}/recommendations/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Recommendation.objects.count(), 1)
        general_names = {item["name"] for item in response.data["general_items"]}
        general_categories = {item["category"] for item in response.data["general_items"]}
        self.assertIn("의류", general_categories)
        self.assertIn("속옷", general_names)
        self.assertIn("양말", general_names)
        self.assertNotIn("상의", general_names)
        self.assertGreater(len(response.data["items"]), 0)

    @patch("recommendations.services.get_trip_daily_weather")
    @patch("recommendations.services._ask_llm_for_recommendation")
    def test_create_recommendation_passes_advanced_mode(
            self, mocked_llm, mocked_weather):
        mocked_weather.return_value = {"days": []}
        mocked_llm.return_value = {
            "general_items": [{
                "name": "여권",
                "category": "서류",
                "quantity": "1개",
                "reason": "출국에 필요합니다.",
            }],
            "catalog_items": [{
                "item_id": self.power.id,
                "category": "전자기기",
                "priority": "recommended",
                "reason": "충전 수요 때문입니다.",
            }],
        }

        response = self.client.post(
            f"/api/v1/trips/{self.trip.id}/recommendations/",
            {"advanced_model": "gemini-3.5-flash"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        _, kwargs = mocked_llm.call_args
        self.assertEqual(kwargs["advanced_model"], "gemini-3.5-flash")
        self.assertIn("여권", {item["name"] for item in response.data["general_items"]})
        self.assertGreater(len(response.data["items"]), 0)

    def test_latest_recommendation_returns_404_when_empty(self):
        response = self.client.get(f"/api/v1/trips/{self.trip.id}/recommendations/latest/")

        self.assertEqual(response.status_code, 404)
