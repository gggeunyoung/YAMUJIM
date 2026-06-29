from rest_framework import serializers

from .models import (City, CitySafety, Country, CountryHealth, CulturalTip,
                     EnvironmentTag, TravelTag)


class CountryHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryHealth
        exclude = ["id", "country"]


class CulturalTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CulturalTip
        fields = ["theme", "content"]


class CitySafetySerializer(serializers.ModelSerializer):
    class Meta:
        model = CitySafety
        exclude = ["id", "city"]


class TravelTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelTag
        fields = ["id", "tag_name", "tag_class"]


class EnvironmentTagSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="tag.id", read_only=True)
    tag_name = serializers.CharField(source="tag.tag_name", read_only=True)
    tag_class = serializers.CharField(source="tag.tag_class", read_only=True)

    class Meta:
        model = EnvironmentTag
        fields = ["id", "tag_name", "tag_class"]


class CountryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]


class CountryDetailSerializer(serializers.ModelSerializer):
    health = CountryHealthSerializer(read_only=True)
    cultural_tips = CulturalTipSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = ["id", "name", "voltage", "plug_type", "adapter_needed",
                  "health", "cultural_tips"]


class CityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "country", "latitude", "longitude"]


class CityDetailSerializer(serializers.ModelSerializer):
    safety = CitySafetySerializer(read_only=True)
    travel_tags = TravelTagSerializer(many=True, read_only=True)
    environment_tags = EnvironmentTagSerializer(many=True, read_only=True)

    class Meta:
        model = City
        fields = ["id", "name", "country", "latitude", "longitude", "safety",
                  "travel_tags", "environment_tags"]
