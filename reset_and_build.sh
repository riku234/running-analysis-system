#!/bin/bash

# =============================================================================
# AWS EC2 - 開発環境完全リセット・再構築スクリプト
# =============================================================================
# 
# 【使用方法】
# chmod +x reset_and_build.sh
# ./reset_and_build.sh
#
# 【目的】
# 既存の開発環境を完全に削除し、GitHubから再クローン・再ビルドします
# 
# 【重要な注意事項】
# - このスクリプトはGEMINI_API_KEYを含むため、取り扱いに十分注意してください
# - 既存の全てのデータ・設定・ログが削除されます
# - 本番環境では実行しないでください
# =============================================================================

# ===== 1. 安全な実行のための設定 =====
set -e  # エラーが発生した場合にスクリプトを停止
set -x  # 実行されるコマンドをターミナルに表示

echo "🚀 AWS EC2 開発環境の完全リセット・再構築を開始します..."
echo "⚠️  注意: 既存の全てのデータが削除されます！"

# ===== 設定変数 =====
# 【重要】以下のGitHubリポジトリURLとAPIキーを環境に合わせて変更してください
GITHUB_REPO_URL="https://github.com/riku234/running-analysis-system.git"
GEMINI_API_KEY="AIzaSyAt7xxYvsvXaWCPyEhslP0YqX97RacpSYU"  # 🚨 実際のAPIキーに変更してください

# プロジェクトディレクトリ名
PROJECT_DIR="running-analysis-system"

echo "📋 設定確認:"
echo "   GitHubリポジトリ: ${GITHUB_REPO_URL}"
echo "   プロジェクトディレクトリ: ${PROJECT_DIR}"
echo ""

# ===== 2. 既存環境の完全なクリーンアップ =====
echo "🧹 ステップ1: 既存環境の完全クリーンアップ"

# 現在のディレクトリを記録
ORIGINAL_DIR=$(pwd)

# プロジェクトディレクトリが存在する場合の処理
if [ -d "${HOME}/${PROJECT_DIR}" ]; then
    echo "   既存の${PROJECT_DIR}ディレクトリが見つかりました"
    
    # プロジェクトディレクトリに移動
    cd "${HOME}/${PROJECT_DIR}"
    
    # Docker Composeサービス停止・削除
    echo "   Docker Composeサービスを停止中..."
    if [ -f "docker-compose.yml" ]; then
        # Docker Compose v1とv2の両方に対応
        if command -v docker-compose &> /dev/null; then
            docker-compose down || true
        elif docker compose version &> /dev/null; then
            docker compose down || true
        else
            echo "   Docker Composeが見つかりません（スキップ）"
        fi
    else
        echo "   docker-compose.ymlが見つかりません（スキップ）"
    fi
    
    # ホームディレクトリに戻る
    cd "${HOME}"
    
    # プロジェクトディレクトリ全体を削除
    echo "   ${PROJECT_DIR}ディレクトリを完全削除中..."
    rm -rf "${PROJECT_DIR}"
    echo "   ✅ ${PROJECT_DIR}ディレクトリを削除しました"
else
    echo "   ${PROJECT_DIR}ディレクトリは存在しません（スキップ）"
fi

# Dockerシステムの徹底的なクリーンアップ
echo "   Dockerシステムを徹底クリーンアップ中..."
docker system prune -a -f || {
    echo "   ⚠️  Docker system pruneに失敗しましたが続行します"
}
echo "   ✅ Dockerシステムのクリーンアップ完了"

echo ""

# ===== 3. GitHubからの再クローン =====
echo "📥 ステップ2: GitHubからの再クローン"

# ホームディレクトリにいることを確認
cd "${HOME}"

# GitHubからクローン
echo "   リポジトリをクローン中: ${GITHUB_REPO_URL}"
git clone "${GITHUB_REPO_URL}"
echo "   ✅ クローン完了"

echo ""

# ===== 4. プロジェクトディレクトリへの移動 =====
echo "📁 ステップ3: プロジェクトディレクトリへの移動"

cd "${HOME}/${PROJECT_DIR}"
echo "   現在のディレクトリ: $(pwd)"
echo "   ✅ プロジェクトディレクトリに移動しました"

echo ""

# ===== 5. 機密情報の設定 =====
echo "🔐 ステップ4: 環境変数設定"

# 既存の.envファイルをチェック
if [ -f ".env" ]; then
    echo "   既存の.envファイルが見つかりました（バックアップ作成）"
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    rm .env
fi

# 新しい.envファイルを作成
echo "   .envファイルを作成中..."
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

echo "   ✅ .envファイルを作成しました"

# .envファイルのパーミッション設定（セキュリティ向上）
chmod 600 .env
echo "   ✅ .envファイルのパーミッションを設定しました (600)"

echo ""

# ===== 6. アプリケーションのビルドと起動 =====
echo "🐳 ステップ5: Dockerアプリケーションのビルド・起動"

echo "   全サービスをゼロからビルド・起動中..."
echo "   （この処理には数分かかる場合があります）"

# Docker Compose v1とv2の両方に対応
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

echo "   ✅ 全サービスのビルド・起動が完了しました"

echo ""

# ===== 7. 最終確認 =====
echo "🔍 ステップ6: 最終確認"

echo "   サービス稼働状況を確認中..."

# Docker Compose v1とv2の両方に対応
if command -v docker-compose &> /dev/null; then
    docker-compose ps
elif docker compose version &> /dev/null; then
    docker compose ps
fi

echo ""
echo "🎉 開発環境の完全リセット・再構築が完了しました！"
echo ""
echo "📋 【確認事項】"
echo "   - 全サービスが 'Up' 状態であることを確認してください"
echo "   - フロントエンドサービス: http://$(curl -s ifconfig.me):80"
echo "   - API Gateway: http://$(curl -s ifconfig.me):80/api/"
echo ""
echo "🔧 【次のステップ】"
echo "   1. ブラウザでアプリケーションにアクセス"
echo "   2. 動画アップロード機能のテスト"
echo "   3. 各マイクロサービスの動作確認"
echo ""
echo "📊 【ログ確認コマンド】"
if command -v docker-compose &> /dev/null; then
    echo "   全サービスログ: docker-compose logs -f"
    echo "   特定サービス: docker-compose logs -f [サービス名]"
else
    echo "   全サービスログ: docker compose logs -f"
    echo "   特定サービス: docker compose logs -f [サービス名]"
fi
echo ""
echo "⚠️  【重要】このスクリプトはGEMINI_API_KEYを含むため、削除またはセキュアに管理してください"

# 元のディレクトリに戻る（オプション）
# cd "${ORIGINAL_DIR}" 