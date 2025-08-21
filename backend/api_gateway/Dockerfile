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

# フロントエンドの静的ファイルをコピー
COPY --from=frontend-builder /app/frontend/out /usr/share/nginx/html

# Nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/nginx.conf

# ポートを公開
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"] 