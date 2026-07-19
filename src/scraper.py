import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import re


def get_today_str() -> tuple:
    """今日の日付を返す（JST）"""
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst)
    return today.strftime("%Y"), today.strftime("%m"), today.strftime("%m%d")


def get_tigers_result(date_str: str = None) -> dict:
    """
    NPB サイトから阪神タイガースの試合結果を取得する
    """
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst)
    year = today.strftime("%Y")
    month = today.strftime("%m")
    mmdd = today.strftime("%m%d") if date_str is None else date_str

    # 月別スケジュールページから今日の阪神の試合リンクを探す
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

        # 今日の阪神の試合リンクを探す
        # URLパターン: /scores/2026/MMDD/[X]-t-01/ または /scores/2026/MMDD/t-[X]-01/
        game_link = None
        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link["href"]
            # 今日の日付 + 阪神（t）が含まれるリンクを探す
            if f"/scores/{year}/{mmdd}/" in href and "-t-" in href or \
               f"/scores/{year}/{mmdd}/" in href and "/t-" in href:
                game_link = href
                break

        if not game_link:
            print("📅 本日は阪神の試合がありませんでした")
            return {"status": "NO_GAME", "score": "", "opponent": "", "home_runs": []}

        # 試合結果ページを取得
        if not game_link.startswith("http"):
            game_link = f"https://npb.jp{game_link}"

        print(f"🔍 試合結果を取得中: {game_link}")
        game_response = requests.get(game_link, headers=headers, timeout=10)
        game_response.encoding = "utf-8"

        if game_response.status_code != 200:
            print(f"⚾ 試合中の可能性があります")
            return {"status": "IN_PROGRESS", "score": "", "opponent": "", "home_runs": []}

        game_soup = BeautifulSoup(game_response.text, "html.parser")

        # スコアテーブルを取得
        score_table = game_soup.find("table", class_="scoreBoard")

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
                total_score = score_cells[-1].get_text(strip=True)
                teams.append(team_name)
                scores.append(total_score)

        if len(teams) < 2 or len(scores) < 2:
            print("⚾ 試合中です")
            return {"status": "IN_PROGRESS", "score": "", "opponent": "", "home_runs": []}

        # 阪神のインデックスを探す
        hanshin_idx = None
        for i, team in enumerate(teams):
            if "阪神" in team or "Ｔ" in team:
                hanshin_idx = i
                break

        if hanshin_idx is None:
            print("❌ 阪神の試合データが見つかりませんでした")
            return None

        opponent_idx = 1 if hanshin_idx == 0 else 0

        # スコアが数字かチェック（試合中は数字でない場合がある）
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

        # 勝敗判定
        if hanshin_score > opponent_score:
            status = "WIN"
        elif hanshin_score < opponent_score:
            status = "LOSE"
        else:
            status = "DRAW"

        # ホームラン情報を取得
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
        # ホームラン情報を含むテキストを探す
        hr_tables = soup.find_all("table")

        for table in hr_tables:
            rows = table.find_all("tr")
            is_hanshin_section = False

            for row in rows:
                cells = row.find_all(["th", "td"])
                if not cells:
                    continue

                text = cells[0].get_text(strip=True)

                if "阪神" in text or "Ｔ" in text:
                    is_hanshin_section = True
                    continue

                # 他チームのセクションに入ったらリセット
                if is_hanshin_section and any(
                    team in text for team in ["巨人", "中日", "広島", "ヤクルト",
                                              "DeNA", "横浜", "ソフトバンク",
                                              "ロッテ", "楽天", "日本ハム",
                                              "西武", "オリックス"]
                ):
                    is_hanshin_section = False
                    continue

                if is_hanshin_section:
                    full_text = row.get_text(strip=True)
                    match = re.search(r"(.+?)(\d+)号", full_text)
                    if match:
                        player_name = match.group(1).strip()
                        hr_number = int(match.group(2))
                        if player_name and len(player_name) < 10:
                            home_runs.append({
                                "player": player_name,
                                "number": hr_number
                            })

    except Exception as e:
        print(f"⚠️ ホームラン情報の取得に失敗しました: {e}")

    return home_runs