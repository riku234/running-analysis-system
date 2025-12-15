#!/bin/bash

# =============================================================================
# AWS EC2 - 迅速デプロイスクリプト（ルールベース機能対応版）
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

echo "📋 .envファイルをEC2にコピー..."
if [ -f ".env" ]; then
    scp -i "$KEY_FILE" .env ec2-user@$EC2_IP:~/running-analysis-system/.env
    echo "   ✅ .envファイルをコピーしました"
else
    echo "   ⚠️  .envファイルが見つかりません（スキップ）"
fi

echo "🐳 Dockerサービスの状態確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose ps"

echo "🔨 全サービスを再ビルド..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose -f docker-compose.yml -f docker-compose.prod.yml build"

echo "📌 APIキー反映のため、advice_generationとvideo_generationを強制再作成します"
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate advice_generation video_generation"

echo "📌 その他のサービスを起動します"
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"

echo "⏳ サービス起動待機（30秒）..."
sleep 30

echo "✅ サービス状態確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose ps"

echo "🌐 フロントエンド接続テスト..."
curl -s http://$EC2_IP/ | head -10

echo ""
echo "🎉 デプロイ完了！"
echo "🔗 アクセス: http://$EC2_IP/"
echo ""
echo "📋 確認コマンド:"
echo "   ssh -i \"$KEY_FILE\" ec2-user@$EC2_IP \"cd running-analysis-system && docker-compose logs advice_generation --tail 20\"" 