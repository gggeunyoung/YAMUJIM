"""
COUNTRY_HEALTH 데이터 생성 (국가 단위, LLM 증강) → dev_assets/country_health.json

필드: tap_water_drinkable, shower_filter_required, yellow_fever_cert_required,
      essential_vaccines(목적지 필수 백신만), vaccine_note
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

HERE = Path(__file__).parent
COUNTRIES_CSV = HERE / "dev_assets" / "countries.csv"
OUT = HERE / "dev_assets" / "country_health.json"


class Health(BaseModel):
    tap_water_drinkable: bool = Field(description="수돗물 식수 적합 여부")
    shower_filter_required: bool = Field(description="수질이 나빠 샤워필터가 권장되는지")
    yellow_fever_cert_required: bool = Field(description="입국 시 황열 증명서 의무 여부")
    essential_vaccines: list[str] = Field(
        description="이 목적지라서 '실제로 꼭 챙겨야 하는' 백신/예방약만. 저위험 선진국은 빈 배열. "
                    "각 항목은 '백신명 (왜 필요한지 짧게)' 형식")
    vaccine_note: str = Field(description="백신 한 줄 요약")


SYSTEM = """너는 한국인 여행자를 위한 국가별 건강 데이터 전문가다.
essential_vaccines 에는 '이 목적지의 감염병 위험 때문에 실제로 추가 접종해야 하는' 백신/예방약만 넣는다.
- 전 세계 공통 기본 접종(MMR, 파상풍/Tdap, 독감, 코로나19, 수두, B형간염)은 절대 넣지 않는다.
- 일본·미국·서유럽·호주·싱가포르처럼 위험 낮은 선진국은 빈 배열 []로 둔다.
- 아프리카/남미 황열, 말라리아 유행지의 말라리아 예방약, 위생 열악지의 장티푸스·A형간염,
  농촌 장기체류의 일본뇌염, 광견병 위험지의 광견병 등 '그 지역 특유의 실질 위험'만 포함. 보통 0~3개.
- essential_vaccines 가 비어있지 않으면 vaccine_note 에 그 백신들을 언급한다.
  비어있을 때만 '기본 예방접종 외 추가로 꼭 맞아야 할 백신은 없습니다' 라고 쓴다.
- 모든 텍스트는 한국어."""


def fetch(country_ko: str) -> Health:
    c = client.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "developer", "content": SYSTEM},
                  {"role": "user", "content": f"국가: {country_ko}"}],
        response_format=Health, reasoning_effort="low")
    return c.choices[0].message.parsed


def main():
    with open(COUNTRIES_CSV, encoding="utf-8-sig") as f:
        countries = [(int(r["country_id"]), r["country_ko"]) for r in csv.DictReader(f)]

    result = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch, ko): (cid, ko) for cid, ko in countries}
        for fut in as_completed(futs):
            cid, ko = futs[fut]
            try:
                result[str(cid)] = {"country_ko": ko, **fut.result().model_dump()}
                print(f"  OK [{cid:>2}] {ko}")
            except Exception as e:
                print(f"  ERR [{cid:>2}] {ko}: {e}")

    ordered = {k: result[k] for k in sorted(result, key=int)}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {OUT}  ({len(ordered)}개국)")


if __name__ == "__main__":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    main()
