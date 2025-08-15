#!/bin/bash

# AWS EC2 デプロイメントスクリプト
# 使用方法: ./deploy.sh [production|staging]

set -e

# 設定
APP_NAME="running-analysis-system"
DEPLOY_USER="ubuntu"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/deploy.log"

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1" | tee -a $LOG_FILE
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1" | tee -a $LOG_FILE
}

# 環境確認
check_environment() {
    log_info "環境確認を開始..."
    
    # Docker確認
    if ! command -v docker &> /dev/null; then
        log_error "Dockerがインストールされていません"
        exit 1
    fi
    
    # Docker Compose確認
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Composeがインストールされていません"
        exit 1
    fi
    
    # 必要なディレクトリ作成
    sudo mkdir -p /opt/running-analysis/uploads
    sudo mkdir -p /opt/running-analysis/models
    sudo mkdir -p /opt/running-analysis/logs
    sudo mkdir -p /opt/running-analysis/ssl-certs
    sudo mkdir -p $BACKUP_DIR
    
    # 権限設定
    sudo chown -R $DEPLOY_USER:$DEPLOY_USER /opt/running-analysis
    sudo chmod -R 755 /opt/running-analysis
    
    log_info "環境確認完了"
}

# 現在のサービス停止
stop_services() {
    log_info "既存サービスを停止中..."
    
    if [ -f $DOCKER_COMPOSE_FILE ]; then
        docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans || true
    fi
    
    # 古いコンテナとイメージをクリーンアップ
    docker system prune -f
    
    log_info "サービス停止完了"
}

# バックアップ作成
create_backup() {
    log_info "バックアップを作成中..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    sudo mkdir -p $BACKUP_PATH
    
    # データベースファイルとアップロードファイルをバックアップ
    if [ -d "/opt/running-analysis/uploads" ]; then
        sudo cp -r /opt/running-analysis/uploads $BACKUP_PATH/
        log_info "アップロードファイルをバックアップ: $BACKUP_PATH/uploads"
    fi
    
    # 設定ファイルをバックアップ
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        sudo cp $DOCKER_COMPOSE_FILE $BACKUP_PATH/
    fi
    
    # 古いバックアップを削除（7日以上古い）
    find $BACKUP_DIR -type d -name "backup_*" -mtime +7 -exec sudo rm -rf {} + 2>/dev/null || true
    
    log_info "バックアップ完了: $BACKUP_PATH"
}

# アプリケーションビルド
build_application() {
    log_info "アプリケーションをビルド中..."
    
    # Docker imageをビルド
    docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache
    
    log_info "ビルド完了"
}

# サービス起動
start_services() {
    log_info "サービスを起動中..."
    
    # Docker Composeでサービス起動
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    log_info "サービス起動完了"
}

# ヘルスチェック
health_check() {
    log_info "ヘルスチェックを実行中..."
    
    # サービスが起動するまで待機
    sleep 30
    
    # 各サービスのヘルスチェック
    services=("api_gateway:80" "frontend:3000" "video_processing:8001" "pose_estimation:8002" "feature_extraction:8003" "analysis:8004" "advice_generation:8005")
    
    for service in "${services[@]}"; do
        service_name="${service%:*}"
        port="${service#*:}"
        
        if docker-compose -f $DOCKER_COMPOSE_FILE ps | grep "$service_name" | grep "Up" > /dev/null; then
            log_info "✅ $service_name サービスが正常に動作中"
        else
            log_error "❌ $service_name サービスが停止中"
            docker-compose -f $DOCKER_COMPOSE_FILE logs $service_name
        fi
    done
    
    # HTTP エンドポイントチェック
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_info "✅ HTTPエンドポイント正常"
    else
        log_warn "⚠️ HTTPエンドポイントに問題があります"
    fi
    
    log_info "ヘルスチェック完了"
}

# SSL証明書セットアップ (Let's Encrypt)
setup_ssl() {
    local domain=$1
    
    if [ -z "$domain" ]; then
        log_warn "ドメインが指定されていません。SSL設定をスキップします"
        return
    fi
    
    log_info "SSL証明書を設定中: $domain"
    
    # Certbot インストール
    if ! command -v certbot &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot
    fi
    
    # 証明書取得
    sudo certbot certonly --standalone -d $domain --email admin@$domain --agree-tos --non-interactive
    
    # 証明書をコピー
    sudo cp /etc/letsencrypt/live/$domain/fullchain.pem /opt/running-analysis/ssl-certs/
    sudo cp /etc/letsencrypt/live/$domain/privkey.pem /opt/running-analysis/ssl-certs/
    
    # 権限設定
    sudo chown -R $DEPLOY_USER:$DEPLOY_USER /opt/running-analysis/ssl-certs
    
    # 自動更新設定
    echo "0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /home/$DEPLOY_USER/$APP_NAME/$DOCKER_COMPOSE_FILE restart api_gateway" | sudo crontab -
    
    log_info "SSL証明書設定完了"
}

# モニタリング設定
setup_monitoring() {
    log_info "モニタリングを設定中..."
    
    # Docker logs rotation
    cat > /tmp/docker-daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    sudo mv /tmp/docker-daemon.json /etc/docker/daemon.json
    sudo systemctl restart docker
    
    # ログローテーション設定
    sudo tee /etc/logrotate.d/running-analysis << EOF
/opt/running-analysis/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $DEPLOY_USER $DEPLOY_USER
}
EOF
    
    log_info "モニタリング設定完了"
}

# メイン実行
main() {
    local environment=${1:-production}
    local domain=$2
    
    log_info "=== AWS EC2 デプロイメント開始 ==="
    log_info "環境: $environment"
    log_info "時刻: $(date)"
    
    check_environment
    create_backup
    stop_services
    build_application
    start_services
    health_check
    setup_monitoring
    
    if [ -n "$domain" ]; then
        setup_ssl $domain
    fi
    
    log_info "=== デプロイメント完了 ==="
    log_info "アプリケーションURL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'localhost')"
    
    # 最終状態表示
    docker-compose -f $DOCKER_COMPOSE_FILE ps
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 