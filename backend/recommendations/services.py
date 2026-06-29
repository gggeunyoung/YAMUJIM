import json
import os
from dataclasses import dataclass

import requests
from django.db import transaction

from accounts.demographics import traveler_profile_payload
from accounts.models import TravelStyle
from trips.weather import WeatherError, get_trip_daily_weather

from .demographics import (build_demographic_general_items,
                           clothing_quantity_adjustments,
                           demographic_signal_tags)
from .item_affinity import (AFFINITY_PREFIX, dedupe_catalog_rows,
                            filter_catalog_rows_against_general,
                            item_affinity_key, merge_general_items)
from .models import Item, Recommendation, RecommendationItem


CATEGORIES = {
    "departure": "출국 전",
    "airport": "공항/비행",
    "accommodation": "숙소",
    "city": "도시 이동",
    "activity": "액티비티",
    "health": "위생/건강",
    "safety": "안전/비상",
    "weather": "날씨 대응",
    "food": "식사/한식",
    "electronics": "전자기기",
}

PRIORITIES = {choice.value for choice in RecommendationItem.Priority}
GMS_CHAT_COMPLETIONS_URL = (
    "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
)
GMS_GEMINI_BASE_URL = (
    "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/"
)
GMS_ANTHROPIC_MESSAGES_URL = (
    "https://gms.ssafy.io/gmsapi/api.anthropic.com/v1/messages"
)
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
GMS_GEMINI_MODELS = {
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
}
GMS_ANTHROPIC_MODELS = {
    "claude-haiku-4-5-20251001",
}
GMS_ADVANCED_MODELS = GMS_GEMINI_MODELS | GMS_ANTHROPIC_MODELS
LLM_CANDIDATE_LIMIT = 24
COLLECT_CANDIDATES_LIMIT = 45
FALLBACK_CATALOG_LIMIT = 24
MIN_CATALOG_ITEMS = 16
USER_NUMERIC_WEIGHT_FACTOR = 0.5
USER_SELECTED_TAG_WEIGHT = 3
WEATHER_TAG_WEIGHTS = {
    "봄가을 의류": 10,
    "초여름 의류": 10,
    "한여름 의류": 10,
    "한겨울 의류": 10,
    "선크림 필요": 7,
    "강한 자외선": 4,
    "비": 6,
    "폭우": 8,
    "눈": 8,
    "방수 필요": 6,
}
WEATHER_CLOTHING_TAGS = {
    "봄가을 의류",
    "초여름 의류",
    "한여름 의류",
    "한겨울 의류",
}
WARM_WEATHER_CLOTHING_TAGS = {
    "초여름 의류",
    "한여름 의류",
}
COLD_OR_SNOW_ONLY_TAGS = {
    "추위",
    "한랭 기후",
    "눈",
    "한겨울 의류",
}
COLD_CONTEXT_TAGS = {
    "자연경관",
    "축제",
    "큰 일교차",
    "방수 필요",
    "상황대비",
}
WARM_COMPATIBLE_WEATHER_TAGS = {
    "비",
    "폭우",
    "더위",
    "고온다습",
    "열대 기후",
    "강한 자외선",
    "선크림 필요",
}
COLD_OR_SNOW_ONLY_NAME_PARTS = {
    "핫팩",
    "손난로",
    "방한",
    "장갑",
    "한겨울",
    "목도리",
    "내복",
    "패딩",
}
CORE_CATALOG_ITEM_NAMES = {
    "우산",
    "방수 신발",
    "선크림",
}
GENERAL_ITEM_ALLOWED_CATEGORY_PARTS = {
    "서류",
    "문서",
    "전자",
    "충전",
    "위생",
    "세면",
    "건강",
    "의약",
    "화장",
    "그루밍",
    "여성",
}
GENERAL_ITEM_ALLOWED_NAME_PARTS = {
    "여권",
    "신분증",
    "비자",
    "항공권",
    "서류",
    "충전기",
    "케이블",
    "어댑터",
    "보조 배터리",
    "보조배터리",
    "세면",
    "칫솔",
    "치약",
    "클렌저",
    "손 소독",
    "손소독",
    "소독제",
    "상비약",
    "의약품",
    "화장",
    "메이크업",
    "스킨",
    "로션",
    "선크림",
    "면도",
    "생리",
    "그루밍",
    "왁스",
    "포마드",
    "돋보기",
    "렌즈",
}
GENERAL_ITEM_BLOCKED_CATEGORY_PARTS = {
    "보안",
    "안전",
    "비상",
    "날씨",
    "액티비티",
}
GENERAL_ITEM_BLOCKED_NAME_PARTS = {
    "방수",
    "잠금",
    "자물쇠",
    "도난",
    "보안",
    "RFID",
    "스트랩",
    "드라이백",
}
DIRECT_REQUIRED_ITEM_NAMES = {
    "우산",
    "선크림",
}
CONTEXTUAL_DOWNGRADE_NAME_PARTS = {
    "방수 신발",
    "자물쇠",
    "잠금",
    "도난",
    "RFID",
    "스트랩",
}
PRIORITY_RANK = {
    RecommendationItem.Priority.OPTIONAL: 1,
    RecommendationItem.Priority.RECOMMENDED: 2,
    RecommendationItem.Priority.REQUIRED: 3,
}
CLOTHING_GENERAL_CATEGORIES = {"의류"}
CLOTHING_GENERAL_NAME_PARTS = {
    "상의",
    "하의",
    "속옷",
    "양말",
    "잠옷",
    "티셔츠",
    "셔츠",
    "바지",
    "외투",
    "코트",
    "자켓",
    "재킷",
    "니트",
}
TAG_PARENTS = {
    "서유럽": ["유럽"],
    "동유럽": ["유럽"],
    "남유럽": ["유럽"],
    "북유럽": ["유럽"],
    "수돗물 음용 불가": ["수질 취약"],
    "석회수": ["수질 취약"],
    "소매치기 빈번": ["치안"],
    "야간 치안 주의": ["치안"],
    "고온다습": ["열대 기후"],
    "폭우": ["비", "방수 필요"],
    "눈": ["방수 필요"],
    "우기": ["열대 기후"],
    "스콜": ["우기"],
    "한랭 기후": ["추위"],
    "해양 환경": ["해변/해양"],
    "산악 지형": ["등산/트레킹"],
}
TAG_WEIGHTS = {
    "동전 사용 많음": 4,
    "수돗물 음용 불가": 4,
    "석회수": 4,
    "소매치기 빈번": 4,
    "야간 치안 주의": 4,
    "모기/해충": 4,
    "스콜": 4,
    "고지대": 4,
    "여성": 3,
    "남성": 3,
    "현금 사용 많음": 3,
    "우기": 3,
    "강한 자외선": 3,
    "고온다습": 3,
    "산악 지형": 3,
    "한랭 기후": 3,
    "건조 기후": 3,
    "해양 환경": 3,
    "큰 일교차": 2,
    "치안": 2,
    "수질 취약": 2,
    "상황대비": 2,
    "열대 기후": 2,
    "비": 2,
    "폭우": 3,
    "눈": 3,
    "방수 필요": 2,
    "선크림 필요": 2,
    "20대 미만": 2,
    "20대 초반": 2,
    "20대 중반": 2,
    "20대 후반": 2,
    "30대 초반": 2,
    "30대 후반": 2,
    "40대": 2,
    "50대": 2,
    "60대 이상": 2,
}
REQUIRED_SIGNAL_TAGS = {
    "고지대",
    "수돗물 음용 불가",
    "석회수",
    "소매치기 빈번",
    "야간 치안 주의",
}


