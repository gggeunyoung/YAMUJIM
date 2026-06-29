from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from trips.models import Trip

from .models import CommunityPost


COMPANION_LABELS = dict(Trip.Companion.choices)


def _trip_nights(trip):
    return max(0, (trip.end_date - trip.start_date).days)


def build_packing_snapshot(recommendation):
    general_items = []
    if isinstance(recommendation.notes, dict):
        general_items = recommendation.notes.get("general_items", [])

    catalog_items = []
    for row in recommendation.items.select_related("item").all():
        catalog_items.append({
            "item_id": row.item_id,
            "item_name": row.item.name,
            "category": row.category,
            "priority": row.priority,
            "reason": row.reason,
            "default_tip": row.item.default_tip,
        })

    return {
        "general_items": general_items,
        "catalog_items": catalog_items,
    }


def get_recommendation_for_user(user, recommendation_id):
    from recommendations.models import Recommendation

    return get_object_or_404(
        Recommendation.objects.filter(trip__user=user)
        .select_related("trip", "trip__country", "trip__city")
        .prefetch_related("items__item"),
        id=recommendation_id,
    )


def is_recommendation_shared(recommendation_id):
    return CommunityPost.objects.filter(recommendation_id=recommendation_id).exists()


def create_post_from_recommendation(user, recommendation_id, title, body):
    if is_recommendation_shared(recommendation_id):
        raise serializers.ValidationError(
            {"recommendation_id": "이 추천은 이미 커뮤니티에 공유되었습니다."})

    recommendation = get_recommendation_for_user(user, recommendation_id)
    trip = recommendation.trip
    nights = _trip_nights(trip)

    try:
        with transaction.atomic():
            return CommunityPost.objects.create(
                user=user,
                trip=trip,
                recommendation=recommendation,
                title=title,
                body=body,
                country_name=trip.country.name,
                city_name=trip.city.name,
                start_date=trip.start_date,
                end_date=trip.end_date,
                nights=nights,
                companion_type=trip.companion_type,
                companion_count=trip.companion_count,
                packing_snapshot=build_packing_snapshot(recommendation),
            )
    except IntegrityError:
        raise serializers.ValidationError(
            {"recommendation_id": "이 추천은 이미 커뮤니티에 공유되었습니다."})


def companion_label(value):
    return COMPANION_LABELS.get(value, value)
