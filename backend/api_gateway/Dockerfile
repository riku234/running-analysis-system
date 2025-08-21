# マルチステージビルド: フロントエンドビルド
FROM node:18-alpine AS frontend-builder

# フロントエンドのビルド
WORKDIR /app/frontend
COPY ../../frontend/package*.json ./
RUN npm ci --only=production

COPY ../../frontend/ ./
RUN npm run build

# Nginx本体
FROM nginx:1.25-alpine

# デフォルトのNginx設定を削除
RUN rm /etc/nginx/conf.d/default.conf

# HTMLディレクトリを確実に作成し、基本的なindex.htmlを作成
RUN mkdir -p /usr/share/nginx/html && \
    echo '<!DOCTYPE html><html><head><title>Running Analysis System</title><meta charset="utf-8"></head><body><h1>🏃‍♂️ Running Analysis System</h1><p>システムを読み込み中...</p><p>しばらくお待ちください。</p></body></html>' > /usr/share/nginx/html/index.html

# Nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ポートを公開
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"] 