@dataclass
class Candidate:
    item: Item
    score: float
    category: str
    priority: str
    reasons: list[str]


def create_recommendation_for_trip(trip, advanced_model=None):
    context = build_recommendation_context(trip)
    catalog = build_item_catalog(context)
    llm_result = _ask_llm_for_recommendation(
        context, catalog, advanced_model=advanced_model)
    general_items = validate_general_items(
        llm_result.get("general_items", [])) if llm_result else []
    rows = validate_llm_rows(
        llm_result.get("catalog_items", []), catalog, context) if llm_result else []
    if rows:
        rows = _ensure_minimum_catalog_rows(rows, catalog, context)
        rows = dedupe_catalog_rows(rows)

    clothing_items = build_clothing_general_items(context)
    demographic_items = build_demographic_general_items(context)
    base_general = general_items or fallback_general_items(context)
    general_items = merge_general_items(clothing_items, demographic_items, base_general)
    if rows:
        rows = filter_catalog_rows_against_general(rows, general_items)
    if not rows:
        rows = fallback_rows(collect_candidates(context), context)
        rows = dedupe_catalog_rows(rows)
        rows = filter_catalog_rows_against_general(rows, general_items)
        context["notes"].append("LLM ranking was unavailable; rule-based fallback was used.")

    with transaction.atomic():
        recommendation = Recommendation.objects.create(
            trip=trip,
            notes={
                "messages": context["notes"],
                "general_items": general_items,
                "traveler_profile": context.get("traveler"),
            },
        )
        RecommendationItem.objects.bulk_create([
            RecommendationItem(
                recommendation=recommendation,
                item_id=row["item_id"],
                category=row["category"],
                priority=row["priority"],
                reason=row["reason"],
            )
            for row in rows
        ])
    return recommendation


def build_recommendation_context(trip):
    preference = getattr(trip.user, "preference", None)
    style = getattr(preference, "travel_style", None) if preference else None
    weather = _safe_weather(trip)
    traveler = traveler_profile_payload(trip.user)

    return {
        "trip": trip,
        "user": trip.user,
        "traveler": traveler,
        "preference": preference,
        "style": style,
        "country_health": getattr(trip.country, "health", None),
        "city_safety": getattr(trip.city, "safety", None),
        "city_tags": list(trip.city.travel_tags.all()),
        "environment_tags": list(trip.city.environment_tags.select_related("tag").all()),
        "weather": weather["data"],
        "notes": weather["notes"],
    }


def collect_candidates(context):
    tag_names = _signal_tags(context)
    tag_weights = _signal_tag_weights(context)
    items = (
        Item.objects.filter(tags__tag_name__in=tag_names)
        .prefetch_related("tags")
        .distinct()
    )

    candidates = []
    for item in items:
        item_tags = {tag.tag_name for tag in item.tags.all()}
        matched = sorted(item_tags & tag_names)
        score = _tag_score(matched, tag_weights)
        if not score:
            continue
        if _should_exclude_for_weather(item, item_tags, context):
            continue
        category = _category_for(item, item_tags)
        candidates.append(Candidate(
            item=item,
            score=score,
            category=category,
            priority=_priority_for(score, matched),
            reasons=[_reason_for_tag(tag) for tag in matched],
        ))

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.item.id))
    return candidates[:COLLECT_CANDIDATES_LIMIT]


