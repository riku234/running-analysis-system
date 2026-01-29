#!/bin/bash

# =============================================================================
# ピッチ非表示修正のデプロイスクリプト
# =============================================================================
# エンターを押すだけで、GitHubへのプッシュとEC2へのデプロイを実行します
# =============================================================================

set -e

echo "🚀 ピッチ非表示修正のデプロイを開始..."
echo ""

# 設定
EC2_IP="54.206.3.155"
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"
PROJECT_DIR="/Users/onoriku/Projects/running-analysis-system"

cd "$PROJECT_DIR"

# ステップ1: GitHubへのプッシュを試行
echo "📤 ステップ1: GitHubへのプッシュを試行..."
if git push origin main 2>&1; then
    echo "   ✅ GitHubへのプッシュ成功"
    USE_GIT_PULL=true
else
    echo "   ⚠️  GitHubへのプッシュ失敗（認証エラーの可能性）"
    echo "   📋 EC2に直接ファイルをコピーします"
    USE_GIT_PULL=false
fi

echo ""

# ステップ2: EC2への接続確認
echo "📡 ステップ2: EC2への接続確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "echo 'SSH接続成功'"

# ステップ3: コードの反映
if [ "$USE_GIT_PULL" = true ]; then
    echo "🔄 ステップ3: EC2で最新コードを取得..."
    ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && git pull origin main"
else
    echo "📋 ステップ3: EC2に直接ファイルをコピー..."
    scp -i "$KEY_FILE" "$PROJECT_DIR/frontend/app/result/[id]/page.tsx" ec2-user@$EC2_IP:~/running-analysis-system/frontend/app/result/\[id\]/page.tsx
    echo "   ✅ ファイルをコピーしました"
fi

# ステップ4: フロントエンドを再ビルド
echo "🔨 ステップ4: フロントエンドを再ビルド..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose -f docker-compose.yml -f docker-compose.prod.yml build frontend"

# ステップ5: フロントエンドを再起動
echo "🚀 ステップ5: フロントエンドを再起動..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate frontend"

# ステップ6: 起動待機
echo "⏳ ステップ6: 起動待機（10秒）..."
sleep 10

# ステップ7: 状態確認
echo "✅ ステップ7: サービス状態確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "cd running-analysis-system && docker-compose ps frontend"

echo ""
echo "🎉 デプロイ完了！"
echo "🔗 アクセス: http://$EC2_IP/"
echo ""
echo "📋 ピッチが非表示になっているか確認してください"
