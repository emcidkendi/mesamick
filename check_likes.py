import os
import json
import requests
from datetime import datetime
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL_ID = "-1003882080903"  # 이크에크 채널
SHEETS_URL = "https://script.google.com/macros/s/AKfycbxscQ1bE4BOitDfbAY2MPISbxpP3lx_nJsBuZJXCN_h3WYfoIpV0FaFnkvGTR0NAi7F/exec"
DAILY_LOG = "daily_log.json"

def load_offset():
    if Path(OFFSET_FILE).exists():
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0

def save_offset(offset: int):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

def load_daily_log():
    if Path(DAILY_LOG).exists():
        with open(DAILY_LOG, "r") as f:
            return json.load(f)
    return []

def save_daily_log(log: list):
    with open(DAILY_LOG, "w") as f:
        json.dump(log, f, ensure_ascii=False)

def answer_callback(callback_id: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={
        "callback_query_id": callback_id,
        "text": "❤️ 저장됐어요!",
        "show_alert": False
    }, timeout=5)

def forward_to_channel(item: dict):
    """이크에크 채널로 포워드"""
    msg = (
        f"❤️ <b>저장된 매물</b>\n"
        f"💴 ¥{item['price']:,}\n"
        f"🔗 <a href='{item['url']}'>메루카리 보기</a>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }, timeout=10)

def add_to_sheets(item: dict):
    """구글 시트에 행 추가"""
    try:
        requests.post(SHEETS_URL, json={
            "price": item["price"],
            "url": item["url"]
        }, timeout=10)
    except Exception as e:
        print(f"[ERROR] 시트 추가 실패: {e}")

def main():
    if not TELEGRAM_TOKEN:
        print("[INFO] 토큰 없음")
        return

    offset = load_offset()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    try:
        resp = requests.get(url, params={"offset": offset, "timeout": 5}, timeout=10)
        updates = resp.json().get("result", [])
    except Exception as e:
        print(f"[ERROR] 업데이트 실패: {e}")
        return

    if not updates:
        print("[INFO] 새 업데이트 없음")
        return

    daily_log = load_daily_log()
    liked_count = 0

    for update in updates:
        new_offset = update["update_id"] + 1
        save_offset(new_offset)

        cb = update.get("callback_query")
        if not cb:
            continue

        data = cb.get("data", "")
        if not data.startswith("save|"):
            continue

        item_id = data.split("|")[1]
        answer_callback(cb["id"])

        for entry in daily_log:
            if entry.get("item_id") == item_id and not entry.get("liked"):
                entry["liked"] = True
                liked_count += 1
                print(f"  ❤️ 저장됨: {entry.get('name', item_id)}")

                # 채널 포워드 + 시트 추가
                forward_to_channel(entry)
                add_to_sheets(entry)

    save_daily_log(daily_log)
    print(f"[완료] {liked_count}개 저장됨")

if __name__ == "__main__":
    main()
