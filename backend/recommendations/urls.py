from django.urls import path

from .views import (LatestTripRecommendationView, RecommendationDetailView,
                    TripRecommendationCreateView)

urlpatterns = [
    path("trips/<int:trip_id>/recommendations/",
         TripRecommendationCreateView.as_view(),
         name="trip-recommendation-create"),
    path("trips/<int:trip_id>/recommendations/latest/",
         LatestTripRecommendationView.as_view(),
         name="trip-recommendation-latest"),
    path("recommendations/<int:recommendation_id>/",
         RecommendationDetailView.as_view(),
         name="recommendation-detail"),
]
