#!/bin/bash

# ================================================================================
# AWS EC2 Amazon Linux 2023 サーバーセットアップスクリプト
# ファイル名: setup_server_al2023.sh
# 
# 用途: Dockerベースのアプリケーション用デプロイ環境構築
# 対象OS: Amazon Linux 2023 (AL2023)
# パッケージマネージャー: dnf
# 
# 実行手順:
# 1. EC2インスタンスにSSHでログイン:
#    ssh -i your-key.pem ec2-user@your-ec2-ip-address
# 
# 2. このスクリプトファイルを作成:
#    nano setup_server_al2023.sh
#    (または) vi setup_server_al2023.sh
# 
# 3. 実行権限を付与:
#    chmod +x setup_server_al2023.sh
# 
# 4. スクリプトを実行 (sudo権限が必要):
#    sudo ./setup_server_al2023.sh
# 
# 5. スクリプト実行後に、ec2-userでDockerグループ設定を有効化:
#    newgrp docker
#    (または) exit してから再度SSHログイン
# 
# ================================================================================

set -e  # エラーが発生した場合にスクリプトを停止

echo "🚀 AWS EC2 Amazon Linux 2023 サーバーセットアップ開始"
echo "======================================================="

# ログ出力関数
log_info() {
    echo "ℹ️  [INFO] $1"
}

log_success() {
    echo "✅ [SUCCESS] $1"
}

log_error() {
    echo "❌ [ERROR] $1"
}

# 現在のユーザーとOS情報を表示
log_info "現在のユーザー: $(whoami)"
log_info "OS情報: $(cat /etc/os-release | grep PRETTY_NAME)"
log_info "カーネルバージョン: $(uname -r)"

# ================================================================================
# 1. システム全パッケージを最新にアップデート
# ================================================================================
log_info "ステップ1: システムパッケージの更新"
dnf update -y
log_success "システムパッケージの更新完了"

# ================================================================================
# 2. Gitのインストール
# ================================================================================
log_info "ステップ2: Gitのインストール"
dnf install git -y
log_success "Git インストール完了"

# Gitバージョン確認
GIT_VERSION=$(git --version)
log_info "インストール済みGitバージョン: $GIT_VERSION"

# ================================================================================
# 3. Docker Engineのインストール
# ================================================================================
log_info "ステップ3: Docker Engineのインストール"
dnf install docker -y
log_success "Docker Engine インストール完了"

# Dockerバージョン確認
DOCKER_VERSION=$(docker --version)
log_info "インストール済みDockerバージョン: $DOCKER_VERSION"

# ================================================================================
# 4. Dockerサービスの起動と自動起動設定
# ================================================================================
log_info "ステップ4: Dockerサービスの起動と自動起動設定"

# Dockerサービスを開始
systemctl start docker
log_success "Dockerサービス開始完了"

# システム起動時の自動起動を有効化
systemctl enable docker
log_success "Dockerサービス自動起動設定完了"

# Dockerサービス状態確認
DOCKER_STATUS=$(systemctl is-active docker)
log_info "Dockerサービス状態: $DOCKER_STATUS"

# ================================================================================
# 5. ec2-userをdockerグループに追加
# ================================================================================
log_info "ステップ5: ec2-userをdockerグループに追加"

# dockerグループが存在するか確認
if ! getent group docker > /dev/null 2>&1; then
    log_info "dockerグループが存在しないため作成します"
    groupadd docker
fi

# ec2-userをdockerグループに追加
usermod -a -G docker ec2-user
log_success "ec2-userをdockerグループに追加完了"

# グループ設定確認
log_info "ec2-userのグループ: $(groups ec2-user)"

# ================================================================================
# 6. Docker Composeのインストール
# ================================================================================
log_info "ステップ6: Docker Composeのインストール"

# Docker Composeの最新バージョンを取得
log_info "Docker Composeの最新版を取得中..."

# GitHubから最新リリース情報を取得
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')

if [ -z "$COMPOSE_VERSION" ]; then
    log_error "Docker Composeの最新バージョン取得に失敗しました"
    COMPOSE_VERSION="v2.21.0"  # フォールバック版
    log_info "フォールバック版を使用: $COMPOSE_VERSION"
fi

log_info "Docker Compose バージョン: $COMPOSE_VERSION"

# Docker Composeバイナリをダウンロード
COMPOSE_URL="https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-linux-x86_64"
log_info "ダウンロードURL: $COMPOSE_URL"

curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose

# 実行権限を付与
chmod +x /usr/local/bin/docker-compose

log_success "Docker Compose インストール完了"

# Docker Composeバージョン確認
COMPOSE_INSTALLED_VERSION=$(docker-compose --version)
log_info "インストール済みDocker Composeバージョン: $COMPOSE_INSTALLED_VERSION"

# ================================================================================
# 7. インストール結果の確認
# ================================================================================
log_info "ステップ7: インストール結果の最終確認"

echo ""
echo "📋 インストール完了サマリー"
echo "=================================="
echo "✅ OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "✅ Git: $(git --version)"
echo "✅ Docker: $(docker --version)"
echo "✅ Docker Compose: $(docker-compose --version)"
echo "✅ Dockerサービス状態: $(systemctl is-active docker)"
echo "✅ ec2-userのグループ: $(groups ec2-user)"

# ================================================================================
# 8. 次の手順案内
# ================================================================================
echo ""
echo "🎉 サーバーセットアップ完了！"
echo "======================================="
echo ""
echo "📌 次に実行すべき手順:"
echo "1. 現在のSSHセッションから一度ログアウトし、再度ログイン"
echo "   (または) 'newgrp docker' を実行してグループ設定を適用"
echo ""
echo "2. Dockerコマンドがsudoなしで実行できることを確認:"
echo "   docker --version"
echo "   docker run hello-world"
echo ""
echo "3. アプリケーションのソースコードをクローン:"
echo "   git clone https://github.com/your-username/your-repository.git"
echo ""
echo "4. アプリケーションディレクトリに移動してDocker Composeで起動:"
echo "   cd your-application-directory"
echo "   docker-compose up -d"
echo ""
echo "⚠️  重要: ec2-userのdockerグループ設定は、"
echo "   ログアウト→再ログインまたは 'newgrp docker' 実行後に有効になります。"
echo ""

log_success "🚀 AWS EC2 Amazon Linux 2023 サーバーセットアップ完了"

# ================================================================================
# セットアップスクリプト終了
# ================================================================================ 