"""추천 아이템 이름 기반 유사도 그룹 — general·catalog·LLM 중복 제거."""

AFFINITY_PREFIX = "affinity:"

# 앞쪽 규칙이 우선(더 구체적인 그룹을 먼저 둠)
AFFINITY_RULES = (
    ("menstrual", ("생리",)),
    ("razor", ("면도", "쉐이빙")),
    ("sunscreen", ("선크림", "SPF", "자외선 차단")),
    ("umbrella", ("우산",)),
    ("raincoat", ("우비",)),
    ("makeup", ("메이크업",)),
    ("skincare", ("스킨케어", "기초 화장", "화장품", "클렌저", "로션", "토너", "세럼")),
    ("beauty_case", ("화장품 파우치", "뷰티 파우치", "화장 파우치")),
    ("toiletries", ("세면도구", "미니 세면", "칫솔", "치약")),
    ("documents", ("여권", "신분증", "항공권", "비자", "증명")),
    ("power_bank", ("보조 배터리", "보조배터리")),
    ("charger", ("충전기", "충전 케이블", "케이블")),
    ("power_strip", ("멀티콘센트", "멀티탭")),
    ("adapter", ("어댑터", "플러그 변환")),
    ("medicine", ("상비약", "의약", "약품", "진통", "소화제", "고산병")),
    ("hair_styler", ("고데기",)),
    ("hair_care", ("헤어팩", "드라이 샴푸", "헤어 트리트먼트")),
    ("hair_style", ("왁스", "포마드", "스타일링")),
    ("wet_wipes", ("물티슈",)),
    ("slippers", ("슬리퍼",)),
    ("sleep", ("귀마개", "안대")),
    ("lock", ("자물쇠", "잠금장치", "잠금")),
    ("anti_theft", ("도난방지", "RFID", "스트랩")),
    ("dry_bag", ("드라이백", "방수 드라이백")),
    ("phone_waterproof", ("방수 파우치", "방수케이스")),
    ("korean_food", ("고추장",)),
    ("sleep_liner", ("침낭 라이너",)),
    ("shower_filter", ("필터 샤워기", "샤워 필터")),
    ("glasses", ("돋보기", "다초점", "렌즈")),
    ("mask", ("방진 마스크", "마스크")),
    ("insect_repellent", ("모기 기피", "기피제")),
    ("towel", ("스포츠 타월", "타월")),
    ("thermos_bag", ("텀블러 백",)),
)


def item_affinity_key(name):
    text = str(name or "").strip()
    if not text:
        return text
    for key, parts in AFFINITY_RULES:
        if any(part in text for part in parts):
            return f"{AFFINITY_PREFIX}{key}"
    return text


def _collect_affinity_state(items, name_field):
    names = set()
    affinities = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get(name_field) or "").strip()
        if name:
            names.add(name)
        affinity = item_affinity_key(name)
        if affinity.startswith(AFFINITY_PREFIX):
            affinities.add(affinity)
    return names, affinities


def dedupe_rows_by_affinity(rows, name_field, blocked_names=None, blocked_affinities=None):
    if not rows:
        return rows

    blocked_names = set(blocked_names or ())
    blocked_affinities = set(blocked_affinities or ())
    seen_names = set()
    seen_affinities = set()
    result = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get(name_field) or "").strip()
        if not name or name in seen_names or name in blocked_names:
            continue
        affinity = item_affinity_key(name)
        if affinity.startswith(AFFINITY_PREFIX):
            if affinity in blocked_affinities or affinity in seen_affinities:
                continue
            seen_affinities.add(affinity)
        result.append(row)
        seen_names.add(name)

    return result


def merge_general_items(*groups):
    merged = []
    for group in groups:
        if not group:
            continue
        merged = dedupe_rows_by_affinity(
            [*merged, *group],
            name_field="name",
        )
    return merged


def dedupe_catalog_rows(rows):
    return dedupe_rows_by_affinity(rows, name_field="item_name")


def filter_catalog_rows_against_general(rows, general_items):
    if not rows:
        return rows
    blocked_names, blocked_affinities = _collect_affinity_state(general_items, "name")
    return dedupe_rows_by_affinity(
        rows,
        name_field="item_name",
        blocked_names=blocked_names,
        blocked_affinities=blocked_affinities,
    )
