#!/bin/bash

# AWS EC2 t3.small専用デプロイメントスクリプト
# 使用方法: ./deploy-t3-small.sh [production|staging]

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

# メモリ使用量チェック
check_memory() {
    local available_mem=$(free -m | awk 'NR==2{print $7}')
    log_info "利用可能メモリ: ${available_mem}MB"
    
    if [ $available_mem -lt 500 ]; then
        log_warn "メモリ不足です。スワップを確認します..."
        
        if ! swapon -s | grep -q "/swapfile"; then
            log_info "スワップファイルを作成中..."
            sudo fallocate -l 2G /swapfile
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
        fi
    fi
}

# 段階的サービス起動（メモリ効率化）
start_services_staged() {
    log_info "段階的にサービスを起動中（メモリ節約のため）..."
    
    # Stage 1: インフラサービス
    log_info "Stage 1: API Gatewayを起動..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d api_gateway
    sleep 15
    
    # Stage 2: バックエンドサービス（重要度順）
    log_info "Stage 2: Video Processing サービスを起動..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d video_processing
    sleep 10
    
    log_info "Stage 3: Pose Estimation サービスを起動..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d pose_estimation
    sleep 10
    
    log_info "Stage 4: 分析サービスを起動..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d feature_extraction analysis advice_generation
    sleep 10
    
    # Stage 3: フロントエンド
    log_info "Stage 5: フロントエンドを起動..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d frontend
    
    log_info "全サービス起動完了"
}

# メモリクリーンアップ
cleanup_memory() {
    log_info "メモリクリーンアップを実行中..."
    
    # 不要なDockerオブジェクトを削除
    docker system prune -f --volumes
    
    # キャッシュクリア
    sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    
    log_info "メモリクリーンアップ完了"
}

# 軽量ビルド
build_application_light() {
    log_info "軽量ビルドを実行中..."
    
    # 1つずつビルド（メモリ使用量を抑制）
    services=("api_gateway" "frontend" "video_processing" "pose_estimation" "feature_extraction" "analysis" "advice_generation")
    
    for service in "${services[@]}"; do
        log_info "ビルド中: $service"
        docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache $service
        
        # メモリクリーンアップ
        docker image prune -f
        sleep 5
    done
    
    log_info "軽量ビルド完了"
}

# 環境確認（t3.small専用）
check_environment_t3() {
    log_info "t3.small環境確認を開始..."
    
    # メモリ確認
    local total_mem=$(free -m | awk 'NR==2{print $2}')
    log_info "総メモリ: ${total_mem}MB"
    
    if [ $total_mem -lt 1800 ]; then
        log_error "メモリが不足しています。t3.smallは約2GBのメモリが必要です"
        exit 1
    fi
    
    # スワップ確認
    if ! swapon -s | grep -q "/swapfile"; then
        log_warn "スワップファイルが設定されていません"
    fi
    
    # Docker確認
    if ! command -v docker &> /dev/null; then
        log_error "Dockerがインストールされていません"
        exit 1
    fi
    
    # 必要なディレクトリ作成
    sudo mkdir -p /opt/running-analysis/{uploads,models,logs}
    sudo mkdir -p $BACKUP_DIR
    
    # 権限設定
    sudo chown -R $DEPLOY_USER:$DEPLOY_USER /opt/running-analysis
    
    log_info "t3.small環境確認完了"
}

# サービス停止（メモリ効率化）
stop_services_graceful() {
    log_info "サービスを段階的に停止中..."
    
    if [ -f $DOCKER_COMPOSE_FILE ]; then
        # フロントエンドから停止
        docker-compose -f $DOCKER_COMPOSE_FILE stop frontend
        sleep 5
        
        # バックエンドサービス停止
        docker-compose -f $DOCKER_COMPOSE_FILE stop advice_generation analysis feature_extraction
        sleep 5
        
        docker-compose -f $DOCKER_COMPOSE_FILE stop pose_estimation video_processing
        sleep 5
        
        # インフラ停止
        docker-compose -f $DOCKER_COMPOSE_FILE stop api_gateway
        
        # 完全削除
        docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans
    fi
    
    log_info "サービス停止完了"
}

# ヘルスチェック（軽量版）
health_check_light() {
    log_info "軽量ヘルスチェックを実行中..."
    
    # サービスが起動するまで待機
    sleep 45
    
    # 基本的なエンドポイントのみチェック
    services=("api_gateway:80" "frontend:3000" "video_processing:8001")
    
    for service in "${services[@]}"; do
        service_name="${service%:*}"
        port="${service#*:}"
        
        if docker-compose -f $DOCKER_COMPOSE_FILE ps | grep "$service_name" | grep "Up" > /dev/null; then
            log_info "✅ $service_name サービスが正常に動作中"
        else
            log_error "❌ $service_name サービスが停止中"
            # ログの最後の10行のみ表示（メモリ節約）
            docker-compose -f $DOCKER_COMPOSE_FILE logs --tail=10 $service_name
        fi
    done
    
    # メモリ使用量確認
    local mem_usage=$(free -m | awk 'NR==2{printf "%.1f", $3/$2 * 100.0}')
    log_info "メモリ使用率: ${mem_usage}%"
    
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        log_warn "⚠️ メモリ使用率が高いです: ${mem_usage}%"
    fi
    
    log_info "軽量ヘルスチェック完了"
}

# バックアップ作成（軽量版）
create_backup_light() {
    log_info "軽量バックアップを作成中..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    sudo mkdir -p $BACKUP_PATH
    
    # 必要最小限のファイルのみバックアップ
    if [ -d "/opt/running-analysis/uploads" ]; then
        # ファイルサイズでフィルタリング（50MB以下のファイルのみ）
        find /opt/running-analysis/uploads -type f -size -50M -exec sudo cp {} $BACKUP_PATH/ \;
        log_info "軽量バックアップ完了: $BACKUP_PATH"
    fi
    
    # 古いバックアップを削除（3日以上古い）
    find $BACKUP_DIR -type d -name "backup_*" -mtime +3 -exec sudo rm -rf {} + 2>/dev/null || true
}

# メイン実行
main() {
    local environment=${1:-production}
    local domain=$2
    
    log_info "=== AWS EC2 t3.small デプロイメント開始 ==="
    log_info "環境: $environment"
    log_info "時刻: $(date)"
    
    check_environment_t3
    check_memory
    create_backup_light
    cleanup_memory
    stop_services_graceful
    build_application_light
    start_services_staged
    health_check_light
    
    log_info "=== t3.small デプロイメント完了 ==="
    log_info "アプリケーションURL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'localhost')"
    
    # 最終状態表示
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    
    # リソース使用状況表示
    log_info "=== リソース使用状況 ==="
    free -h
    df -h /
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 