import sys
import os
from dotenv import load_dotenv

# .env ファイルのパスを明示的に指定
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from notifier import build_message, send_slack_notification


def main():
    print("🐯 阪神タイガース試合結果通知BOT 起動！")

    # テスト用のダミーデータ（後で scraper.py に置き換える）
    result = {
        "status": "WIN",
        "score": "5-2",
        "opponent": "読売ジャイアンツ"
    }

    # メッセージを生成
    message = build_message(result)
    print(f"メッセージ: {message}")

    # Slack に通知
    success = send_slack_notification(message)

    if not success:
        print("❌ 通知に失敗しました")
        sys.exit(1)

    print("✅ BOT 処理完了！")


if __name__ == "__main__":
    main()