def build_item_catalog(context, limit=LLM_CANDIDATE_LIMIT):
    signal_tags = _signal_tags(context)
    tag_weights = _signal_tag_weights(context)
    catalog = []

    items = Item.objects.prefetch_related("tags").order_by("id")
    for item in items:
        item_tags = {tag.tag_name for tag in item.tags.all()}
        matched = sorted(item_tags & signal_tags)
        score = _tag_score(matched, tag_weights)
        if score <= 0:
            continue
        if _should_exclude_for_weather(item, item_tags, context):
            continue
        catalog.append(Candidate(
            item=item,
            score=score,
            category=_category_for(item, item_tags),
            priority=_priority_for(score, matched),
            reasons=(
                [_reason_for_tag(tag) for tag in matched]
                or [item.default_tip or "카탈로그 특화 아이템입니다."]
            ),
        ))

    catalog.sort(key=lambda candidate: (-candidate.score, candidate.item.id))
    return _limit_item_catalog(catalog, limit)


def _limit_item_catalog(catalog, limit):
    selected = catalog[:limit]
    clothing = next(
        (candidate for candidate in catalog if _is_weather_clothing_candidate(candidate)),
        None,
    )

    if clothing and clothing not in selected:
        if len(selected) < limit:
            selected.append(clothing)
        elif selected:
            selected[-1] = clothing
        else:
            selected = [clothing]
        selected.sort(key=lambda candidate: (-candidate.score, candidate.item.id))

    return selected


def _is_weather_clothing_candidate(candidate):
    return any(tag.tag_name in WEATHER_CLOTHING_TAGS for tag in candidate.item.tags.all())


def _should_exclude_for_weather(item, item_tags, context):
    if not context or _weather_clothing_tag(
        (context.get("weather") or {}).get("days", [])
    ) not in WARM_WEATHER_CLOTHING_TAGS:
        return False
    if not item_tags & COLD_OR_SNOW_ONLY_TAGS:
        return False
    if item_tags & WARM_COMPATIBLE_WEATHER_TAGS:
        return False
    if any(part in item.name for part in COLD_OR_SNOW_ONLY_NAME_PARTS):
        return True
    return item_tags <= (COLD_OR_SNOW_ONLY_TAGS | COLD_CONTEXT_TAGS)


def validate_llm_rows(rows, candidates, context=None):
    valid_ids = {candidate.item.id for candidate in candidates}
    candidate_by_id = {candidate.item.id: candidate for candidate in candidates}
    valid_rows = []
    seen = set()

    if not isinstance(rows, list):
        return []

    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = row.get("item_id")
        priority = row.get("priority")
        if item_id not in valid_ids or item_id in seen or priority not in PRIORITIES:
            continue
        candidate = candidate_by_id[item_id]
        if _should_exclude_for_weather(
            candidate.item, {tag.tag_name for tag in candidate.item.tags.all()}, context
        ):
            continue
        priority = _final_priority(candidate, priority, context)
        valid_rows.append({
            "item_id": item_id,
            "item_name": candidate.item.name,
            "category": row.get("category") or candidate.category,
            "priority": priority,
            "reason": _enrich_catalog_reason(row.get("reason"), candidate),
        })
        seen.add(item_id)

    for candidate in candidates:
        priority = _candidate_priority(candidate, context)
        if (
            candidate.item.id in seen
            or _should_exclude_for_weather(
                candidate.item, {tag.tag_name for tag in candidate.item.tags.all()}, context
            )
            or not _should_force_catalog_item(candidate, priority)
        ):
            continue
        valid_rows.append({
            "item_id": candidate.item.id,
            "item_name": candidate.item.name,
            "category": candidate.category,
            "priority": priority,
            "reason": _fallback_reason(candidate)[:500],
        })
        seen.add(candidate.item.id)

    return valid_rows


def _final_priority(candidate, llm_priority, context):
    candidate_priority = _candidate_priority(candidate, context)
    priority = _max_priority(llm_priority, candidate_priority)
    priority = _cap_required_priority(candidate, priority, context)
    return _adjust_priority_for_context(candidate, priority, context)


def _candidate_priority(candidate, context):
    priority = _cap_required_priority(candidate, candidate.priority, context)
    return _adjust_priority_for_context(candidate, priority, context)


def _max_priority(llm_priority, candidate_priority):
    return max(
        [llm_priority, candidate_priority],
        key=lambda priority: PRIORITY_RANK[priority],
    )


def _should_force_catalog_item(candidate, priority=None):
    priority = priority or candidate.priority
    return (
        _is_weather_clothing_candidate(candidate)
        or (
            candidate.item.name in CORE_CATALOG_ITEM_NAMES
            and priority == RecommendationItem.Priority.REQUIRED
        )
    )


def _cap_required_priority(candidate, priority, context):
    if priority != RecommendationItem.Priority.REQUIRED:
        return priority
    if _can_be_required(candidate, context):
        return priority
    return RecommendationItem.Priority.RECOMMENDED


def _can_be_required(candidate, context):
    item_tags = {tag.tag_name for tag in candidate.item.tags.all()}
    if candidate.item.name in DIRECT_REQUIRED_ITEM_NAMES:
        return True
    if candidate.item.name == "방수 신발":
        return _context_has_snow(context)
    return bool(item_tags & REQUIRED_SIGNAL_TAGS)


def _adjust_priority_for_context(candidate, priority, context):
    if not _is_light_hotel_resort_context(context):
        return priority
    if not _is_contextually_heavy_item(candidate):
        return priority
    if priority == RecommendationItem.Priority.REQUIRED:
        return RecommendationItem.Priority.RECOMMENDED
    return priority


def _is_light_hotel_resort_context(context):
    if not context:
        return False

    trip = context["trip"]
    pref = context["preference"]
    style = context["style"]
    city_tags = {tag.tag_name for tag in context.get("city_tags", [])}

    return (
        trip.accommodation_type == "hotel"
        and (pref is None or getattr(pref, "preparedness", 0) <= 2)
        and not _style_has_activity(style)
        and bool(city_tags & {"휴양/힐링", "해변/해양"})
        and not bool(city_tags & {"오지 여행", "등산/트레킹"})
        and not _has_high_safety_risk(context)
    )


