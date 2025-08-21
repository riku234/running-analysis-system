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

# 基本的なindex.htmlを作成（フロントエンドビルドが失敗した場合のフォールバック）
RUN echo '<!DOCTYPE html><html><head><title>Running Analysis System</title></head><body><h1>Running Analysis System</h1><p>Loading...</p></body></html>' > /etc/nginx/html/index.html

# Nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ポートを公開
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"] 