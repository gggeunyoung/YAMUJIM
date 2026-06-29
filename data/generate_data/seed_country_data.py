"""
국가별 정적 데이터 1회 생성 (LLM 증강) → dev_assets/country_data.json

생성 항목 (국가 단위):
  health         : tap_water_drinkable, shower_filter_required,
                   required_vaccines, recommended_vaccines, yellow_fever_cert
  safety         : travel_alert_level(외교부 기준 1~4), emergency_contact
                   + Numbeo 도시 평균(crime_index/safe_alone_day/night)
  cultural_taboos: [{category, content}]

데이터 출처:
  - 백신: CDC 표준 여행 권장 기준 (LLM)
  - 문화금기/식수/경보: LLM 증강
  - 범죄지수: dev_assets/numbeo_crime_features.csv (도시 → 국가 평균)

주의: LLM 생성 데이터다. 황열 증명서 의무, 여행경보처럼 법적/공식 정보는
      추후 CDC/외교부 공식 소스로 검증·갱신 권장.
"""

import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

BASE_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"
MODEL = "gpt-5-nano"
client = OpenAI(base_url=BASE_URL, api_key=os.environ.get("API_KEY") or os.environ.get("GMS_KEY"))

HERE = Path(__file__).parent
COUNTRIES_CSV = HERE / "dev_assets" / "countries.csv"
NUMBEO_CSV = HERE / "dev_assets" / "numbeo_crime_features.csv"
OUT_JSON = HERE / "dev_assets" / "country_data.json"


# ── 출력 스키마 ──────────────────────────────────────────────
class Taboo(BaseModel):
    category: Literal["복장", "주류", "제스처", "기타"]
    content: str = Field(description="구체적 금기/주의사항 한 문장")


class Health(BaseModel):
    tap_water_drinkable: bool = Field(description="수돗물 식수 적합 여부")
    shower_filter_required: bool = Field(description="샤워필터 권장 여부(수질 나쁘면 true)")
    yellow_fever_cert_required: bool = Field(description="입국 시 황열 예방접종 증명서(옐로카드) 의무 여부")
    essential_vaccines: list[str] = Field(
        description="이 목적지라서 '실제로 꼭 챙겨야 하는' 백신/예방약만. 저위험 선진국은 빈 배열. "
                    "각 항목은 '백신명 (왜 필요한지 짧게)' 형식"
    )
    vaccine_note: str = Field(description="백신 한 줄 요약. 특별히 필요 없으면 그렇게 명시")


class Safety(BaseModel):
    travel_alert_level: int = Field(description="외교부 여행경보 추정 1~4 (1 유의 ~ 4 금지)")
    emergency_contact: str = Field(
        description="현지 실제 긴급전화(경찰/구급)와 한국 영사콜센터(+82-2-3210-0404)를 모두 포함. "
                    "예: '경찰 113, 구급 115 / 영사콜센터 +82-2-3210-0404'"
    )


class Tip(BaseModel):
    theme: Literal["기후/복장", "교통", "결제", "통신", "음식/식수", "준비물", "기타"]
    content: str = Field(description="현지 특화 실용 팁 한 문장")


class CountryData(BaseModel):
    health: Health
    safety: Safety
    cultural_taboos: list[Taboo]
    travel_tips: list[Tip]