def _style_has_activity(style):
    if not style:
        return False
    selected = {visit_type.name for visit_type in style.visit_place_types.all()}
    return bool(selected & {"액티비티", "등산/트레킹", "자연경관", "테마파크"})


def _has_high_safety_risk(context):
    safety = context.get("city_safety")
    if not safety:
        return False
    return (
        (safety.crime_index is not None and safety.crime_index >= 55)
        or (safety.safe_alone_night is not None and safety.safe_alone_night <= 45)
    )


def _is_contextually_heavy_item(candidate):
    name = candidate.item.name
    item_tags = {tag.tag_name for tag in candidate.item.tags.all()}
    return (
        any(part in name for part in CONTEXTUAL_DOWNGRADE_NAME_PARTS)
        or bool(item_tags & {"치안", "소매치기 빈번", "야간 치안 주의"})
    )


def _context_has_snow(context):
    if not context:
        return False
    return any(_has_snow(day) for day in (context.get("weather") or {}).get("days", []))


def _enrich_general_reason(reason, fallback="여행 기간과 일정에 맞춘 기본 준비물입니다."):
    text = str(reason or "").strip() or fallback
    if len(text) >= 80:
        return text[:500]
    extra = (
        "이번 여행 일정과 목적지 환경을 기준으로 챙기면 현지에서 불편을 줄일 수 있습니다. "
        "미리 준비해 두면 이동·숙소·관광 중 갑작스러운 구매나 대체품 찾기에 쓰는 시간을 "
        "아낄 수 있습니다."
    )
    if extra not in text:
        text = f"{text} {extra}".strip()
    return text[:500]


def validate_general_items(rows):
    valid_rows = []
    seen_names = set()
    seen_affinities = set()

    if not isinstance(rows, list):
        return []

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        category = str(row.get("category") or "기본 짐")[:30]
        if not name or name in seen_names:
            continue
        affinity = item_affinity_key(name)
        if affinity.startswith(AFFINITY_PREFIX) and affinity in seen_affinities:
            continue
        if _is_clothing_general_item(name, category):
            continue
        if not _is_allowed_general_item(name, category):
            continue
        valid_rows.append({
            "name": name[:80],
            "category": category,
            "quantity": str(row.get("quantity") or "")[:40],
            "reason": _enrich_general_reason(row.get("reason")),
        })
        seen_names.add(name)
        if affinity.startswith(AFFINITY_PREFIX):
            seen_affinities.add(affinity)
        if len(valid_rows) >= 40:
            break

    return valid_rows


def fallback_rows(candidates, context=None):
    return [
        {
            "item_id": candidate.item.id,
            "item_name": candidate.item.name,
            "category": candidate.category,
            "priority": _candidate_priority(candidate, context),
            "reason": _fallback_reason(candidate),
        }
        for candidate in candidates[:FALLBACK_CATALOG_LIMIT]
    ]


def _trip_days(trip):
    return (trip.end_date - trip.start_date).days + 1


