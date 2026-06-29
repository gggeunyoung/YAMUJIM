"""개발/시연용 즉시 로그인."""

import re

from django.core.exceptions import ValidationError

from .models import User

DEV_USERNAME_MAX_LENGTH = 30


def normalize_dev_username(value):
    text = str(value or "").strip()
    if not text:
        raise ValidationError("사용자명을 입력해주세요.")
    if len(text) > DEV_USERNAME_MAX_LENGTH:
        raise ValidationError(
            f"사용자명은 {DEV_USERNAME_MAX_LENGTH}글자 이하로 입력해주세요.")
    if not re.match(r"^[\w가-힣]+$", text, re.UNICODE):
        raise ValidationError("사용자명은 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.")
    return text


def dev_social_id(username):
    return f"dev-{username}"


def _unique_nickname(username, exclude_user_id=None):
    base = username[:50]
    qs = User.objects.filter(nickname=base)
    if exclude_user_id is not None:
        qs = qs.exclude(pk=exclude_user_id)
    if not qs.exists():
        return base
    for i in range(1, 1000):
        candidate = f"{base[:45]}_{i}"
        taken = User.objects.filter(nickname=candidate)
        if exclude_user_id is not None:
            taken = taken.exclude(pk=exclude_user_id)
        if not taken.exists():
            return candidate
    raise ValidationError("사용 가능한 닉네임을 만들지 못했습니다.")


def login_or_create_dev_user(username):
    username = normalize_dev_username(username)
    social_id = dev_social_id(username)
    user, created = User.objects.get_or_create(
        social_id=social_id,
        defaults={
            "social_provider": User.Provider.DEV,
            "name": username,
            "nickname": _unique_nickname(username),
        },
    )
    if not created:
        user.name = username
        update_fields = ["name"]
        if not user.nickname:
            user.nickname = _unique_nickname(username, exclude_user_id=user.pk)
            update_fields.append("nickname")
        user.save(update_fields=update_fields)
    return user, created
