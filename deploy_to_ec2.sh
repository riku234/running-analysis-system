#!/bin/bash

# EC2接続情報
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"
EC2_USER="ec2-user"
EC2_HOST="54.206.3.155"

echo "================================================"
echo "EC2へのデプロイとテーブル作成"
echo "================================================"
echo ""

# 1. ファイルをEC2にコピー（.envファイルも含める）
echo "📤 ファイルをEC2にアップロード中..."
scp -i "$KEY_FILE" database_schema.sql create_tables.py .env ${EC2_USER}@${EC2_HOST}:~/running-analysis-system/
echo "✅ .envファイルを含むすべてのファイルをアップロードしました"

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
echo "🔧 .envファイルの確認"
echo "================================================"
echo "✅ ローカルの.envファイルがアップロード済みです"

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
# advice_generationとvideo_generationは環境変数を確実に反映するため強制再作成
echo "📌 APIキー反映のため、advice_generationとvideo_generationを強制再作成します"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate advice_generation video_generation

echo "📌 その他のサービスを起動します"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo ""
echo "⏳ サービスの起動を待機中..."
sleep 15

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

