# 메루카리 알림봇 🛍

메루카리 재팬에서 키워드 매물이 올라오면 텔레그램으로 알림을 보내주는 봇입니다.

---

## 설치 순서

### 1. 텔레그램 봇 만들기

1. 텔레그램에서 **@BotFather** 검색
2. `/newbot` 입력
3. 봇 이름 입력 (예: `MercariAlert`)
4. 유저네임 입력 (예: `my_mercari_alert_bot`)
5. **토큰 복사** (이렇게 생긴 문자열: `123456789:ABCdefGHI...`)

### 2. Chat ID 얻기

1. 방금 만든 봇에게 아무 메시지나 보내기
2. 브라우저에서 접속:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. `"chat":{"id": 숫자}` — 이 숫자가 Chat ID

### 3. GitHub 레포 만들기

1. GitHub에서 새 레포 생성 (private 권장)
2. 이 파일들을 전부 올리기:
   - `scraper.py`
   - `keywords.txt`
   - `.github/workflows/mercari.yml`

### 4. Secrets 등록

GitHub 레포 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `TELEGRAM_TOKEN` | BotFather에서 받은 토큰 |
| `TELEGRAM_CHAT_ID` | 위에서 찾은 숫자 |

### 5. Actions 활성화

- GitHub 레포 → **Actions 탭** → Enable

끝! 이제 매 1시간마다 자동으로 실행됩니다.
수동으로 테스트하려면 Actions → Run workflow 버튼 클릭.

---

## 키워드 수정

`keywords.txt` 파일을 직접 수정하면 됩니다.
- `#` 으로 시작하는 줄은 주석 (무시됨)
- 일본어/영어 모두 가능

---

## 알림 예시

```
🛍 새 매물 발견!
🔍 키워드: marilyn manson vintage tシャツ
📦 マリリンマンソン ヴィンテージ Tシャツ 90s
💴 ¥3,200
🔗 메루카리 보기
```
