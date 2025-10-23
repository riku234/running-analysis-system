#!/bin/bash

echo "🚀 EC2デプロイ開始..."
echo ""

# 現在のブランチとステータス確認
echo "📊 現在のGit状態:"
git status --porcelain
echo ""

# 変更をコミット
if git status --porcelain | grep -q .; then
    echo "💾 変更をコミット..."
    git add .
    git commit -m "Fix: 個別課題の詳細解説表示問題を修正
    
- generate_detailed_advice_for_issue 関数のキー名統一
- バックエンド: description → explanation, action → exercise  
- フロントエンド: 後方互換性確保 (description || explanation)
- 統合アドバイス生成の動作確認済み"
    
    if [ $? -ne 0 ]; then
        echo "❌ コミットに失敗しました"
        exit 1
    fi
else
    echo "✅ 変更なし - コミット不要"
fi

# GitHubにプッシュ
echo "📤 GitHubにプッシュ..."
git push origin main

if [ $? -ne 0 ]; then
    echo "❌ GitHubへのプッシュに失敗しました"
    exit 1
fi

echo ""
echo "✅ デプロイ準備完了！"
echo ""
echo "🔧 EC2での実行手順:"
echo "1. ssh -i ~/.ssh/running-analysis-ec2 ec2-user@54.206.3.155"
echo "2. cd ~/running-analysis-system"
echo "3. git pull origin main"
echo "4. docker-compose down"
echo "5. docker-compose build"
echo "6. docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate"
echo "7. docker-compose restart api_gateway"
echo ""

echo "📋 確認コマンド:"
echo "- docker-compose ps"
echo "- docker-compose logs advice_generation --tail 20"
echo "- curl http://localhost:8005/"