SYSTEM = """너는 한국인 여행자를 위한 국가별 여행 데이터 전문가다.
주어진 국가에 대해 health, safety, cultural_taboos 데이터를 생성한다.

[백신 — 매우 중요한 기준]
essential_vaccines 에는 '이 목적지의 감염병 위험 때문에 여행자가 실제로 추가로 꼭 챙겨야 하는'
백신/예방약만 넣는다.
- 전 세계 공통 기본 접종은 절대 넣지 않는다: MMR(홍역), 파상풍/Tdap, 독감(인플루엔자),
  코로나19, 수두, B형간염 등은 제외.
- 일본·미국·서유럽·호주·싱가포르처럼 감염병 위험이 낮은 선진국/위생 양호국은 빈 배열 [] 로 둔다.
- 다음과 같은 '그 지역 특유의 실질 위험'만 포함한다:
  아프리카/남미 등의 황열, 말라리아 유행지의 말라리아 예방약, 위생이 열악한 지역의
  장티푸스·A형간염, 농촌 장기체류의 일본뇌염, 광견병 위험지의 광견병 등.
- 애매하면 넣지 않는다. 목록은 보통 0~3개면 충분하다.
- yellow_fever_cert_required 는 입국 시 황열 증명서가 '의무'인 경우만 true.
- vaccine_note 규칙(중요): essential_vaccines 가 비어있지 않으면 그 백신들을 언급하는 요약을 쓴다.
  essential_vaccines 가 빈 배열일 때만 "기본 예방접종 외 추가로 꼭 맞아야 할 백신은 없습니다" 라고 쓴다.
  (목록이 있는데 '필요 없음'이라고 쓰면 안 된다.)

[그 외]
- travel_alert_level 은 대한민국 외교부 여행경보 체계(1 여행유의 ~ 4 여행금지) 기준 추정값.
- emergency_contact 는 그 나라의 실제 경찰/구급 긴급전화번호와 한국 영사콜센터를 모두 포함한다.
- cultural_taboos 는 복장/주류/제스처 등 한국인이 실수하기 쉬운 현지 금기 위주로 3~6개.
- travel_tips 는 그 목적지 특유의 실용 정보를 4~6개. 기후/복장, 교통, 결제(현금vs카드),
  통신(유심/eSIM/로밍), 음식/식수, 특화 준비물 등에서 한국인 여행자에게 도움되는 팁 위주.
- 모든 텍스트는 한국어."""


def fetch_country(country_ko: str) -> CountryData:
    completion = client.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "developer", "content": SYSTEM},
            {"role": "user", "content": f"국가: {country_ko}"},
        ],
        response_format=CountryData,
        reasoning_effort="low",
    )
    return completion.choices[0].message.parsed


def load_countries() -> list[tuple[int, str]]:
    with open(COUNTRIES_CSV, encoding="utf-8-sig") as f:
        return [(int(r["country_id"]), r["country_ko"]) for r in csv.DictReader(f)]


def numbeo_country_avg() -> dict[int, dict]:
    """도시별 Numbeo 범죄 데이터를 국가 평균으로 집계."""
    agg: dict[int, list] = {}
    with open(NUMBEO_CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cid = int(r["country_id"])
            agg.setdefault(cid, []).append(r)

    def avg(rows, key):
        vals = [float(x[key]) for x in rows if x.get(key) not in (None, "")]
        return round(sum(vals) / len(vals), 2) if vals else None

    return {
        cid: {
            "crime_index": avg(rows, "level_of_crime"),
            "safe_alone_day": avg(rows, "safety_daylight"),
            "safe_alone_night": avg(rows, "safety_night"),
        }
        for cid, rows in agg.items()
    }


def main():
    countries = load_countries()
    crime = numbeo_country_avg()
    result: dict[str, dict] = {}

    def work(item):
        cid, ko = item
        data = fetch_country(ko).model_dump()
        data["safety"].update(crime.get(cid, {}))  # Numbeo 평균 병합
        return cid, ko, data

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(work, c): c for c in countries}
        for fut in as_completed(futures):
            cid, ko = futures[fut]
            try:
                cid, ko, data = fut.result()
                result[str(cid)] = {"country_ko": ko, **data}
                print(f"  OK  [{cid:>2}] {ko}")
            except Exception as e:
                print(f"  ERR [{cid:>2}] {ko}: {e}")

    # country_id 순으로 정렬 저장
    ordered = {k: result[k] for k in sorted(result, key=int)}
    OUT_JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {OUT_JSON}  ({len(ordered)}개국)")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