def _clothing_quantities(days):
    if days <= 0:
        days = 1
    if days <= 4:
        return {
            "tops": days,
            "bottoms": max(2, (days + 1) // 2),
            "underwear": days,
            "socks": days,
            "pajamas": 1,
        }
    if days <= 10:
        return {
            "tops": min(days, 6),
            "bottoms": min(4, max(2, (days + 2) // 3)),
            "underwear": min(days, 7),
            "socks": min(days, 7),
            "pajamas": 1,
        }
    return {
        "tops": 7,
        "bottoms": 4,
        "underwear": 8,
        "socks": 8,
        "pajamas": 2,
    }


def build_clothing_general_items(context):
    trip = context["trip"]
    days = _trip_days(trip)
    counts = _clothing_quantities(days)
    counts = clothing_quantity_adjustments(counts, context)
    weather_days = (context.get("weather") or {}).get("days", [])
    clothing_tag = _weather_clothing_tag(weather_days)
    weather_note = ""
    if clothing_tag:
        season = clothing_tag.replace(" 의류", "")
        weather_note = f" 예상 기온({season})을 반영했습니다."
    reason_base = (
        f"{days}일 일정 기준 매일 갈아입을 수 있도록 계산한 수량입니다.{weather_note}"
    )

    return [
        {
            "name": "상의(티셔츠·셔츠)",
            "category": "의류",
            "quantity": f"{counts['tops']}벌",
            "reason": reason_base + " 겹쳐 입기·세탁 간격을 고려해 상의는 조금 여유 있게 잡았습니다.",
        },
        {
            "name": "하의(바지·치마)",
            "category": "의류",
            "quantity": f"{counts['bottoms']}벌",
            "reason": reason_base + " 하의는 상의보다 적게, 교체·세탁 주기를 감안했습니다.",
        },
        {
            "name": "속옷",
            "category": "의류",
            "quantity": f"{counts['underwear']}벌",
            "reason": reason_base,
        },
        {
            "name": "양말",
            "category": "의류",
            "quantity": f"{counts['socks']}켤레",
            "reason": reason_base,
        },
        {
            "name": "잠옷",
            "category": "의류",
            "quantity": f"{counts['pajamas']}벌",
            "reason": reason_base + " 숙소에서 입을 잠옷입니다.",
        },
    ]


def _ensure_minimum_catalog_rows(rows, catalog, context, minimum=MIN_CATALOG_ITEMS):
    target = min(minimum, len(catalog))
    if len(rows) >= target:
        return rows

    result = list(rows)
    seen = {row["item_id"] for row in result}
    for candidate in catalog:
        if len(result) >= target:
            break
        if candidate.item.id in seen:
            continue
        result.append({
            "item_id": candidate.item.id,
            "item_name": candidate.item.name,
            "category": candidate.category,
            "priority": _candidate_priority(candidate, context),
            "reason": _fallback_reason(candidate)[:500],
        })
        seen.add(candidate.item.id)
    return result


def fallback_general_items(context):
    return [
        {
            "name": "세면도구",
            "category": "위생",
            "quantity": "1세트",
            "reason": "칫솔, 치약, 클렌저 등 매일 쓰는 개인 위생용품입니다.",
        },
        {
            "name": "여권/신분증",
            "category": "서류",
            "quantity": "1개",
            "reason": "출국과 숙소 체크인에 필요한 핵심 서류입니다.",
        },
        {
            "name": "충전기",
            "category": "전자기기",
            "quantity": "1세트",
            "reason": "휴대폰과 전자기기 사용을 위한 기본 준비물입니다.",
        },
    ]


def _is_clothing_general_item(name, category):
    return (
        category in CLOTHING_GENERAL_CATEGORIES
        or any(part in name for part in CLOTHING_GENERAL_NAME_PARTS)
    )


def _is_allowed_general_item(name, category):
    if any(part in name for part in GENERAL_ITEM_BLOCKED_NAME_PARTS):
        return False
    if any(part in name for part in GENERAL_ITEM_ALLOWED_NAME_PARTS):
        return True
    if any(part in category for part in GENERAL_ITEM_BLOCKED_CATEGORY_PARTS):
        return False
    return any(part in category for part in GENERAL_ITEM_ALLOWED_CATEGORY_PARTS)


def _safe_weather(trip):
    # 날씨는 추천의 보조 신호일 뿐이라 실패해도 추천은 계속되어야 한다.
    # WeatherError 외에 날씨 API 타임아웃(requests.ReadTimeout 등)·캐시(Redis)
    # 장애도 넓게 흡수해 graceful degrade 한다(엔진은 weather=None을 견딘다).
    try:
        return {"data": get_trip_daily_weather(trip), "notes": []}
    except Exception as exc:  # noqa: BLE001 — 의도적 광범위 흡수
        return {"data": None, "notes": [f"Weather unavailable: {exc}"]}


def _signal_tags(context):
    trip = context["trip"]
    pref = context["preference"]
    style = context["style"]
    health = context["country_health"]
    safety = context["city_safety"]
    weather_days = (context["weather"] or {}).get("days", [])

    tags = {tag.tag_name for tag in context["city_tags"]}
    tags.update(env_tag.tag.tag_name for env_tag in context.get("environment_tags", []))

    tags.update(_signal_tag_weights(context).keys())

    tags.update(demographic_signal_tags(context))

    if style:
        tags.update(_style_tags(style))

    if trip.companion_type == "alone":
        tags.add("혼자 여행")
    if trip.accommodation_type == "hotel":
        tags.add("호텔/리조트")
    if trip.accommodation_type == "guesthouse":
        tags.add("호스텔")
    if trip.accommodation_type == "capsule":
        tags.update(["호스텔", "예민성"])
    if trip.country.adapter_needed:
        tags.add("전자기기")

    if health:
        if health.shower_filter_required or health.tap_water_drinkable is False:
            tags.add("수질 취약")

    if safety and (
        (safety.crime_index is not None and safety.crime_index >= 55)
        or (safety.safe_alone_night is not None and safety.safe_alone_night <= 45)
    ):
        tags.add("치안")

    tags.update(_weather_tag_weights(weather_days).keys())

    return _expand_parent_tags(tags)


def _signal_tag_weights(context):
    weights = {}
    pref = context["preference"]
    style = context["style"]

    if pref:
        for tag, weight in _preference_tag_weights(pref).items():
            _add_tag_weight(weights, tag, weight)

    if style:
        for tag in _style_tags(style):
            _add_tag_weight(weights, tag, USER_SELECTED_TAG_WEIGHT)

    for tag, weight in _weather_tag_weights(
        (context["weather"] or {}).get("days", [])
    ).items():
        _add_tag_weight(weights, tag, weight)

    for tag in demographic_signal_tags(context):
        _add_tag_weight(weights, tag, 3)

    return weights


def _weather_tag_weights(weather_days):
    weights = {}
    if not weather_days:
        return weights

    clothing_tag = _weather_clothing_tag(weather_days)
    if clothing_tag:
        _add_tag_weight(weights, clothing_tag, WEATHER_TAG_WEIGHTS[clothing_tag])

    if any(_has_rain(day) for day in weather_days):
        _add_tag_weight(weights, "비", WEATHER_TAG_WEIGHTS["비"])

    if any(_has_heavy_rain(day) for day in weather_days):
        _add_tag_weight(weights, "폭우", WEATHER_TAG_WEIGHTS["폭우"])
        _add_tag_weight(weights, "방수 필요", WEATHER_TAG_WEIGHTS["방수 필요"])

    if any(_has_snow(day) for day in weather_days):
        _add_tag_weight(weights, "눈", WEATHER_TAG_WEIGHTS["눈"])
        _add_tag_weight(weights, "방수 필요", WEATHER_TAG_WEIGHTS["방수 필요"])

    if any((day.get("uvi") or 0) >= 7 for day in weather_days):
        _add_tag_weight(weights, "선크림 필요", WEATHER_TAG_WEIGHTS["선크림 필요"])
        _add_tag_weight(weights, "강한 자외선", WEATHER_TAG_WEIGHTS["강한 자외선"])

    return weights


def _weather_clothing_tag(weather_days):
    temps = [
        day.get("feels_like_c") if day.get("feels_like_c") is not None else day.get("temp_c")
        for day in weather_days
    ]
    temps = [temp for temp in temps if temp is not None]
    if not temps:
        return None

    avg_temp = sum(temps) / len(temps)
    if avg_temp <= 5:
        return "한겨울 의류"
    if avg_temp >= 28:
        return "한여름 의류"
    if avg_temp >= 22:
        return "초여름 의류"
    return "봄가을 의류"


def _has_rain(day):
    return (
        (day.get("rain_mm") or 0) > 0
        or day.get("precipitation_level") in {"low", "medium", "high", "very_high"}
        or str(day.get("weather") or "").lower() == "rain"
    )


def _has_heavy_rain(day):
    return (
        (day.get("rain_mm") or 0) >= 10
        or day.get("precipitation_level") in {"high", "very_high"}
    )


def _has_snow(day):
    weather = str(day.get("weather") or "").lower()
    description = str(day.get("weather_description") or "")
    return (day.get("snow_mm") or 0) > 0 or "snow" in weather or "눈" in description


def _preference_tag_weights(pref):
    weights = {}

    hygiene_weight = _numeric_preference_weight(pref.hygiene_sensitivity)
    _add_tag_weight(weights, "위생", hygiene_weight)
    _add_tag_weight(weights, "예민성", hygiene_weight)

    preparedness_weight = _numeric_preference_weight(pref.preparedness)
    _add_tag_weight(weights, "상황대비", preparedness_weight)
    _add_tag_weight(weights, "계획성", preparedness_weight)

    _add_tag_weight(
        weights,
        "더위",
        _inverse_tolerance_weight(pref.heat_tolerance),
    )
    _add_tag_weight(
        weights,
        "추위",
        _inverse_tolerance_weight(pref.cold_tolerance),
    )
    _add_tag_weight(
        weights,
        "한식 선호",
        _numeric_preference_weight(pref.korean_food_need),
    )

    return weights


def _numeric_preference_weight(value):
    if value is None:
        return 0
    return max(0, float(value)) * USER_NUMERIC_WEIGHT_FACTOR


def _inverse_tolerance_weight(value):
    if value is None:
        return 0
    return max(0, 5 - float(value)) * USER_NUMERIC_WEIGHT_FACTOR


def _add_tag_weight(weights, tag, weight):
    if weight > 0:
        weights[tag] = weights.get(tag, 0) + weight


def _expand_parent_tags(tags):
    expanded = set(tags)
    pending = list(tags)

    while pending:
        tag = pending.pop()
        for parent in TAG_PARENTS.get(tag, []):
            if parent not in expanded:
                expanded.add(parent)
                pending.append(parent)

    return expanded


def _style_tags(style):
    tags = {visit_type.name for visit_type in style.visit_place_types.all()}
    if style.movement_type == TravelStyle.Movement.WALKER:
        tags.add("도보 여행")
    if style.movement_type == TravelStyle.Movement.MINIMAL:
        tags.add("도보 최소")
    if style.consumption_type == TravelStyle.Consumption.VALUE:
        tags.add("가성비")
    if style.planning_type == TravelStyle.Planning.PLANNED:
        tags.add("계획성")
    return tags


def _category_for(item, tags):
    if tags & {
        "봄가을 의류",
        "초여름 의류",
        "한여름 의류",
        "한겨울 의류",
        "선크림 필요",
        "비",
        "폭우",
        "눈",
        "방수 필요",
        "강한 자외선",
    }:
        return CATEGORIES["weather"]
    if "전자기기" in tags:
        return CATEGORIES["electronics"]
    if tags & {"위생", "예민성", "수질 취약"}:
        return CATEGORIES["health"]
    if tags & {"치안", "상황대비"}:
        return CATEGORIES["safety"]
    if tags & {"더위", "추위", "열대 기후", "사막"}:
        return CATEGORIES["weather"]
    if tags & {"호스텔", "호텔/리조트", "에어비앤비"}:
        return CATEGORIES["accommodation"]
    if tags & {"미식", "한식 선호"}:
        return CATEGORIES["food"]
    if tags & {"액티비티", "등산/트레킹", "해변/해양", "테마파크"}:
        return CATEGORIES["activity"]
    if tags & {"도보 여행", "도보 최소", "장거리 이동", "도시"}:
        return CATEGORIES["city"]
    if item.name in {"포켓 수첩과 펜", "동전 지갑"}:
        return CATEGORIES["departure"]
    return CATEGORIES["activity"]


def _priority_for(score, tags):
    if score >= 16 or any(tag in tags for tag in REQUIRED_SIGNAL_TAGS):
        return RecommendationItem.Priority.REQUIRED
    if score >= 6:
        return RecommendationItem.Priority.RECOMMENDED
    return RecommendationItem.Priority.OPTIONAL


def _tag_score(tags, extra_weights=None):
    extra_weights = extra_weights or {}
    return sum(TAG_WEIGHTS.get(tag, 1) + extra_weights.get(tag, 0) for tag in tags)


def _reason_for_tag(tag):
    reasons = {
        "위생": "위생 민감도 또는 숙소/환경 정보와 맞습니다.",
        "예민성": "소음, 공용 공간, 청결 이슈에 대비할 수 있습니다.",
        "상황대비": "예상 밖 상황에 대비하려는 성향과 여행 조건에 맞습니다.",
        "계획성": "미리 준비하면 현지에서 시행착오를 줄일 수 있습니다.",
        "더위": "더위에 약하거나 고온/강한 자외선 가능성이 있습니다.",
        "추위": "추위에 약하거나 낮은 체감온도 가능성이 있습니다.",
        "한식 선호": "한식 필요도가 높은 사용자에게 도움이 됩니다.",
        "도보 여행": "도보 이동이 많은 일정에 맞습니다.",
        "도보 최소": "이동 피로를 줄이는 데 도움이 됩니다.",
        "호스텔": "공용 시설 또는 저가 숙소 이용 시 유용합니다.",
        "호텔/리조트": "호텔/리조트 부대시설 이용 가능성을 반영했습니다.",
        "수질 취약": "목적지의 물/샤워 환경 리스크를 반영했습니다.",
        "치안": "도시 치안 또는 야간 이동 리스크를 반영했습니다.",
        "전자기기": "전압, 플러그, 충전 수요를 반영했습니다.",
    }
    return reasons.get(tag, f"{tag} 일정 또는 취향과 관련성이 높습니다.")


def _fallback_reason(candidate):
    tip = (candidate.item.default_tip or "").strip()
    tag_reason = " ".join(candidate.reasons[:2]).strip()
    if tip:
        if tag_reason and tag_reason not in tip:
            return f"{tag_reason} {tip}"[:500]
        return tip[:500]
    return tag_reason or "여행 조건과 아이템 태그가 일치합니다."


def _enrich_catalog_reason(llm_reason, candidate):
    reason = str(llm_reason or "").strip()
    tip = (candidate.item.default_tip or "").strip()
    if not reason:
        return _fallback_reason(candidate)
    if len(reason) >= 80:
        return reason[:500]

    parts = [reason]
    if tip and tip not in reason:
        parts.append(tip)
    enriched = " ".join(parts).strip()
    if len(enriched) >= 50:
        return enriched[:500]
    return _fallback_reason(candidate)


def _ask_llm_for_recommendation(context, catalog, advanced_model=None):
    api_key = os.getenv("GMS_KEY")
    if not api_key or not catalog:
        return {}
    if advanced_model:
        if advanced_model in GMS_GEMINI_MODELS:
            return _ask_gemini_for_recommendation(
                context, catalog, api_key, advanced_model)
        if advanced_model in GMS_ANTHROPIC_MODELS:
            return _ask_anthropic_for_recommendation(
                context, catalog, api_key, advanced_model)
        return {}

    try:
        response = requests.post(
            os.getenv("GMS_CHAT_COMPLETIONS_URL", GMS_CHAT_COMPLETIONS_URL),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": os.getenv("GMS_MODEL", "gpt-5-nano"),
                "reasoning_effort": os.getenv("GMS_REASONING_EFFORT", "medium"),
                "messages": [
                    {"role": "developer", "content": _system_prompt()},
                    {"role": "user", "content": json.dumps(
                        _llm_payload(context, catalog), ensure_ascii=False)},
                ],
            },
            timeout=float(os.getenv("GMS_TIMEOUT_SECONDS", "180")),
        )
        if response.status_code != 200:
            return {}

        content = response.json()["choices"][0]["message"]["content"]
        return _parse_llm_content(content)
    except (KeyError, ValueError, requests.RequestException):
        return {}


def _ask_gemini_for_recommendation(context, catalog, api_key, model):
    if model not in GMS_GEMINI_MODELS:
        return {}

    try:
        response = requests.post(
            os.getenv("GMS_GEMINI_GENERATE_CONTENT_URL", _gemini_url(model)),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    f"{_system_prompt()}\n\n"
                                    f"{json.dumps(_llm_payload(context, catalog), ensure_ascii=False)}"
                                )
                            }
                        ]
                    }
                ],
            },
            timeout=float(os.getenv("GMS_TIMEOUT_SECONDS", "180")),
        )
        if response.status_code != 200:
            return {}

        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_llm_content(content)
    except (KeyError, ValueError, requests.RequestException):
        return {}


