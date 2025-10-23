#!/bin/bash

echo "🔐 EC2接続テスト開始..."
echo ""

# SSH接続テスト
ssh -i ~/.ssh/running-analysis-ec2 -o ConnectTimeout=10 ec2-user@54.206.3.155 "echo '✅ EC2接続成功！' && hostname && whoami"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 接続テスト成功！"
    echo "次のステップ: GitHubへのプッシュとデプロイができます"
else
    echo ""
    echo "❌ 接続に失敗しました"
    echo "公開鍵がEC2の ~/.ssh/authorized_keys に正しく追加されているか確認してください"
fi







