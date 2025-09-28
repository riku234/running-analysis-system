#!/bin/bash

echo "🚀 EC2フロントエンド強制更新開始..."

# EC2に接続してフロントエンドを再ビルド
ssh -i ~/.ssh/aws-ec2-key.pem ec2-user@54.206.3.155 << 'EOF'
echo "📂 プロジェクトディレクトリに移動..."
cd /home/ec2-user/running-analysis-system

echo "🔄 最新コードを確認..."
git pull origin main

echo "🐳 フロントエンドコンテナを停止..."
docker-compose stop frontend

echo "🗑️ 古いフロントエンドコンテナとイメージを削除..."
docker-compose rm -f frontend
docker image rm running-analysis-system-frontend 2>/dev/null || true

echo "🔨 フロントエンドを強制再ビルド..."
docker-compose build --no-cache frontend

echo "🚀 フロントエンドを再起動..."
docker-compose up -d frontend

echo "⏳ 起動待機（15秒）..."
sleep 15

echo "✅ フロントエンド状態確認..."
docker-compose ps frontend

echo "🌐 フロントエンド接続テスト..."
curl -s http://localhost:3000 | head -20
EOF

echo "🎉 EC2フロントエンド更新完了！"
echo "🔗 アクセス: http://54.206.3.155/"