def _gemini_url(model):
    return f"{GMS_GEMINI_BASE_URL}models/{model}:generateContent"


def _ask_anthropic_for_recommendation(context, catalog, api_key, model):
    if model not in GMS_ANTHROPIC_MODELS:
        return {}

    try:
        response = requests.post(
            os.getenv("GMS_ANTHROPIC_MESSAGES_URL", GMS_ANTHROPIC_MESSAGES_URL),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": int(os.getenv("GMS_ANTHROPIC_MAX_TOKENS", "4096")),
                "system": _system_prompt(),
                "messages": [{
                    "role": "user",
                    "content": json.dumps(
                        _llm_payload(context, catalog), ensure_ascii=False),
                }],
            },
            timeout=float(os.getenv("GMS_TIMEOUT_SECONDS", "180")),
        )
        if response.status_code != 200:
            return {}

        content_parts = response.json()["content"]
        content = "\n".join(
            part.get("text", "")
            for part in content_parts
            if part.get("type") == "text"
        )
        return _parse_llm_content(content)
    except (KeyError, ValueError, requests.RequestException):
        return {}


def _ask_llm_for_ranking(context, candidates):
    result = _ask_llm_for_recommendation(context, candidates)
    return result.get("catalog_items", result.get("items", []))


def _parse_llm_content(content):
    if isinstance(content, dict):
        return content

    text = str(content).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)


