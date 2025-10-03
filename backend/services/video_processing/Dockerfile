# Amazon Linux 2023ベースイメージを使用
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# 作業ディレクトリを設定
WORKDIR /app

# dnfを使ってPython3と最小限の依存関係をインストール
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        git \
        which \
    && dnf clean all

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/
COPY db_utils.py .

# ポートを公開
EXPOSE 8001

# アプリケーションを起動
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"] 