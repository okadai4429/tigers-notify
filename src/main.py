import sys
import os
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from notifier import build_message, send_slack_notification
from scraper import get_tigers_result

CHECK_INTERVAL = 300    # 5分ごとにチェック
MAX_WAIT_TIME  = 10800  # 最大3時間待機


def get_jst_now():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst)


def main():
    print("🐯 阪神タイガース試合結果通知BOT 起動！")

    elapsed = 0

    while elapsed <= MAX_WAIT_TIME:

        result = get_tigers_result()

        if result is None:
            print("❌ 試合結果の取得に失敗しました")
            sys.exit(1)

        print(f"⏱️ 試合状態: {result['status']}")

        # 試合中の場合は5分待って再チェック
        if result["status"] == "IN_PROGRESS":
            print(f"⚾ 試合中です。{CHECK_INTERVAL // 60}分後に再チェックします...")
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL
            continue

        # 試合なしの場合は 23時まで待ってから通知
        if result["status"] == "NO_GAME":
            now = get_jst_now()
            target_hour = 23

            if now.hour < target_hour:
                wait_seconds = (target_hour - now.hour) * 3600 - now.minute * 60 - now.second
                print(f"📅 試合なし。{target_hour}時まで {wait_seconds // 60} 分待ちます...")
                time.sleep(wait_seconds)

            # 23時になったら通知
            message = build_message(result)
            print(f"メッセージ: {message}")
            success = send_slack_notification(message)
            if not success:
                print("❌ 通知に失敗しました")
                sys.exit(1)
            print("✅ BOT 処理完了！")
            return

        # 試合終了（WIN / LOSE / DRAW）の場合はすぐ通知
        message = build_message(result)
        print(f"メッセージ: {message}")

        success = send_slack_notification(message)

        if not success:
            print("❌ 通知に失敗しました")
            sys.exit(1)

        print("✅ BOT 処理完了！")
        return

    # タイムアウト
    print("⏰ タイムアウト：試合結果を取得できませんでした")
    send_slack_notification("⏰ タイムアウト：試合結果を取得できませんでした")
    sys.exit(1)


if __name__ == "__main__":
    main()