def _system_prompt():
    return (
        "Answer in Korean. You are Yamujim's travel packing recommendation engine. "
        "Recommend two groups: general packing items and specialized catalog items. "
        "Use traveler.gender and traveler.age_bracket_label as strong signals for "
        "grooming and health general_items: female travelers may need skincare/makeup "
        "and menstrual care on long trips; male travelers may need shaving/grooming. "
        "Use visit_place_types and preferences as the primary signals for food and "
        "photo gear; gender is only a soft hint there. "
        "Keep general_items focused on documents, chargers, toiletries, grooming, "
        "cosmetics, medicines, and personal hygiene. Do not create waterproof, "
        "anti-theft, security, emergency, or activity-specific gear in general_items; "
        "those must come only from item_catalog when present. "
        "Do not include clothing, socks, underwear, pajamas, or outfit quantities in "
        "general_items; the backend already computes clothing separately. "
        "Calculate practical quantities for the logged-in user's own luggage from "
        "trip_days, weather, accommodation, traveler profile, and travel context. "
        "companion_count is context, not a multiplier for personal general item quantities. "
        "Specialized catalog items must use only item_catalog item_id values. "
        "The item_catalog was prefiltered and sorted by backend tag signal_score; "
        "prioritize specialized items from these candidates, especially higher "
        "signal_score rows, while still excluding conflicts with the actual trip. "
        "Select generously from item_catalog: when it has 15 or more entries, include "
        "at least 15 catalog_items across varied categories; aim for breadth so the "
        "packing list feels complete, not minimal. "
        "Mention traveler gender/age context in catalog_items reasons when relevant. "
        "For every general_items and catalog_items reason field, write at least 2 full "
        "Korean sentences and preferably 3-4 sentences. Each reason must mention this "
        "trip's destination, dates, weather, traveler profile, or itinerary context, "
        "explain how the item will be used on the trip, and what problem it prevents. "
        "Never return one-line, keyword-only, or generic reasons. "
        "Use required only for items that would materially harm safety or trip quality "
        "if missing; otherwise prefer recommended or optional. "
        "Do not invent catalog item IDs. Do not put item_catalog names in general_items; "
        "catalog items must appear only in catalog_items. Exclude catalog items that "
        "conflict with the actual trip context. "
        "Return JSON only with this schema: "
        '{"general_items":[{"name":string,"category":string,"quantity":string,'
        '"reason":string}],"catalog_items":[{"item_id":number,"category":string,'
        '"priority":"required|recommended|optional","reason":string}]}.'
    )


