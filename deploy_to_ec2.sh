#!/bin/bash

# EC2接続情報
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"
EC2_USER="ec2-user"
EC2_HOST="54.206.3.155"

echo "================================================"
echo "EC2へのデプロイとテーブル作成"
echo "================================================"
echo ""

# 1. ファイルをEC2にコピー
echo "📤 ファイルをEC2にアップロード中..."
scp -i "$KEY_FILE" database_schema.sql create_tables.py ${EC2_USER}@${EC2_HOST}:~/running-analysis-system/

# 2. EC2上でGitプルと設定
ssh -i "$KEY_FILE" ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
cd ~/running-analysis-system

echo ""
echo "================================================"
echo "📥 最新のコードを取得"
echo "================================================"
git pull origin main

echo ""
echo "================================================"
echo "🔧 .envファイルの作成"
echo "================================================"

# .envファイルを作成
cat > .env << 'EOF'
# RDSデータベースへの接続情報
DB_HOST=running-analysis-db-single.cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=vfmdev_01

# Gemini API設定
GEMINI_API_KEY=******

# OpenAI API設定 (Sora-2)
OPENAI_API_KEY=******

# 動画生成パスワード
VIDEO_GENERATION_PASSWORD=xebio-generate
EOF

# 実際のAPIキーを環境変数から設定（EC2上で手動設定が必要）
echo "⚠️  注意: .envファイルのAPIキーは手動で設定してください"

echo "✅ .envファイルを作成しました"

echo ""
echo "================================================"
echo "🏗️  Dockerコンテナの再ビルド"
echo "================================================"
docker-compose build video_processing analysis advice_generation video_generation frontend api_gateway

echo ""
echo "================================================"
echo "🚀 サービスの再起動（本番環境設定）"
echo "================================================"
# 本番環境ではdocker-compose.prod.ymlを使用してENABLE_DB_SAVE=trueに設定
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo ""
echo "⏳ サービスの起動を待機中..."
sleep 10

echo ""
echo "================================================"
echo "📊 データベーステーブルの作成"
echo "================================================"

# テーブル作成スクリプトを実行
docker-compose run --rm \
  -v $(pwd)/create_tables.py:/app/create_tables.py \
  -v $(pwd)/database_schema.sql:/app/database_schema.sql \
  video_processing python3 /app/create_tables.py

echo ""
echo "================================================"
echo "✅ デプロイ完了!"
echo "================================================"
echo ""
echo "アプリケーションURL: http://54.206.3.155"
echo ""

ENDSSH

echo ""
echo "================================================"
echo "🎉 全ての作業が完了しました！"
echo "================================================"

