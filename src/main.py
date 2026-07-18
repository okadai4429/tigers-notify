import sys
import os
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from notifier import build_message, send_slack_notification

CHECK_INTERVAL = 300
MAX_WAIT_TIME = 10800


def main():
    print("🐯 阪神タイガース試合結果通知BOT 起動！")

    elapsed = 0

    while elapsed <= MAX_WAIT_TIME:

        result = {
            "status": "WIN",
            "score": "5-2",
            "opponent": "読売ジャイアンツ",
            "home_runs": [
                {"player": "大山悠輔", "number": 15},
                {"player": "佐藤輝明", "number": 23}
            ]
        }

        print(f"⏱️ 試合状態: {result['status']}")

        if result["status"] == "IN_PROGRESS":
            print(f"⚾ 試合中です。{CHECK_INTERVAL // 60}分後に再チェックします...")
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL
            continue

        message = build_message(result)
        print(f"メッセージ: {message}")

        success = send_slack_notification(message)

        if not success:
            print("❌ 通知に失敗しました")
            sys.exit(1)

        print("✅ BOT 処理完了！")
        return

    print("⏰ タイムアウト：試合結果を取得できませんでした")
    send_slack_notification("⏰ タイムアウト：試合結果を取得できませんでした")
    sys.exit(1)


if __name__ == "__main__":
    main()