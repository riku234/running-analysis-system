# Amazon Linux 2023ベースイメージを使用
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# 作業ディレクトリを設定
WORKDIR /app

# dnfを使ってPython3とMediaPipe/OpenCV依存関係をインストール
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        git \
        glibc \
        libSM \
        libXext \
        libXrender \
        libgomp \
        mesa-libGL \
        libxcb \
        libXrandr \
        libXcursor \
        libXcomposite \
        alsa-lib \
        libXi \
        libXtst \
        gtk3 \
    && dnf clean all

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/

# ポートを公開
EXPOSE 8002

# アプリケーションを起動
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"] 