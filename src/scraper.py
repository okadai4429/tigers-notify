import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import re


def get_today_str() -> tuple:
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst)
    return today.strftime("%Y"), today.strftime("%m"), today.strftime("%m%d")


def get_tigers_result(date_str: str = None) -> dict:
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst)
    year = today.strftime("%Y")
    month = today.strftime("%m")
    mmdd = today.strftime("%m%d") if date_str is None else date_str

    schedule_url = f"https://npb.jp/games/{year}/schedule_{month}_detail.html"
    print(f"🔍 スケジュールページを取得中: {schedule_url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(schedule_url, headers=headers, timeout=10)
        response.encoding = "utf-8"

        if response.status_code != 200:
            print(f"❌ スケジュールページの取得に失敗しました: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        game_link = None
        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link["href"]
            if f"/scores/{year}/{mmdd}/" in href and (
                "-t-" in href or href.split("/")[-2].startswith("t-")
            ):
                game_link = href
                break

        if not game_link:
            print("📅 本日は阪神の試合がありませんでした")
            return {"status": "NO_GAME", "score": "", "opponent": "", "home_runs": []}

        if not game_link.startswith("http"):
            game_link = f"https://npb.jp{game_link}"

        print(f"🔍 試合結果を取得中: {game_link}")
        game_response = requests.get(game_link, headers=headers, timeout=10)
        game_response.encoding = "utf-8"

        if game_response.status_code != 200:
            print(f"⚾ 試合中の可能性があります")
            return {"status": "IN_PROGRESS", "score": "", "opponent": "", "home_runs": []}

        game_soup = BeautifulSoup(game_response.text, "html.parser")

        # クラスなしの全テーブルから探す
        tables = game_soup.find_all("table")
        score_table = None

        for t in tables:
            text = t.get_text()
            if "阪神" in text or "Ｔ" in text:
                score_table = t
                break

        if not score_table:
            print("⚾ 試合中です（スコアボードなし）")
            return {"status": "IN_PROGRESS", "score": "", "opponent": "", "home_runs": []}

        rows = score_table.find_all("tr")
        teams = []
        scores = []

        for row in rows:
            team_cell = row.find("th")
            score_cells = row.find_all("td")

            if team_cell and score_cells:
                team_name = team_cell.get_text(strip=True)
                total_score = score_cells[-3].get_text(strip=True)
                # 空のチーム名とヘッダー行を除外
                if team_name and total_score != "計":
                    teams.append(team_name)
                    scores.append(total_score)

        if len(teams) < 2 or len(scores) < 2:
            print("⚾ 試合中です")
            return {"status": "IN_PROGRESS", "score": "", "opponent": "", "home_runs": []}

        hanshin_idx = None
        for i, team in enumerate(teams):
            if "阪神" in team or "Ｔ" in team:
                hanshin_idx = i
                break

        if hanshin_idx is None:
            print("❌ 阪神の試合データが見つかりませんでした")
            return None

        opponent_idx = 1 if hanshin_idx == 0 else 0

        try:
            hanshin_score = int(scores[hanshin_idx])
            opponent_score = int(scores[opponent_idx])
        except ValueError:
            print("⚾ 試合中です")
            return {
                "status": "IN_PROGRESS",
                "score": f"{scores[hanshin_idx]}-{scores[opponent_idx]}",
                "opponent": teams[opponent_idx],
                "home_runs": []
            }

        # 試合終了チェック（勝投手の存在確認）
        page_text = game_soup.get_text()
        if "勝投手" not in page_text and "引分" not in page_text:
            print("⚾ 試合中です（勝投手未確定）")
            return {
                "status": "IN_PROGRESS",
                "score": f"{hanshin_score}-{opponent_score}",
                "opponent": teams[opponent_idx],
                "home_runs": []
            }
        if hanshin_score > opponent_score:
            status = "WIN"
        elif hanshin_score < opponent_score:
            status = "LOSE"
        else:
            status = "DRAW"

        home_runs = get_home_runs(game_soup)

        print(f"✅ 試合結果取得成功: {status} {hanshin_score}-{opponent_score}")

        return {
            "status": status,
            "score": f"{hanshin_score}-{opponent_score}",
            "opponent": teams[opponent_idx],
            "home_runs": home_runs
        }

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return None

def get_home_runs(soup) -> list:
    """ホームラン情報を取得する"""
    home_runs = []

    try:
        import re
        tables = soup.find_all("table")

        for table in tables:
            text = table.get_text(strip=True)

            # 「号」が含まれるテーブルだけホームラン情報
            if "【阪神】" not in text or "号" not in text:
                continue

            # 阪神のホームラン部分を抽出
            hanshin_match = re.search(
                r"【阪神】(.+?)(?:【|$)", text
            )
            if not hanshin_match:
                continue

            hanshin_hr_text = hanshin_match.group(1)

            # "佐藤33号" のパターンを抽出
            hr_matches = re.findall(
                r"([^\s、（）]+?)(\d+)号", hanshin_hr_text
            )

            for player_name, hr_number in hr_matches:
                player_name = player_name.strip()
                if player_name:
                    home_runs.append({
                        "player": player_name,
                        "number": int(hr_number)
                    })
            break

    except Exception as e:
        print(f"⚠️ ホームラン情報の取得に失敗しました: {e}")

    return home_runs