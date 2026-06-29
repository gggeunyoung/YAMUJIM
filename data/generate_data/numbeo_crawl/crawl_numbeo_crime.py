import argparse
import csv
import re
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


TARGET_FIELDS = {
    "level_of_crime": "Level of crime",
    "safety_daylight": "Safety walking alone during daylight",
    "safety_night": "Safety walking alone during night",
}

SLUG_OVERRIDES = {
    "Ho Chi Minh City": "Ho-Chi-Minh-City",
    "Kuala Lumpur": "Kuala-Lumpur",
    "Kota Kinabalu": "Kota-Kinabalu",
    "Gold Coast": "Gold-Coast",
    "Quebec City": "Quebec-City",
    "Mexico City": "Mexico-City",
    "New York": "New-York",
    "Los Angeles": "Los-Angeles",
    "San Francisco": "San-Francisco",
    "Las Vegas": "Las-Vegas",
    "Da Nang": "Da-Nang",
    "Nha Trang": "Nha-Trang",
    "Phu Quoc": "Phu-Quoc",
    "Sa Pa": "Sa-Pa",
    "Chiang Mai": "Chiang-Mai",
    "Koh Samui": "Koh-Samui",
}

URL_OVERRIDES = {
    "Phu Quoc": "https://www.numbeo.com/crime/in/Da-Nang",
    "Sa Pa": "https://www.numbeo.com/crime/in/Hanoi",
    "Hawaii": "https://www.numbeo.com/crime/in/Honolulu",
    "Boracay": "https://www.numbeo.com/crime/in/Boracay-Philippines",
    "Bohol": "https://www.numbeo.com/crime/in/Bohol-Philippines",
    "Clark": "https://www.numbeo.com/crime/in/Manila",
    "Hualien": "https://www.numbeo.com/crime/in/Taipei",
    "Guam": "https://www.numbeo.com/crime/in/Tamuning",
    "Amalfi": "https://www.numbeo.com/crime/in/Naples",
    "Seville": "https://www.numbeo.com/crime/in/Sevilla",
    "Interlaken": "https://www.numbeo.com/crime/in/Zurich",
    "Zermatt": "https://www.numbeo.com/crime/in/Zermatt-Switzerland",
    "Langkawi": "https://www.numbeo.com/crime/in/Penang",
    "Zhangjiajie": "https://www.numbeo.com/crime/in/Chengdu",
    "Lombok": "https://www.numbeo.com/crime/in/Bali",
    "Hallstatt": "https://www.numbeo.com/crime/in/Salzburg",
    "Cesky Krumlov": "https://www.numbeo.com/crime/in/Prague",
    "Cappadocia": "https://www.numbeo.com/crime/in/Antalya",
    "Santorini": "https://www.numbeo.com/crime/in/Santorini-Greece",
    "Macau": "https://www.numbeo.com/crime/in/Hong-Kong",
    "Saipan": "https://www.numbeo.com/crime/in/Saipan-Northern-Mariana-Islands",
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        data = data.strip()
        if data:
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def city_to_slug(city_en):
    slug = SLUG_OVERRIDES.get(city_en, city_en.replace(" ", "-"))
    return quote(slug, safe="-")


def city_to_url(city_en):
    if city_en in URL_OVERRIDES:
        return URL_OVERRIDES[city_en]
    return f"https://www.numbeo.com/crime/in/{city_to_slug(city_en)}"


def fetch_page(url, timeout):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; educational-city-index-script/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_crime_values(html):
    parser = TextExtractor()
    parser.feed(html)
    text = re.sub(r"\s+", " ", parser.text())

    values = {}
    for output_name, label in TARGET_FIELDS.items():
        match = re.search(rf"{re.escape(label)}\s+([0-9]+(?:\.[0-9]+)?)", text)
        if not match:
            raise ValueError(f"missing field: {label}")
        values[output_name] = match.group(1)
    return values


def crawl_city(city_en, timeout):
    url = city_to_url(city_en)
    html = fetch_page(url, timeout)
    values = parse_crime_values(html)
    values["numbeo_url"] = url
    values["scrape_error"] = ""
    return values


def is_socket_permission_error(exc):
    return "WinError 10013" in str(exc)


def iter_city_rows(reader):
    header = next(reader)
    expected_header = ["city_id", "city_ko", "city_en", "country_id"]
    if header != expected_header:
        raise ValueError(f"unexpected input header: {header}")

    for row in reader:
        if len(row) < 4 or not row[0].strip() or not row[2].strip():
            continue
        yield row


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--input", default="cities.csv")
    arg_parser.add_argument("--output", default="numbeo_crime_features.csv")
    arg_parser.add_argument("--delay", type=float, default=1.5)
    arg_parser.add_argument("--timeout", type=float, default=20.0)
    arg_parser.add_argument("--limit", type=int, default=None)
    arg_parser.add_argument("--update-missing", action="store_true")
    args = arg_parser.parse_args()

    output_header = [
        "city_id",
        "city_ko",
        "city_en",
        "country_id",
        "numbeo_url",
        "level_of_crime",
        "safety_daylight",
        "safety_night",
        "scrape_error",
    ]

    if args.update_missing:
        with open(args.output, "r", encoding="utf-8-sig", newline="") as output_file:
            rows = list(csv.DictReader(output_file))

        targets = [row for row in rows if not row["level_of_crime"].strip()]
        if args.limit is not None:
            targets = targets[: args.limit]

        for index, row in enumerate(targets, start=1):
            city_ko = row["city_ko"].strip()
            city_en = row["city_en"].strip()
            print(f"[{index}] retrying {city_ko} ({city_en}) ...", flush=True)
            try:
                result = crawl_city(city_en, args.timeout)
                row.update(result)
                print(f"[{index}] ok {city_ko} ({city_en})", flush=True)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                row["numbeo_url"] = city_to_url(city_en)
                row["scrape_error"] = str(exc)
                print(f"[{index}] failed {city_ko} ({city_en}): {exc}", flush=True)
                if is_socket_permission_error(exc):
                    print("network socket access is blocked. stopping crawl.", flush=True)
                    break
            time.sleep(args.delay)

        with open(args.output, "w", encoding="utf-8-sig", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=output_header)
            writer.writeheader()
            writer.writerows(rows)

        print(f"done. retried {len(targets)} missing rows in {args.output}", flush=True)
        return

    written = 0
    with open(args.input, "r", encoding="utf-8", newline="") as input_file:
        with open(args.output, "w", encoding="utf-8-sig", newline="") as output_file:
            reader = csv.reader(input_file)
            writer = csv.writer(output_file)
            writer.writerow(output_header)
            output_file.flush()

            for row in iter_city_rows(reader):
                if args.limit is not None and written >= args.limit:
                    break

                city_id, city_ko, city_en, country_id = [value.strip() for value in row[:4]]
                result = {
                    "numbeo_url": city_to_url(city_en),
                    "level_of_crime": "",
                    "safety_daylight": "",
                    "safety_night": "",
                    "scrape_error": "",
                }

                print(f"[{written + 1}] crawling {city_ko} ({city_en}) ...", flush=True)
                try:
                    result.update(crawl_city(city_en, args.timeout))
                    print(f"[{written + 1}] ok {city_ko} ({city_en})", flush=True)
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                    result["scrape_error"] = str(exc)
                    print(f"[{written + 1}] failed {city_ko} ({city_en}): {exc}", flush=True)
                    if is_socket_permission_error(exc):
                        print("network socket access is blocked. stopping crawl.", flush=True)

                writer.writerow(
                    [city_id, city_ko, city_en, country_id]
                    + [
                        result["numbeo_url"],
                        result["level_of_crime"],
                        result["safety_daylight"],
                        result["safety_night"],
                        result["scrape_error"],
                    ]
                )
                output_file.flush()
                written += 1
                if is_socket_permission_error(result["scrape_error"]):
                    break
                time.sleep(args.delay)

    print(f"done. wrote {written} rows to {args.output}", flush=True)


if __name__ == "__main__":
    main()
