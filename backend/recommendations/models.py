from django.db import models

from places.models import KoreanJSONEncoder


class Item(models.Model):
    """준비물 마스터.  → data/dev_assets/items.csv (item_id, item_name, related_tags, default_tip)"""
    name = models.CharField(max_length=100, unique=True)
    default_tip = models.TextField(null=True, blank=True)  # 준비 이유/팁
    tags = models.ManyToManyField("places.TravelTag", related_name="items", blank=True)  # related_tags

    def __str__(self):
        return self.name


class Recommendation(models.Model):
    """Trip 1건에 대한 추천 결과(스냅샷)."""
    trip = models.ForeignKey("trips.Trip", on_delete=models.CASCADE, related_name="recommendations")
    notes = models.JSONField(default=list, blank=True, encoder=KoreanJSONEncoder)  # 안내사항 배열
    created_at = models.DateTimeField(auto_now_add=True)


class RecommendationItem(models.Model):
    """추천에 포함된 개별 준비물 + 챙겨야 하는 근거 (LLM 결과)."""

    class Priority(models.TextChoices):
        REQUIRED = "required", "필수"
        RECOMMENDED = "recommended", "권장"
        OPTIONAL = "optional", "선택"

    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE,
                                       related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    category = models.CharField(max_length=30, blank=True)
    priority = models.CharField(max_length=12, choices=Priority.choices)
    reason = models.TextField()  # 챙겨야 하는 근거

    def __str__(self):
        return f"{self.recommendation_id} - {self.item.name}"
