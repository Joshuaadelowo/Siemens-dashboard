import json
from pathlib import Path
from urllib.parse import unquote

import requests

# 1. Siemens endpoint from the curl request
url = "https://eadvantage.siemens.com/remote/release/reportengine/report-task/057d2cc7-4213-45e0-a20e-60a33887d669/result"

# 2. Headers from the curl request
headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://eadvantage.siemens.com/eccng/?viewId=104069&theme=default",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Microsoft Edge";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "x-navigator-csrf": "fOWbRUdihTp3lSiavglPNOtezMlY3ErFyWLGek0Lzzc=",
    "x-requested-with": "XMLHttpRequest",
}

# 3. Cookie header from the curl request
cookie_header = (
    "SXSESS=s%3Adssa_OKH0g09tgF1oluFJfM1oWsjaVa4.RFAmsxrzLaGSdKa8hTx9RHZDc0hwQ2x0nzFI9TOTla8; "
    "s_cc=true; "
    "SelectedCountry=%7B%22countrycode%22%3A%22GB%22%2C%22countryname%22%3A%22United%20Kingdom%22%2C%22default%22%3Afalse%7D; "
    "TERMS=submitted; "
    "remember=AREAWLplnqnUsYsfBvqL7clRllYejTq8KkNTpWdoJfqmeag132BqANWCBgAvDAARiavrsH7zSGa6BAbSLJM0AAAAmlAbVrdINzNy7lD9H6gQ_A; "
    "navsession=AREAU6UbdZZfbQWcTEVI6yCC7IYfmt6jZuVZVAvnfjs_26gKYmdqAAAAAAAvDABCYigHErW3G6T3jfdekAhvAAAAcBhNIzbK_WI3G4Z59M62_g; "
    "navigator-csrf=fOWbRUdihTp3lSiavglPNOtezMlY3ErFyWLGek0Lzzc="
)


def parse_cookies(cookie_header_value: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for chunk in cookie_header_value.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        cookies[key] = unquote(value)
    return cookies


cookies = parse_cookies(cookie_header)
output_path = Path(__file__).resolve().parent / "siemens_data.json"

print("Fetching data from Siemens Navigator...")
response = requests.get(url, headers=headers, cookies=cookies, timeout=30)

if response.ok:
    try:
        data = response.json()
    except ValueError:
        data = {"raw_text": response.text}

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Success! Data saved to '{output_path}'.")
else:
    print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
    print(response.text[:1000])