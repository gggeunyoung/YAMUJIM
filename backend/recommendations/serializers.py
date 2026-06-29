from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Recommendation, RecommendationItem


class RecommendationItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source="item.id", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    default_tip = serializers.CharField(source="item.default_tip", read_only=True)

    class Meta:
        model = RecommendationItem
        fields = ["id", "item_id", "item_name", "default_tip",
                  "category", "priority", "reason"]


class RecommendationSerializer(serializers.ModelSerializer):
    items = RecommendationItemSerializer(many=True, read_only=True)
    general_items = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = ["id", "trip", "notes", "general_items", "created_at", "items"]

    @extend_schema_field({
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "category": {"type": "string"},
                "quantity": {"type": "string"},
                "reason": {"type": "string"},
            },
        },
    })
    def get_general_items(self, obj):
        if isinstance(obj.notes, dict):
            return obj.notes.get("general_items", [])
        return []
