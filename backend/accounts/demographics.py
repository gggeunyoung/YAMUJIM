"""생년월일 기반 나이·연령대 구간 (추천·프로필 공용)."""

from datetime import date

from django.core.exceptions import ValidationError

MIN_TRAVEL_AGE = 10
MAX_TRAVEL_AGE = 100
TOO_YOUNG_MESSAGE = "너무 어립니다. 어딜 여행을 가려고 그래요."

AGE_BRACKET_SPECS = (
    ("under_20", "20대 미만", lambda age: age < 20),
    ("early_20s", "20대 초반", lambda age: 20 <= age <= 23),
    ("mid_20s", "20대 중반", lambda age: 24 <= age <= 26),
    ("late_20s", "20대 후반", lambda age: 27 <= age <= 29),
    ("early_30s", "30대 초반", lambda age: 30 <= age <= 35),
    ("late_30s", "30대 후반", lambda age: 36 <= age <= 39),
    ("40s", "40대", lambda age: 40 <= age <= 49),
    ("50s", "50대", lambda age: 50 <= age <= 59),
    ("60_plus", "60대 이상", lambda age: age >= 60),
)


def calculate_age(birth_date, on_date=None):
    if not birth_date:
        return None
    today = on_date or date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def resolve_age_bracket(age):
    if age is None:
        return None, None
    for key, label, matcher in AGE_BRACKET_SPECS:
        if matcher(age):
            return key, label
    return None, None


def validate_travel_age(age):
    if age is None:
        raise ValidationError("생년월일을 입력해주세요.")
    if age <= 9:
        raise ValidationError(TOO_YOUNG_MESSAGE)
    if age < MIN_TRAVEL_AGE or age > MAX_TRAVEL_AGE:
        raise ValidationError(
            f"만 {MIN_TRAVEL_AGE}세 이상 {MAX_TRAVEL_AGE}세 이하만 이용할 수 있습니다."
        )


def validate_birth_date(birth_date, on_date=None):
    if not birth_date:
        raise ValidationError("생년월일을 입력해주세요.")
    today = on_date or date.today()
    if birth_date > today:
        raise ValidationError("생년월일은 오늘 이전이어야 합니다.")
    validate_travel_age(calculate_age(birth_date, on_date=today))


def traveler_profile_payload(user):
    age = calculate_age(getattr(user, "birth_date", None))
    bracket_key, bracket_label = resolve_age_bracket(age)
    gender = getattr(user, "gender", None)
    return {
        "gender": gender,
        "birth_date": (
            user.birth_date.isoformat()
            if getattr(user, "birth_date", None) else None
        ),
        "age": age,
        "age_bracket": bracket_key,
        "age_bracket_label": bracket_label,
    }


def is_profile_complete(user):
    if not user or not getattr(user, "gender", None):
        return False
    if user.gender not in {"male", "female"}:
        return False
    if not getattr(user, "birth_date", None):
        return False
    age = calculate_age(user.birth_date)
    try:
        validate_travel_age(age)
    except ValidationError:
        return False
    return True
