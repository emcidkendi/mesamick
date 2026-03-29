import os
import json
import requests
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL_ID = "-1003882080903"
SHEETS_URL = "https://script.google.com/macros/s/AKfycbxACB9dj74D6PjCNo_4GHPIdTzoRKc0nmG9Ig5f6au45x0mrhdmRt50u62JADPv2r-O/exec"
OFFSET_FILE = "callback_offset.json"
DAILY_LOG = "daily_log.json"

def load_offset():
    if Path(OFFSET_FILE).exists():
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

def load_daily_log():
    if Path(DAILY_LOG).exists():
        with open(DAILY_LOG, "r") as f:
            return json.load(f)
    return []

def save_daily_log(log):
    with open(DAILY_LOG, "w") as f:
        json.dump(log, f, ensure_ascii=False)

def answer_callback(callback_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id, "text": "❤️ 저장됐어요!", "show_alert": False}, timeout=5)

def forward_to_channel(item):
    msg = f"❤️ <b>저장된 매물</b>\n💴 ¥{item['price']:,}\n🔗 <a href='{item['url']}'>메루카리 보기</a>"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)

def add_to_sheets(item):
    try:
        requests.post(SHEETS_URL, json={"price": item["price"], "url": item["url"]}, timeout=10)
    except Exception as e:
        print(f"[ERROR] 시트 추가 실패: {e}")

def main():
    if not TELEGRAM_TOKEN:
        return
    offset = load_offset()
    try:
        resp = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", params={"offset": offset, "timeout": 5}, timeout=10)
        updates = resp.json().get("result", [])
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    if not updates:
        print("[INFO] 새 업데이트 없음")
        return
    daily_log = load_daily_log()
    liked_count = 0
    for update in updates:
        save_offset(update["update_id"] + 1)
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
                forward_to_channel(entry)
                add_to_sheets(entry)
    save_daily_log(daily_log)
    print(f"[완료] {liked_count}개 저장됨")

if __name__ == "__main__":
    main()
