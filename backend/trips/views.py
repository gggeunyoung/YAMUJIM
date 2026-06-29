from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Trip
from .serializers import TripSerializer
from .weather import WeatherError, get_trip_daily_weather
from .weather_summary import WeatherSummaryError, summarize_trip_weather_with_ai


class TripViewSet(viewsets.ModelViewSet):
    """내 여행 CRUD (본인 것만)."""
    serializer_class = TripSerializer
    queryset = Trip.objects.none()

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def weather(self, request, pk=None):
        try:
            return Response(get_trip_daily_weather(self.get_object()))
        except WeatherError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=["get"], url_path="weather/ai-summary")
    def weather_ai_summary(self, request, pk=None):
        try:
            return Response(summarize_trip_weather_with_ai(self.get_object()))
        except WeatherError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except WeatherSummaryError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
