# ベースイメージ（Python 3.11 軽量版）
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY src/ ./src/

# 起動コマンド
CMD ["python", "src/main.py"]