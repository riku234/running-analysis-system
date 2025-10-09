FROM public.ecr.aws/amazonlinux/amazonlinux:2023

WORKDIR /app

# システムパッケージのインストール
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        git \
        which \
    && dnf clean all

# 依存関係のインストール
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/

# ポートを公開
EXPOSE 8006

# サービスを起動
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]

