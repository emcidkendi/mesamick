import os
import json
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SEEN_FILE = "seen_items.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def load_keywords():
    kw_file = Path("keywords.txt")
    if not kw_file.exists():
        return []
    lines = kw_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def search_mercari(keyword: str) -> list:
    encoded = quote(keyword)
    url = f"https://jp.mercari.com/search?keyword={encoded}&status=on_sale&sort=created_time&order=desc"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text

        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if not match:
            print(f"  [WARN] __NEXT_DATA__ 없음 ({keyword})")
            return []

        data = json.loads(match.group(1))

        try:
            items = data["props"]["pageProps"]["initialState"]["search"]["result"]["items"]
            return items if items else []
        except (KeyError, TypeError):
            text = json.dumps(data)
            items_match = re.search(r'"items"\s*:\s*(\[.*?\])', text, re.DOTALL)
            if items_match:
                try:
                    return json.loads(items_match.group(1))
                except:
                    pass
            print(f"  [WARN] 아이템 파싱 실패 ({keyword})")
            return []

    except Exception as e:
        print(f"  [ERROR] 검색 실패 ({keyword}): {e}")
        return []

def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] 텔레그램 미설정")
        print(message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] 텔레그램 전송 실패: {e}")

def main():
    keywords = load_keywords()
    if not keywords:
        print("[INFO] keywords.txt 가 비어있거나 없음")
        return

    seen = load_seen()
    new_count = 0

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 검색 시작 — {len(keywords)}개 키워드")

    for keyword in keywords:
        print(f"  → 검색 중: {keyword}")
        items = search_mercari(keyword)
        print(f"     {len(items)}개 결과")

        for item in items:
            item_id = item.get("id", "")
            if not item_id or item_id in seen:
                continue

            seen.add(item_id)
            new_count += 1

            name = item.get("name", "이름 없음")
            price = item.get("price", 0)
            item_url = f"https://jp.mercari.com/item/{item_id}"

            msg = (
                f"🛍 <b>새 매물 발견!</b>\n"
                f"🔍 키워드: <code>{keyword}</code>\n"
                f"📦 {name}\n"
                f"💴 ¥{price:,}\n"
                f"🔗 <a href='{item_url}'>메루카리 보기</a>"
            )
            send_telegram(msg)
            time.sleep(0.3)

        time.sleep(2)

    save_seen(seen)
    print(f"[완료] 새 매물 {new_count}개 발견")

if __name__ == "__main__":
    main()
