# 🐯 阪神タイガース 試合結果通知 BOT

> **毎日18時に自動起動 → NPBから試合結果をスクレイピング → Slackに通知**  
> Python / Docker / AWS / Terraform / GitHub Actions で構築した個人開発プロジェクト

---

## 📌 プロジェクト概要

個人学習として構築した  
**インフラ自動化プロジェクト**です。

「毎日 Slack で阪神の試合結果を受け取りたい」という実用的なユースケースをベースに、  
Git・Docker・AWS・Terraform・GitHub Actions を実践的に学びながら構築しました。

---

## 🏗️ システム構成図

```
┌─────────────────────────────────────────────────────────┐
│                     開発フロー                            │
│                                                          │
│  ローカル開発  →  git push  →  GitHub Actions           │
│                               ↓                         │
│                          docker build                    │
│                               ↓                         │
│                          ECR push                       │
│                               ↓                         │
│                       ECS サービス更新                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   本番稼働フロー（毎日自動）                │
│                                                          │
│  EventBridge（毎日18:00 JST）                            │
│         ↓ トリガー                                       │
│  ECS Fargate（コンテナ起動）                              │
│         ↓                                                │
│  scraper.py（NPB公式サイトをスクレイピング）               │
│         ↓ 試合中の場合は5分後に再チェック（最大3時間）     │
│  notifier.py（試合結果・ホームラン情報を整形）             │
│         ↓                                                │
│  Slack Webhook（#阪神タイガース試合結果bot に通知）        │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 使用技術

### アプリケーション

| 技術 | バージョン | 用途 |
|---|---|---|
| Python | 3.11 | スクレイパー・通知処理本体 |
| requests | 2.32.3 | NPB サイトへの HTTP リクエスト |
| BeautifulSoup4 | 4.12.3 | HTML 解析・スクレイピング |
| python-dotenv | 1.0.1 | 環境変数管理 |

### インフラ・DevOps

| 技術 | バージョン | 用途 |
|---|---|---|
| Docker | 29.1.3 | コンテナ化 |
| AWS ECR | - | Docker イメージ管理 |
| AWS ECS Fargate | - | サーバーレスコンテナ実行 |
| AWS EventBridge | - | 定時実行スケジューラー |
| AWS CloudWatch Logs | - | コンテナログ収集・監視 |
| AWS S3 | - | Terraform tfstate 管理 |
| AWS IAM | - | 最小権限によるアクセス制御 |
| Terraform | 1.15.8 | インフラのコード化（IaC） |
| GitHub Actions | - | CI/CD パイプライン |

---

## 📁 ディレクトリ構成

```
tigers-notify/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD パイプライン
├── infra/                      # Terraform インフラコード
│   ├── backend.tf              # S3 バックエンド設定
│   ├── provider.tf             # AWS プロバイダー設定
│   ├── variables.tf            # 変数定義
│   ├── vpc.tf                  # VPC・サブネット・IGW・ルートテーブル
│   ├── iam.tf                  # IAM ロール・ポリシー
│   ├── ecs.tf                  # ECS クラスター・タスク定義・SG
│   ├── eventbridge.tf          # EventBridge スケジュールルール
│   └── outputs.tf              # 出力値
├── src/
│   ├── scraper.py              # NPBスクレイピング処理
│   ├── notifier.py             # Slack通知処理
│   └── main.py                 # エントリーポイント・試合終了検知ループ
├── tests/
│   └── test_scraper.py
├── Dockerfile                  # python:3.11-slim ベース
├── .dockerignore
├── docker-compose.yml          # ローカル開発環境
└── requirements.txt
```

---

## ☁️ AWS インフラ構成

### VPC設計（ネットワーク）

```
VPC: tigers-notify-vpc（10.0.0.0/16）
├── パブリックサブネット1（10.0.1.0/24）ap-northeast-1a
├── パブリックサブネット2（10.0.2.0/24）ap-northeast-1c
└── インターネットゲートウェイ → ルートテーブル（0.0.0.0/0）
```

### ECS Fargate 設定

```
クラスター: tigers-notify-cluster
タスク定義: tigers-notify
  - CPU: 256（0.25 vCPU）
  - メモリ: 512MB
  - ネットワークモード: awsvpc
  - ログ: CloudWatch Logs（/ecs/tigers-notify）
```

### IAM 設計（最小権限の原則）

```
ECS タスク実行ロール
├── AmazonECSTaskExecutionRolePolicy（ECR pull・CloudWatch Logs）
├── AmazonSSMReadOnlyAccess
└── カスタムポリシー（logs:CreateLogGroup）

EventBridge 実行ロール
└── AmazonECS_FullAccess
```

### Terraform で管理するリソース（全17個）

| カテゴリ | リソース数 | 主なリソース |
|---|---|---|
| ネットワーク | 7 | VPC・サブネット×2・IGW・ルートテーブル×2・association×2 |
| コンピューティング | 3 | ECS クラスター・タスク定義・セキュリティグループ |
| IAM | 5 | ロール×2・ポリシーアタッチメント×3 |
| スケジューラー | 2 | EventBridge ルール・ターゲット |

---

## ⚙️ CI/CD パイプライン

```
main ブランチに push
        ↓
