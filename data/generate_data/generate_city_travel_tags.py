import csv
import json
import os
import time
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
CITIES_CSV = BASE_DIR / "dev_assets" / "cities.csv"
COUNTRIES_CSV = BASE_DIR / "dev_assets" / "countries.csv"
OUTPUT_CSV = BASE_DIR / "generate_data" / "city_travel_tags.csv"
ENV_FILE = BASE_DIR / ".env"

MODEL_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
MODEL_NAME = "gpt-5-nano"

FIELDNAMES = [
    "city_id",
    "country_id",
    "country_ko",
    "city_ko",
    "city_en",
    "travel_theme_tags",
]


def load_env_file(path):
    if not path.exists():
        return

    with path.open(encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_output(rows):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def build_prompt(country_ko, city_ko, city_en):
    return f"""
다음 여행지의 주요 여행 테마 태그를 생성해라.

국가명: {country_ko}
도시명: {city_ko} ({city_en})

규칙:
- 한국어 태그 5~8개만 생성한다.
- 태그는 쉼표로 구분한다.
- 태그 예시는 휴양, 유적지, 온천, 박물관, 종교 성지, 쇼핑, 미식, 자연, 야경, 액티비티 등이다.
- 해당 도시와 관련성이 높은 태그만 사용한다.
- 설명 문장 없이 JSON만 출력한다.

출력 형식:
{{"tags":["태그1","태그2","태그3"]}}
""".strip()


def call_model(api_key, prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "developer",
                "content": "Answer in Korean. Output JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }
    for attempt in range(3):
        try:
            response = requests.post(
                MODEL_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
                timeout=60,
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                raise RuntimeError(f"Retryable OpenAI API HTTP {response.status_code}: {response.text}")
            if response.status_code >= 400:
                raise RuntimeError(f"OpenAI API HTTP {response.status_code}: {response.text}")
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            if attempt == 2:
                raise RuntimeError(f"OpenAI API request failed: {e}") from e
        except RuntimeError as e:
            if not str(e).startswith("Retryable ") or attempt == 2:
                raise

        time.sleep(2**attempt)

    raise RuntimeError("OpenAI API request failed")


def extract_text(response):
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected OpenAI response: {response}") from e


def parse_tags(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    data = json.loads(cleaned)
    tags = data.get("tags")
    if not isinstance(tags, list) or not tags:
        raise RuntimeError(f"OpenAI response has no tags: {text}")

    return ", ".join(str(tag).strip() for tag in tags if str(tag).strip())


def main():
    load_env_file(ENV_FILE)
    api_key = os.environ.get("GMS_KEY")
    if not api_key:
        raise RuntimeError("GMS_KEY is missing. Set it in .env or environment variables.")

    countries = {row["country_id"]: row["country_ko"] for row in read_csv(COUNTRIES_CSV)}
    cities = read_csv(CITIES_CSV)

    existing_rows = read_csv(OUTPUT_CSV) if OUTPUT_CSV.exists() else []
    done_city_ids = {row["city_id"] for row in existing_rows}
    output_rows = existing_rows[:]

    for city in cities:
        if city["city_id"] in done_city_ids:
            continue

        country_ko = countries[city["country_id"]]
        prompt = build_prompt(country_ko, city["city_ko"], city["city_en"])
        response = call_model(api_key, prompt)
        tags = parse_tags(extract_text(response))

        output_rows.append(
            {
                "city_id": city["city_id"],
                "country_id": city["country_id"],
                "country_ko": country_ko,
                "city_ko": city["city_ko"],
                "city_en": city["city_en"],
                "travel_theme_tags": tags,
            }
        )
        write_output(output_rows)
        print(f"{city['city_id']}: {country_ko} {city['city_ko']} -> {tags}", flush=True)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
