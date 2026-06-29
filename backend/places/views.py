from rest_framework import permissions, viewsets

from .models import City, Country
from .serializers import (CityDetailSerializer, CityListSerializer,
                          CountryDetailSerializer, CountryListSerializer)


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """국가 목록/상세 (읽기전용, 공개)."""
    queryset = Country.objects.all().order_by("id")
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        return CountryDetailSerializer if self.action == "retrieve" else CountryListSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """도시 목록/상세 (읽기전용, 공개). ?country={id} 로 국가별 필터."""
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = City.objects.select_related("country").order_by("id")
        country = self.request.query_params.get("country")
        return qs.filter(country_id=country) if country else qs

    def get_serializer_class(self):
        return CityDetailSerializer if self.action == "retrieve" else CityListSerializer
