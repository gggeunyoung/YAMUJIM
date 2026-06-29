from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from trips.models import Trip

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services import (DEFAULT_GEMINI_MODEL, GMS_ADVANCED_MODELS,
                       create_recommendation_for_trip)


class TripRecommendationCreateView(generics.GenericAPIView):
    serializer_class = RecommendationSerializer

    def post(self, request, trip_id):
        trip = _get_user_trip(request.user, trip_id)
        advanced_model = request.data.get("advanced_model")
        if advanced_model not in GMS_ADVANCED_MODELS:
            advanced_model = (
                DEFAULT_GEMINI_MODEL
                if request.data.get("advanced_mode") is True else None
            )
        recommendation = create_recommendation_for_trip(
            trip, advanced_model=advanced_model)
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LatestTripRecommendationView(generics.RetrieveAPIView):
    serializer_class = RecommendationSerializer

    def get_object(self):
        trip = _get_user_trip(self.request.user, self.kwargs["trip_id"])
        queryset = (
            Recommendation.objects.filter(trip=trip)
            .prefetch_related("items__item")
            .order_by("-created_at")
        )
        recommendation = queryset.first()
        if recommendation is None:
            raise generics.Http404
        return recommendation


class RecommendationDetailView(generics.RetrieveAPIView):
    serializer_class = RecommendationSerializer
    lookup_url_kwarg = "recommendation_id"

    def get_queryset(self):
        return (
            Recommendation.objects.filter(trip__user=self.request.user)
            .prefetch_related("items__item")
        )


def _get_user_trip(user, trip_id):
    return get_object_or_404(
        Trip.objects.select_related("country", "city"),
        id=trip_id,
        user=user,
    )
