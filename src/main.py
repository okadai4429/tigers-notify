import sys
import os
import time
from dotenv import load_dotenv

# .env ファイルのパスを明示的に指定
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from notifier import build_message, send_slack_notification
from scraper import get_tigers_result

# 設定
CHECK_INTERVAL = 300    # 5分ごとにチェック（秒）
MAX_WAIT_TIME  = 10800  # 最大3時間待機（秒）


def main():
    print("🐯 阪神タイガース試合結果通知BOT 起動！")

    elapsed = 0  # 経過時間

    while elapsed <= MAX_WAIT_TIME:

        # NPB サイトから試合結果を取得
        result = get_tigers_result()

        # 取得失敗の場合
        if result is None:
            print("❌ 試合結果の取得に失敗しました")
            sys.exit(1)

        print(f"⏱️ 試合状態: {result['status']}")

        # 試合中の場合は待機して再チェック
        if result["status"] == "IN_PROGRESS":
            print(f"⚾ 試合中です。{CHECK_INTERVAL // 60}分後に再チェックします...")
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL
            continue

        # 試合終了 or 試合なしの場合は通知して終了
        message = build_message(result)
        print(f"メッセージ: {message}")

        success = send_slack_notification(message)

        if not success:
            print("❌ 通知に失敗しました")
            sys.exit(1)

        print("✅ BOT 処理完了！")
        return

    # 3時間経過してもまだ試合中の場合
    print("⏰ タイムアウト：試合結果を取得できませんでした")
    send_slack_notification("⏰ タイムアウト：試合結果を取得できませんでした")
    sys.exit(1)


if __name__ == "__main__":
    main()