"""개발용 테스트 유저 + JWT 액세스 토큰 발급 (소셜로그인 구현 전 API 테스트용).

실행: python manage.py dev_token [사용자명]
"""

from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.dev_auth import login_or_create_dev_user


class Command(BaseCommand):
    help = "개발용 테스트 유저를 만들고 JWT 액세스 토큰을 출력한다."

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", default="dev-tester")

    def handle(self, *args, **opts):
        user, created = login_or_create_dev_user(opts["username"])
        token = RefreshToken.for_user(user)
        self.stdout.write(self.style.SUCCESS(
            f"user_id={user.id} nickname={user.nickname} ({'생성' if created else '기존'})"))
        self.stdout.write(f"ACCESS_TOKEN:\n{token.access_token}")