GitHub Actions 起動（deploy.yml）
        ↓
1. AWS 認証（GitHub Secrets から取得）
2. ECR ログイン
3. docker build（タグ: github.sha）
4. ECR push
5. ECS タスク定義を新イメージで更新
6. ECS サービスをローリングデプロイ
        ↓
約10分で本番環境に反映
```

### GitHub Secrets で管理する秘密情報

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
SLACK_WEBHOOK_URL
```

---

## 🔄 BOT の処理フロー詳細

```python
# main.py の処理ロジック
while 経過時間 <= 3時間:
    result = get_tigers_result()  # NPBスクレイピング

    if result["status"] == "IN_PROGRESS":
        5分待機して再チェック  # 試合中は繰り返し確認
    else:
        Slack に通知して終了   # 試合終了・試合なし

3時間経過 → タイムアウト通知
```

### Slack 通知の例

```
🎉 *勝利！* 阪神タイガース 7-4 東京ヤクルトスワローズ
バンザーーイ！！六甲おろしにー颯爽と🐯
　🏠 佐藤輝明 33号
　🏠 佐藤輝明 34号

😢 *敗戦...* 阪神タイガース 2-5 読売ジャイアンツ
次は頑張れ！ファイト🐯

📅 本日は試合がありませんでした。
```

---

## 🚀 環境構築手順

### 前提条件

- Python 3.11+
- Docker Desktop
- AWS CLI（`aws configure` 設定済み）
- Terraform 1.0+

### ローカル実行

```bash
# リポジトリをクローン
git clone https://github.com/okadai4429/tigers-notify.git
cd tigers-notify

# 依存パッケージをインストール
python -m pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env に SLACK_WEBHOOK_URL を設定

# ローカルで実行
python src/main.py
```

### Docker で実行

```bash
# イメージをビルド
docker build -t tigers-notify:latest .

# コンテナを実行
docker run --rm \
  -e SLACK_WEBHOOK_URL=your_webhook_url \
  tigers-notify:latest
```

### AWS インフラの構築（Terraform）

```bash
cd infra

# 初期化
terraform init

# 実行計画の確認
terraform plan

# インフラ構築（17リソースが一括作成）
terraform apply

# インフラ削除（課金停止）
terraform destroy
```

---

## 📊 コスト見積もり

| サービス | 月額（概算） | 備考 |
|---|---|---|
| ECS Fargate | 約 $0.03〜0.09 | 1日1回・数分の実行のみ |
| ECR | 約 $0.03 | イメージ保存料 |
| S3 | 約 $0.01 | tfstate 保存料 |
| CloudWatch Logs | 約 $0.01 | ログ保存料 |
| **合計** | **約 $0.10〜0.15** | **（約15〜22円/月）** |

> AWS Budgets で月 $10 のアラートを設定済み

---

## 🔧 ネットワークエンジニアとしての技術的考察

本プロジェクトを通じて、オンプレミスのネットワーク知識がクラウドにどう対応するかを体系的に習得しました。

| オンプレミス | AWS | 本プロジェクトでの用途 |
|---|---|---|
| プライベートネットワーク | VPC | ECS タスクの実行環境 |
| VLAN | サブネット | パブリックサブネット×2（冗長化） |
| デフォルトゲートウェイ | IGW | インターネットへの出口 |
| ACL | セキュリティグループ | アウトバウンド全許可・インバウンド全拒否 |
| サーバー | EC2 / ECS Fargate | サーバーレスでコンテナを実行 |
| cron ジョブ | EventBridge | 毎日18時の定時実行 |
| ログサーバー | CloudWatch Logs | コンテナログの集中管理 |

### awsvpc モードの採用理由

ECS Fargate には `bridge` / `host` / `awsvpc` の3つのネットワークモードがありますが、  
`awsvpc` を採用することで以下のメリットを得ました。

- コンテナに直接 ENI が割り当てられるため、**セキュリティグループを直接適用可能**
- VPC フローログでコンテナ単位のトラフィック監視が可能
- ネットワークエンジニアの既存知識（VLAN・ACL設計）をそのまま活用できる

---

## 📝 学習記録

### 習得したスキル

- **Git**: commit / branch / merge / コンフリクト解消 / GitHub フロー
- **Docker**: Dockerfile 作成 / レイヤー最適化 / docker-compose / .dockerignore
- **AWS**: IAM 最小権限設計 / VPC 設計 / ECS Fargate / ECR / EventBridge / CloudWatch
- **Terraform**: HCL 構文 / 変数・参照・jsonencode / S3 バックエンド / IaC の考え方
- **GitHub Actions**: CI/CD パイプライン / Secrets 管理 / 自動デプロイ
- **Python**: スクレイピング（requests / BeautifulSoup）/ 正規表現 / 環境変数管理

## 🔗 関連リンク

- [NPB 公式サイト](https://npb.jp)
- [AWS ECS Fargate ドキュメント](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## 👤 作者

**岡本大輝**  

---

*このプロジェクトは個人学習・ポートフォリオ目的で作成しています。*
