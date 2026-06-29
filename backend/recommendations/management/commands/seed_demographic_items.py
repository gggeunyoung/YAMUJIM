"""
성별·연령대 태그 및 카탈로그 아이템 시드 (재실행 안전).

실행: python manage.py seed_demographic_items
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from places.models import TravelTag
from recommendations.models import Item


DEMOGRAPHIC_TAGS = [
    ("여성", "개인 성향/조건"),
    ("남성", "개인 성향/조건"),
    ("20대 미만", "개인 성향/조건"),
    ("20대 초반", "개인 성향/조건"),
    ("20대 중반", "개인 성향/조건"),
    ("20대 후반", "개인 성향/조건"),
    ("30대 초반", "개인 성향/조건"),
    ("30대 후반", "개인 성향/조건"),
    ("40대", "개인 성향/조건"),
    ("50대", "개인 성향/조건"),
    ("60대 이상", "개인 성향/조건"),
]

DEMOGRAPHIC_ITEMS = [
    (
        "휴대용 면도 세트",
        "남성, 위생",
        "공용 숙소·장기 이동 시 면도 루틴을 유지할 수 있습니다.",
    ),
    (
        "미니 화장품 파우치",
        "여성, 위생",
        "기초 스킨케어·메이크업을 한곳에 모아 챙기기 좋습니다.",
    ),
    (
        "휴대용 헤어 고데기",
        "여성, 전자기기",
        "장기 여행·습한 기후에서 헤어 스타일을 정리할 때 유용합니다.",
    ),
    (
        "생리용품 파우치",
        "여성, 위생",
        "장기 여행 시 생리 주기에 대비한 위생용품 보관·휴대용입니다.",
    ),
]


class Command(BaseCommand):
    help = "성별·연령대 추천용 TravelTag 및 Item 시드"

    @transaction.atomic
    def handle(self, *args, **options):
        tag_by_name = {}
        for name, tag_class in DEMOGRAPHIC_TAGS:
            tag, _ = TravelTag.objects.update_or_create(
                tag_name=name,
                defaults={"tag_class": tag_class},
            )
            tag_by_name[name] = tag

        for name, tag_csv, tip in DEMOGRAPHIC_ITEMS:
            item, _ = Item.objects.update_or_create(
                name=name,
                defaults={"default_tip": tip},
            )
            tag_names = [part.strip() for part in tag_csv.split(",") if part.strip()]
            item.tags.set([tag_by_name[t] for t in tag_names if t in tag_by_name])

        self.stdout.write(self.style.SUCCESS(
            f"Demographic tags={len(DEMOGRAPHIC_TAGS)}, items={len(DEMOGRAPHIC_ITEMS)} seeded."
        ))
