#!/bin/bash

# =============================================================================
# AWS EC2 - 最新版デプロイスクリプト
# =============================================================================
# 
# 【使用方法】
# chmod +x deploy_latest.sh
# ./deploy_latest.sh
#
# 【目的】
# 既存の環境を保持しつつ、最新版のコードを取得・デプロイします
# =============================================================================

set -e  # エラーが発生した場合にスクリプトを停止

echo "🚀 最新版のデプロイを開始します..."

# 設定変数
PROJECT_DIR="running-analysis-system"
GEMINI_API_KEY="AIzaSyAt7xxYvsvXaWCPyEhslP0YqX97RacpSYU"

echo "📋 設定確認:"
echo "   プロジェクトディレクトリ: ${PROJECT_DIR}"
echo ""

# プロジェクトディレクトリの確認
if [ ! -d "${HOME}/${PROJECT_DIR}" ]; then
    echo "❌ エラー: ${PROJECT_DIR}ディレクトリが見つかりません"
    echo "   まず reset_and_build.sh を実行してください"
    exit 1
fi

# プロジェクトディレクトリに移動
cd "${HOME}/${PROJECT_DIR}"
echo "📁 プロジェクトディレクトリに移動: $(pwd)"

# 現在のDockerサービスを停止
echo "🛑 ステップ1: 既存サービスの停止"
if command -v docker-compose &> /dev/null; then
    echo "   Docker Compose v1を使用してサービスを停止中..."
    docker-compose down || true
elif docker compose version &> /dev/null; then
    echo "   Docker Compose v2を使用してサービスを停止中..."
    docker compose down || true
else
    echo "   ⚠️  Docker Composeが見つかりません（スキップ）"
fi
echo "   ✅ サービスを停止しました"

# Gitから最新版を取得
echo "📥 ステップ2: 最新版のコードを取得"
echo "   現在のブランチ: $(git branch --show-current)"
echo "   最新のコミットを取得中..."

# 変更を保存（stash）
git stash push -m "Auto-stash before deploy $(date)"

# 最新版を取得
git fetch origin
git reset --hard origin/main

echo "   ✅ 最新版のコードを取得しました"
echo "   最新のコミット: $(git log --oneline -1)"

# 環境変数の確認・更新
echo "🔐 ステップ3: 環境変数の確認"
if [ ! -f ".env" ]; then
    echo "   .envファイルが見つかりません。作成中..."
    cat > .env << EOF
# =============================================================================
# 環境変数設定ファイル
# 生成日時: $(date)
# =============================================================================

# Gemini API Key for advice generation service
GEMINI_API_KEY=${GEMINI_API_KEY}

# Application Environment
NODE_ENV=production

# Docker Compose Settings
COMPOSE_PROJECT_NAME=running-analysis-system
EOF
    chmod 600 .env
    echo "   ✅ .envファイルを作成しました"
else
    echo "   ✅ .envファイルが存在します"
fi

# Dockerイメージの再ビルド・起動
echo "🐳 ステップ4: Dockerサービスの再ビルド・起動"
echo "   全サービスを再ビルド・起動中..."
echo "   （この処理には数分かかる場合があります）"

if command -v docker-compose &> /dev/null; then
    echo "   Docker Compose v1を使用"
    docker-compose up --build -d
elif docker compose version &> /dev/null; then
    echo "   Docker Compose v2を使用"
    docker compose up --build -d
else
    echo "   ❌ エラー: Docker Composeが見つかりません"
    exit 1
fi

echo "   ✅ 全サービスの再ビルド・起動が完了しました"

# 最終確認
echo "🔍 ステップ5: 最終確認"
echo "   サービス稼働状況を確認中..."

if command -v docker-compose &> /dev/null; then
    docker-compose ps
elif docker compose version &> /dev/null; then
    docker compose ps
fi

echo ""
echo "🎉 最新版のデプロイが完了しました！"
echo ""
echo "📋 【確認事項】"
echo "   - 全サービスが 'Up' 状態であることを確認してください"
echo "   - フロントエンドサービス: http://$(curl -s ifconfig.me):80"
echo "   - API Gateway: http://$(curl -s ifconfig.me):80/api/"
echo ""
echo "🔧 【ログ確認コマンド】"
if command -v docker-compose &> /dev/null; then
    echo "   全サービスログ: docker-compose logs -f"
    echo "   特定サービス: docker-compose logs -f [サービス名]"
else
    echo "   全サービスログ: docker compose logs -f"
    echo "   特定サービス: docker compose logs -f [サービス名]"
fi
echo ""
echo "📊 【システム情報】"
echo "   最新コミット: $(git log --oneline -1)"
echo "   デプロイ日時: $(date)"
echo "   外部IP: $(curl -s ifconfig.me)"
