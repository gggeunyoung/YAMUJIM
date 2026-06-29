"""서비스 닉네임 자동 생성·검증."""

import random
import re

from django.core.exceptions import ValidationError

NICKNAME_PREFIX = "야무진 여행자_"
USER_NICKNAME_MAX_LENGTH = 10


def generate_unique_nickname():
    for _ in range(200):
        candidate = f"{NICKNAME_PREFIX}{random.randint(0, 9999):04d}"
        if not _nickname_exists(candidate):
            return candidate
    while True:
        candidate = f"{NICKNAME_PREFIX}{random.randint(10000, 999999)}"
        if not _nickname_exists(candidate):
            return candidate


def validate_user_nickname(value, *, exclude_user_id=None):
    text = str(value or "").strip()
    if not text:
        raise ValidationError("닉네임을 입력해주세요.")
    if len(text) > USER_NICKNAME_MAX_LENGTH:
        raise ValidationError(
            f"닉네임은 {USER_NICKNAME_MAX_LENGTH}글자 이하로 입력해주세요.")
    if not re.match(r"^[\w가-힣]+$", text, re.UNICODE):
        raise ValidationError("닉네임은 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.")
    if _nickname_exists(text, exclude_user_id=exclude_user_id):
        raise ValidationError("이미 사용 중인 닉네임입니다.")
    return text


def _nickname_exists(nickname, exclude_user_id=None):
    from .models import User

    qs = User.objects.filter(nickname=nickname)
    if exclude_user_id is not None:
        qs = qs.exclude(pk=exclude_user_id)
    return qs.exists()
