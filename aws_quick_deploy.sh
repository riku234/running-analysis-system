#!/bin/bash

# =============================================================================
# AWS EC2 - 迅速デプロイスクリプト
# =============================================================================

set -e

echo "🚀 AWS EC2での迅速なサービス起動を開始..."

# 設定
EC2_IP="54.206.3.155"
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"

echo "📡 EC2への接続確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "echo 'SSH接続成功'"

echo "🔄 最新コードの取得..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && git pull origin main"

echo "🐳 Dockerサービスの状態確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose ps"

echo "🔨 フロントエンド強制再ビルド..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose stop frontend && docker-compose rm -f frontend && docker image rm running-analysis-system-frontend 2>/dev/null || true && docker-compose build --no-cache frontend"

echo "⚡ サービス起動..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose up -d"

echo "⏳ サービス起動待機（30秒）..."
sleep 30

echo "✅ サービス状態確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose ps"

echo "🌐 フロントエンド接続テスト..."
curl -s http://$EC2_IP/ | head -10

echo ""
echo "🎉 デプロイ完了！"
echo "🔗 アクセス: http://$EC2_IP/" 