def _llm_payload(context, catalog):
    trip = context["trip"]
    pref = context["preference"]
    weather_days = (context["weather"] or {}).get("days", [])
    style = context["style"]
    return {
        "task": (
            "Recommend a complete, generous packing list tailored to the traveler's "
            "gender and age bracket, plus practical general luggage quantities and "
            "many specialized items selected from item_catalog only. "
            f"When item_catalog has enough entries, select at least {MIN_CATALOG_ITEMS} "
            "catalog_items. Every reason must be at least 2 Korean sentences (3-4 preferred)."
        ),
        "trip_days": (trip.end_date - trip.start_date).days + 1,
        "traveler": context.get("traveler"),
        "trip": {
            "country": trip.country.name,
            "city": trip.city.name,
            "companion_type": trip.companion_type,
            "companion_count": trip.companion_count,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "local_language_ok": trip.local_language_ok,
            "accommodation_type": trip.accommodation_type,
        },
        "preference": {
            "hygiene_sensitivity": getattr(pref, "hygiene_sensitivity", None),
            "preparedness": getattr(pref, "preparedness", None),
            "heat_tolerance": getattr(pref, "heat_tolerance", None),
            "cold_tolerance": getattr(pref, "cold_tolerance", None),
            "korean_food_need": getattr(pref, "korean_food_need", None),
        },
        "travel_style": {
            "movement_type": getattr(style, "movement_type", None),
            "consumption_type": getattr(style, "consumption_type", None),
            "planning_type": getattr(style, "planning_type", None),
            "visit_place_types": [
                visit_type.name for visit_type in style.visit_place_types.all()
            ] if style else [],
        },
        "place_context": _place_context(context),
        "weather_summary": _weather_summary(weather_days),
        "item_catalog": [
            {
                "item_id": candidate.item.id,
                "name": candidate.item.name,
                "tags": [tag.tag_name for tag in candidate.item.tags.all()],
                "suggested_category": candidate.category,
                "signal_score": candidate.score,
                "matched_context_reasons": candidate.reasons,
            }
            for candidate in catalog
        ],
    }


def _weather_summary(days):
    if not days:
        return None

    temps = [day.get("temp_c") for day in days if day.get("temp_c") is not None]
    feels = [day.get("feels_like_c") for day in days if day.get("feels_like_c") is not None]
    uvis = [day.get("uvi") for day in days if day.get("uvi") is not None]
    rain_days = sum(
        1 for day in days
        if day.get("precipitation_level") in {"low", "medium", "high", "very_high"}
    )

    return {
        "days": len(days),
        "avg_temp_c": round(sum(temps) / len(temps), 1) if temps else None,
        "min_temp_c": min(temps) if temps else None,
        "max_temp_c": max(temps) if temps else None,
        "avg_feels_like_c": round(sum(feels) / len(feels), 1) if feels else None,
        "max_uvi": max(uvis) if uvis else None,
        "rain_days": rain_days,
    }


def _place_context(context):
    trip = context["trip"]
    health = context["country_health"]
    safety = context["city_safety"]
    return {
        "adapter_needed": trip.country.adapter_needed,
        "voltage": trip.country.voltage,
        "plug_type": trip.country.plug_type,
        "tap_water_drinkable": getattr(health, "tap_water_drinkable", None),
        "shower_filter_required": getattr(health, "shower_filter_required", None),
        "essential_vaccines": getattr(health, "essential_vaccines", []),
        "crime_index": getattr(safety, "crime_index", None),
        "safe_alone_day": getattr(safety, "safe_alone_day", None),
        "safe_alone_night": getattr(safety, "safe_alone_night", None),
        "city_tags": [tag.tag_name for tag in context["city_tags"]],
        "environment_tags": [
            env_tag.tag.tag_name for env_tag in context.get("environment_tags", [])
        ],
    }
