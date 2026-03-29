"""
매 2시간마다 실행 — 텔레그램에서 ❤️ 버튼 누른 것 감지해서 daily_log.json 업데이트
"""
import os
import json
import requests
from pathlib import Path

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OFFSET_FILE = "callback_offset.json"
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
    """버튼 누른 것에 응답 (텔레그램 필수)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={
        "callback_query_id": callback_id,
        "text": "❤️ 저장됐어요!",
        "show_alert": False
    }, timeout=5)

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
        print(f"[ERROR] 업데이트 가져오기 실패: {e}")
        return

    if not updates:
        print("[INFO] 새 업데이트 없음")
        return

    daily_log = load_daily_log()
    liked_count = 0

    for update in updates:
        new_offset = update["update_id"] + 1
        save_offset(new_offset)

        # 콜백 쿼리 (버튼 클릭) 처리
        cb = update.get("callback_query")
        if not cb:
            continue

        data = cb.get("data", "")
        if not data.startswith("save|"):
            continue

        item_id = data.split("|")[1]
        answer_callback(cb["id"])

        # daily_log에서 해당 아이템 liked = True 로 업데이트
        for entry in daily_log:
            if entry.get("item_id") == item_id and not entry.get("liked"):
                entry["liked"] = True
                liked_count += 1
                print(f"  ❤️ 저장됨: {entry.get('name', item_id)}")

    save_daily_log(daily_log)
    print(f"[완료] {liked_count}개 저장됨")

if __name__ == "__main__":
    main()
