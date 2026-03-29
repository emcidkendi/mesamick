import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path

# ── 설정 ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SEEN_FILE = "seen_items.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "DPoP-Nonce": "",
}

# ── 키워드 로드 ───────────────────────────────────────
def load_keywords():
    kw_file = Path("keywords.txt")
    if not kw_file.exists():
        return []
    lines = kw_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

# ── 이미 본 아이템 관리 ───────────────────────────────
def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

# ── 메루카리 검색 ─────────────────────────────────────
def search_mercari(keyword: str) -> list:
    """메루카리 재팬 검색 API"""
    url = "https://api.mercari.jp/v2/entities:search"
    params = {
        "pageSize": 30,
        "pageToken": "",
        "searchSessionId": "",
        "indexRouting": "INDEX_ROUTING_UNSPECIFIED",
        "thumbnailTypes": [],
        "searchCondition": {
            "keyword": keyword,
            "excludeKeyword": "",
            "sort": "SORT_CREATED_TIME",
            "order": "ORDER_DESC",
            "status": ["STATUS_ON_SALE"],
            "categoryId": [],
            "brandId": [],
            "sellerId": [],
            "priceMin": 0,
            "priceMax": 0,
            "itemConditionId": [],
            "shippingPayerId": [],
            "shippingFromArea": [],
            "shippingMethod": [],
            "colorId": [],
            "hasCoupon": False,
            "attributes": [],
            "itemTypes": [],
            "skuIds": [],
        },
        "userId": "",
        "pageSize": 30,
    }

    try:
        resp = requests.post(
            url,
            json=params,
            headers={
                **HEADERS,
                "X-Platform": "web",
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        return items
    except Exception as e:
        print(f"[ERROR] 검색 실패 ({keyword}): {e}")
        return []

# ── 텔레그램 전송 ─────────────────────────────────────
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] 텔레그램 토큰 미설정 — 콘솔 출력만 함")
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

# ── 메인 ──────────────────────────────────────────────
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

        for item in items:
            item_id = item.get("id", "")
            if not item_id or item_id in seen:
                continue

            seen.add(item_id)
            new_count += 1

            name = item.get("name", "이름 없음")
            price = item.get("price", 0)
            thumbnails = item.get("thumbnails", [])
            thumb_url = thumbnails[0] if thumbnails else ""
            item_url = f"https://jp.mercari.com/item/{item_id}"

            msg = (
                f"🛍 <b>새 매물 발견!</b>\n"
                f"🔍 키워드: <code>{keyword}</code>\n"
                f"📦 {name}\n"
                f"💴 ¥{price:,}\n"
                f"🔗 <a href='{item_url}'>메루카리 보기</a>"
            )
            send_telegram(msg)
            time.sleep(0.3)  # 텔레그램 rate limit 방지

        time.sleep(1.5)  # 메루카리 요청 간격

    save_seen(seen)
    print(f"[완료] 새 매물 {new_count}개 발견")

if __name__ == "__main__":
    main()
