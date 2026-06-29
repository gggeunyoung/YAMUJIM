"""
data/dev_assets 의 CSV/JSON → DB 적재.
재실행 안전(update_or_create). CSV/JSON의 id를 PK로 그대로 사용해 FK가 맞물리게 함.

실행: python manage.py seed_data
"""

import csv
import json
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from places.models import (City, CitySafety, Country, CountryHealth, CulturalTip,
                           EnvironmentTag, TravelTag)
from recommendations.models import Item

DATA = settings.BASE_DIR.parent / "data" / "dev_assets"
GEN = settings.BASE_DIR.parent / "data" / "generate_data"
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CACHE_PATH = DATA / "city_coordinates.json"
ENVIRONMENT_TAG_NAMES = {
    "동북아", "서유럽", "동유럽", "남유럽", "북유럽", "북미", "오세아니아",
    "태평양 휴양지", "도서 지역", "지중해", "고온다습", "강한 자외선", "우기",
    "스콜", "한랭 기후", "큰 일교차", "건조 기후", "해양 환경", "산악 지형",
    "소매치기 빈번", "야간 치안 주의", "현금 사용 많음", "동전 사용 많음",
    "수돗물 음용 불가", "석회수", "모기/해충",
}
COUNTRY_CODES = {
    1: "JP",
    2: "VN",
    3: "TH",
    4: "US",
    5: "PH",
    6: "TW",
    7: "GU",
    8: "SG",
    9: "HK",
    10: "IT",
    11: "FR",
    12: "ES",
    13: "GB",
    14: "CH",
    15: "DE",
    16: "MY",
    17: "AU",
    18: "CA",
    19: "CN",
    20: "ID",
    21: "NZ",
    22: "AT",
    23: "CZ",
    24: "HR",
    25: "TR",
    26: "GR",
    27: "MO",
    28: "MN",
    29: "MX",
    30: "MP",
}
CITY_GEOCODING_QUERIES = {
    36: "Guam,US",
    38: "Hong Kong,CN",
    109: "Goreme,TR",
    113: "Macau,CN",
    117: "Saipan,US",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_optional_json(path):
    if not Path(path).exists():
        return {}
    return read_json(path)


class Command(BaseCommand):
    help = "data/dev_assets 의 CSV/JSON 을 DB 에 적재한다."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._countries()
        self._cities()
        self._health()
        self._safety()
        self._cultural_tips()
        self._tags()
        self._environment_tags()
        self._items()
        self._city_tags()
        self.stdout.write(self.style.SUCCESS("\n시드 적재 완료."))

    def _countries(self):
        rows = read_csv(DATA / "countries.csv")
        for r in rows:
            Country.objects.update_or_create(
                id=int(r["country_id"]), defaults={"name": r["country_ko"]})
        self.stdout.write(f"  Country        {len(rows):>4}")

    def _cities(self):
        rows = read_csv(DATA / "cities.csv")
        coordinates = read_optional_json(CACHE_PATH)
        changed = False
        missing = 0
        for r in rows:
            lat, lon = self._city_coordinates(r, coordinates)
            if lat is None or lon is None:
                missing += 1
            elif str(r["city_id"]) not in coordinates:
                coordinates[str(r["city_id"])] = {"lat": lat, "lon": lon}
                changed = True
            City.objects.update_or_create(
                id=int(r["city_id"]),
                defaults={
                    "name": r["city_ko"],
                    "country_id": int(r["country_id"]),
                    "latitude": lat,
                    "longitude": lon,
                })
        if changed:
            CACHE_PATH.write_text(json.dumps(coordinates, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        msg = f"  City           {len(rows):>4}"
        if missing:
            msg += f"   (좌표 없음 {missing}개)"
        self.stdout.write(msg)

    def _city_coordinates(self, row, coordinates):
        city_id = str(row["city_id"])
        if city_id in coordinates:
            return coordinates[city_id]["lat"], coordinates[city_id]["lon"]

        if row.get("latitude") and row.get("longitude"):
            return float(row["latitude"]), float(row["longitude"])

        api_key = getattr(settings, "OPEN_WEATHER_KEY", "")
        country_code = COUNTRY_CODES.get(int(row["country_id"]))
        if not api_key or not country_code:
            return None, None

        response = requests.get(
            GEOCODING_URL,
            params={
                "q": CITY_GEOCODING_QUERIES.get(
                    int(row["city_id"]), f"{row['city_en']},{country_code}"),
                "limit": 1,
                "appid": api_key,
            },
            timeout=5,
        )
        if response.status_code != 200:
            return None, None

        matches = response.json()
        if not matches:
            return None, None
        return matches[0]["lat"], matches[0]["lon"]

    def _health(self):
        data = read_json(DATA / "health_country.json")
        for cid, v in data.items():
            CountryHealth.objects.update_or_create(
                country_id=int(cid),
                defaults={
                    "tap_water_drinkable": v.get("tap_water_drinkable"),
                    "shower_filter_required": v.get("shower_filter_required"),
                    "yellow_fever_cert_required": v.get("yellow_fever_cert_required"),
                    "essential_vaccines": v.get("essential_vaccines", []),
                    "vaccine_note": v.get("vaccine_note"),
                })
        self.stdout.write(f"  CountryHealth  {len(data):>4}")

    def _safety(self):
        data = read_json(DATA / "safety_city.json")
        for cid, v in data.items():
            CitySafety.objects.update_or_create(
                city_id=int(cid),
                defaults={
                    "crime_index": v.get("crime_index"),
                    "safe_alone_day": v.get("safe_alone_day"),
                    "safe_alone_night": v.get("safe_alone_night"),
                    "emergency_contact": v.get("emergency_contact"),
                })
        self.stdout.write(f"  CitySafety     {len(data):>4}")

    def _cultural_tips(self):
        data = read_json(DATA / "cultural_tips_country.json")
        n = 0
        for cid, v in data.items():
            CulturalTip.objects.filter(country_id=int(cid)).delete()  # 재실행 시 중복 방지
            tips = [CulturalTip(country_id=int(cid), theme=t.get("theme", ""),
                                content=t.get("content", ""))
                    for t in v.get("cultural_tips", [])]
            CulturalTip.objects.bulk_create(tips)
            n += len(tips)
        self.stdout.write(f"  CulturalTip    {n:>4}")

    def _tags(self):
        rows = read_csv(DATA / "tags.csv")
        for r in rows:
            TravelTag.objects.update_or_create(
                id=int(r["pk"]),
                defaults={"tag_name": r["tag_name"], "tag_class": r["class"]})
        self.stdout.write(f"  TravelTag      {len(rows):>4}")

    def _items(self):
        rows = read_csv(DATA / "items.csv")
        tag_by_name = {t.tag_name: t for t in TravelTag.objects.all()}
        unmatched = set()
        for r in rows:
            item, _ = Item.objects.update_or_create(
                id=int(r["item_id"]),
                defaults={"name": r["item_name"], "default_tip": r.get("default_tip", "")})
            names = [n.strip() for n in (r.get("related_tags") or "").split(",") if n.strip()]
            matched = []
            for nm in names:
                t = tag_by_name.get(nm)
                if t:
                    matched.append(t)
                else:
                    unmatched.add(nm)
            item.tags.set(matched)
        msg = f"  Item           {len(rows):>4}"
        if unmatched:
            msg += f"   (tags.csv 에 없는 태그 {len(unmatched)}종 매칭 제외)"
        self.stdout.write(msg)

    def _city_tags(self):
        # cities.csv 의 travel_theme_tags 컬럼으로 도시↔태그 연결
        rows = read_csv(DATA / "cities.csv")
        tag_by_name = {t.tag_name: t for t in TravelTag.objects.all()}
        n, unmatched = 0, set()
        for r in rows:
            names = [x.strip() for x in (r.get("travel_theme_tags") or "").split(",") if x.strip()]
            tags = []
            for nm in names:
                t = tag_by_name.get(nm)
                if t:
                    tags.append(t)
                else:
                    unmatched.add(nm)
            try:
                City.objects.get(id=int(r["city_id"])).travel_tags.set(tags)
                n += 1
            except City.DoesNotExist:
                pass
        msg = f"  City↔Tag       {n:>4} 도시"
        if unmatched:
            msg += f"   (tags.csv 에 없는 태그 {len(unmatched)}종 제외)"
        self.stdout.write(msg)

    def _environment_tags(self):
        path = DATA / "city_environment_tags.csv"
        if not path.exists():
            self.stdout.write("  City↔EnvTag       0 도시   (city_environment_tags.csv 없음)")
            return

        rows = read_csv(path)
        tag_by_name = {t.tag_name: t for t in TravelTag.objects.all()}
        for name in ENVIRONMENT_TAG_NAMES:
            travel_tag = tag_by_name.get(name)
            if travel_tag:
                EnvironmentTag.objects.update_or_create(tag=travel_tag)
        n, unmatched = 0, set()
        for r in rows:
            names = [x.strip() for x in (r.get("environment_tags") or "").split(",")
                     if x.strip()]
            tags = []
            for nm in names:
                travel_tag = tag_by_name.get(nm)
                if travel_tag:
                    env_tag, _ = EnvironmentTag.objects.update_or_create(tag=travel_tag)
                    tags.append(env_tag)
                else:
                    unmatched.add(nm)
            try:
                City.objects.get(id=int(r["city_id"])).environment_tags.set(tags)
                n += 1
            except City.DoesNotExist:
                pass
        msg = f"  City↔EnvTag    {n:>4} 도시"
        if unmatched:
            msg += f"   (tags.csv 에 없는 태그 {len(unmatched)}종 제외)"
        self.stdout.write(msg)
