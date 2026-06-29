"""성별·연령대 기반 general_items (서버 확정 룰)."""

from accounts.models import User

LONG_TRIP_DAYS = 28

GENDER_TAG_LABELS = {
    User.Gender.FEMALE: "여성",
    User.Gender.MALE: "남성",
}


def _long_trip_menstrual_cycles(days):
    return max(1, min(3, (days + 27) // 28))


def demographic_signal_tags(context):
    profile = context.get("traveler") or {}
    tags = set()
    gender = profile.get("gender")
    if gender in GENDER_TAG_LABELS:
        tags.add(GENDER_TAG_LABELS[gender])
    label = profile.get("age_bracket_label")
    if label:
        tags.add(label)
    return tags


def build_demographic_general_items(context):
    profile = context.get("traveler") or {}
    gender = profile.get("gender")
    age = profile.get("age")
    bracket_label = profile.get("age_bracket_label") or "여행자"
    days = _trip_days(context)
    items = []

    if gender == User.Gender.FEMALE:
        items.extend(_female_items(days, bracket_label))
    elif gender == User.Gender.MALE:
        items.extend(_male_items(days, bracket_label))

    if age is not None:
        items.extend(_age_items(age, bracket_label, days))

    return items


def _female_items(days, bracket_label):
    rows = [
        {
            "name": "기초 화장품·스킨케어",
            "category": "위생/화장",
            "quantity": "1세트",
            "reason": (
                f"{bracket_label} 여성 여행자 기준, 세안·기초 스킨케어·선크림 등 "
                "매일 쓰는 뷰티 필수품입니다. 파우치·미니 화장품 세트는 여기에 포함해 챙기면 됩니다."
            ),
        },
        {
            "name": "미니 메이크업 키트",
            "category": "위생/화장",
            "quantity": "1세트",
            "reason": "현지 일정·사진·외출 시 간단히 손볼 수 있는 메이크업 준비물입니다.",
        },
    ]
    if days >= LONG_TRIP_DAYS:
        cycles = _long_trip_menstrual_cycles(days)
        rows.append({
            "name": "생리대·생리용품",
            "category": "여성 위생",
            "quantity": f"{cycles}회분",
            "reason": (
                f"{days}일 장기 여행 기준, 생리 주기에 대비한 필수 위생용품입니다. "
                "보관용 파우치는 이 항목에 포함해 챙기면 됩니다."
            ),
        })
    return rows


def _male_items(days, bracket_label):
    return [
        {
            "name": "면도기·면도크림",
            "category": "그루밍",
            "quantity": "1세트",
            "reason": (
                f"{bracket_label} 남성 여행자 기준, 일상 그루밍용 필수품입니다. "
                "휴대용 면도 세트는 이 항목에 포함해 챙기면 됩니다."
            ),
        },
        {
            "name": "스타일링 왁스·포마드(선택)",
            "category": "그루밍",
            "quantity": "1개",
            "reason": "머리 스타일 유지가 필요할 때 쓰는 소형 그루밍용품입니다.",
        },
    ]


def _age_items(age, bracket_label, days):
    rows = []
    if age >= 60:
        rows.append({
            "name": "돋보기·다초점 렌즈(선택)",
            "category": "건강",
            "quantity": "1개",
            "reason": f"{bracket_label} 여행자에게 현지 메뉴·표지판 확인에 도움이 됩니다.",
        })
        rows.append({
            "name": "관절·소화 보조 상비약",
            "category": "건강/의약",
            "quantity": "1세트",
            "reason": "장시간 이동·식습관 변화에 대비한 연령 맞춤 상비약입니다.",
        })
    elif age >= 50:
        rows.append({
            "name": "개인 상비약(혈압·소화)",
            "category": "건강/의약",
            "quantity": "1세트",
            "reason": f"{bracket_label} 여행자 기준, 평소 복용약과 소화제를 여분으로 챙기세요.",
        })
    elif age < 20:
        rows.append({
            "name": "학생증·할인 신분증",
            "category": "서류",
            "quantity": "1개",
            "reason": "현지 박물관·교통 할인 혜택 확인용 신분증입니다.",
        })
    return rows


def clothing_quantity_adjustments(counts, context):
    profile = context.get("traveler") or {}
    gender = profile.get("gender")
    if gender == User.Gender.FEMALE:
        counts["tops"] = min(counts["tops"] + 1, counts.get("underwear", counts["tops"]) + 2)
        counts["bottoms"] = min(counts["bottoms"] + 1, 5)
    return counts


def _trip_days(context):
    trip = context.get("trip")
    if not trip:
        return 1
    return (trip.end_date - trip.start_date).days + 1
