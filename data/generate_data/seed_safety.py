"""
CITY_SAFETY 데이터 생성 (도시 단위) → dev_assets/city_safety.json

- crime_index / safe_alone_day / safe_alone_night  : numbeo_crime_features.csv (도시별 원본)
- emergency_contact : 국가별 LLM 1회 호출(경찰/구급 + 도시별 관할 한국공관) → 도시별 조립
  주의: 공관 명칭/번호는 LLM best-effort. 정확값은 외교부 재외공관 데이터로 검증 권장.
"""

import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
client = OpenAI(base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1",
               api_key=os.environ.get("API_KEY") or os.environ.get("GMS_KEY"))
MODEL = "gpt-5-nano"
CONSULAR = "+82-2-3210-0404"  # 외교부 영사콜센터(공통)

HERE = Path(__file__).parent
CITIES_CSV = HERE / "dev_assets" / "cities.csv"
COUNTRIES_CSV = HERE / "dev_assets" / "countries.csv"
NUMBEO_CSV = HERE / "dev_assets" / "numbeo_crime_features.csv"
OUT = HERE / "dev_assets" / "city_safety.json"


class CityConsulate(BaseModel):
    city_ko: str
    consulate: str = Field(description="그 도시를 관할하는 대한민국 공관 명칭(없으면 그 나라 대사관)")


class CountryEmergency(BaseModel):
    police: str = Field(description="현지 경찰 긴급전화 번호")
    ambulance: str = Field(description="현지 구급/응급 전화 번호")
    consulates: list[CityConsulate]


def fetch_emergency(country_ko: str, city_list: list[str]) -> CountryEmergency:
    prompt = (f"국가: {country_ko}\n도시들: {', '.join(city_list)}\n"
              f"이 나라의 경찰/구급 긴급전화번호와, 각 도시를 관할하는 대한민국 재외공관"
              f"(대사관 또는 총영사관) 명칭을 알려줘.")
    c = client.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "developer", "content": "너는 한국 여행자용 해외 안전정보 전문가다. 한국어로 답한다."},
                  {"role": "user", "content": prompt}],
        response_format=CountryEmergency, reasoning_effort="low")
    return c.choices[0].message.parsed


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    cities = load_csv(CITIES_CSV)              # city_id, city_ko, city_en, country_id
    countries = {r["country_id"]: r["country_ko"] for r in load_csv(COUNTRIES_CSV)}
    numbeo = {r["city_id"]: r for r in load_csv(NUMBEO_CSV)}

    # 국가별 도시 그룹
    by_country: dict[str, list] = {}
    for c in cities:
        by_country.setdefault(c["country_id"], []).append(c)

    # 국가별 emergency 생성 (병렬)
    emerg: dict[str, CountryEmergency] = {}

    def work(cid):
        ko = countries.get(cid, "")
        names = [c["city_ko"] for c in by_country[cid]]
        return cid, fetch_emergency(ko, names)

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(work, cid): cid for cid in by_country}
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                cid, e = fut.result(); emerg[cid] = e
                print(f"  OK 국가[{cid:>2}] {countries.get(cid,'')}")
            except Exception as ex2:
                print(f"  ERR 국가[{cid}] {ex2}")

    def fnum(v):
        try: return round(float(v), 2)
        except (TypeError, ValueError): return None

    # 도시별 조립
    result = {}
    for c in cities:
        cid, ccid = c["city_id"], c["country_id"]
        n = numbeo.get(cid, {})
        e = emerg.get(ccid)
        consulate = ""
        if e:
            consulate = next((x.consulate for x in e.consulates
                              if x.city_ko.strip() == c["city_ko"].strip()), "")
            if not consulate and e.consulates:
                consulate = e.consulates[0].consulate  # 매칭 실패 시 첫 공관
        contact = (f"경찰 {e.police} / 구급 {e.ambulance} / {consulate} / 영사콜센터 {CONSULAR}"
                   if e else f"영사콜센터 {CONSULAR}")
        result[cid] = {
            "city_ko": c["city_ko"], "country_id": int(ccid),
            "crime_index": fnum(n.get("level_of_crime")),
            "safe_alone_day": fnum(n.get("safety_daylight")),
            "safe_alone_night": fnum(n.get("safety_night")),
            "emergency_contact": contact,
        }

    ordered = {k: result[k] for k in sorted(result, key=int)}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {OUT}  ({len(ordered)}개 도시)")


if __name__ == "__main__":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    main()
