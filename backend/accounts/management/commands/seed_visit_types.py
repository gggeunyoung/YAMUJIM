"""방문 장소 유형(VisitPlaceType) 시드.

이름이 추천 엔진의 TravelTag '여행 테마' 어휘와 정확히 일치해야 도시 태그와
매칭된다. 정규 목록만 남기고 그 외(영문 슬러그 등 깨진 행)는 제거한다(멱등).

실행: python manage.py seed_visit_types
"""

from django.core.management.base import BaseCommand

from accounts.models import VisitPlaceType

# 취향 테스트의 '방문 장소 유형' 선택지 = TravelTag '여행 테마' 부분집합(핵심 13개)
CANONICAL = [
    "미식",
    "쇼핑",
    "자연경관",
    "액티비티",
    "등산/트레킹",
    "테마파크",
    "박물관/미술관",
    "유적지/역사",
    "해변/해양",
    "야경",
    "휴양/힐링",
    "문화/예술",
    "도시",
]


class Command(BaseCommand):
    help = "VisitPlaceType을 정규 목록(여행 테마 13개)으로 시드한다."

    def handle(self, *args, **opts):
        created = 0
        for name in CANONICAL:
            _, was_created = VisitPlaceType.objects.get_or_create(name=name)
            created += int(was_created)

        removed_qs = VisitPlaceType.objects.exclude(name__in=CANONICAL)
        removed_names = list(removed_qs.values_list("name", flat=True))
        removed_qs.delete()

        self.stdout.write(self.style.SUCCESS(
            f"VisitPlaceType 시드 완료 — 총 {len(CANONICAL)}개 "
            f"(신규 {created}, 제거 {len(removed_names)}: {removed_names})"
        ))
