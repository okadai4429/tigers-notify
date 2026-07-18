import os
import requests
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def build_message(result: dict) -> str:
    """試合結果に応じてメッセージを生成する"""

    if result["status"] == "WIN":
        return (
            f"🎉 *勝利！* 阪神タイガース {result['score']} {result['opponent']}\n"
            f"六甲おろしに颯々たる⚡ やったぞ！"
        )
    elif result["status"] == "LOSE":
        return (
            f"😢 *敗戦...* 阪神タイガース {result['score']} {result['opponent']}\n"
            f"次は頑張れ！ファイト🐯"
        )
    elif result["status"] == "DRAW":
        return (
            f"🤝 *引き分け* 阪神タイガース {result['score']} {result['opponent']}\n"
            f"惜しかった！次回に期待！"
        )
    else:
        return "📅 本日は試合がありませんでした。"


def send_slack_notification(message: str) -> bool:
    """Slack に通知を送信する"""

    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL が設定されていません")
        return False

    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)

    if response.status_code == 200:
        print("✅ Slack 通知を送信しました")
        return True
    else:
        print(f"❌ Slack 通知の送信に失敗しました: {response.status_code}")
        return False