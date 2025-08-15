#!/bin/bash

# AWS EC2 初期設定スクリプト
# Ubuntu 22.04 LTS用

set -e

log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# システム更新
update_system() {
    log_info "システムを更新中..."
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get install -y curl wget git unzip htop tree
}

# Docker インストール
install_docker() {
    log_info "Dockerをインストール中..."
    
    # 既存のDockerを削除
    sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Dockerの公式GPGキーを追加
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Dockerリポジトリを追加
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Dockerをインストール
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Docker Composeをインストール
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # ubuntuユーザーをdockerグループに追加
    sudo usermod -aG docker ubuntu
    
    # Dockerサービス開始・自動起動設定
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_info "Dockerインストール完了"
}

# Node.js インストール (ビルド用)
install_nodejs() {
    log_info "Node.jsをインストール中..."
    
    # NodeSourceリポジトリを追加
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    log_info "Node.js インストール完了: $(node --version)"
}

# ファイアウォール設定
setup_firewall() {
    log_info "ファイアウォールを設定中..."
    
    # UFWを有効化
    sudo ufw --force enable
    
    # 基本ルール
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # SSH許可
    sudo ufw allow ssh
    
    # HTTP/HTTPS許可
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # アプリケーションポート許可（開発用）
    sudo ufw allow 3000/tcp  # Frontend
    sudo ufw allow 8001:8005/tcp  # Backend services
    
    sudo ufw status
    
    log_info "ファイアウォール設定完了"
}

# システム最適化
optimize_system() {
    log_info "システムを最適化中..."
    
    # スワップファイル作成（t3.smallは2GBなので必須）
    log_info "スワップファイルを作成中..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    # スワップ使用頻度を調整（メモリ不足時のパフォーマンス向上）
    echo 'vm.swappiness=60' | sudo tee -a /etc/sysctl.conf
    
    # システム制限値の調整
    sudo tee -a /etc/security/limits.conf << EOF
ubuntu soft nofile 65536
ubuntu hard nofile 65536
ubuntu soft nproc 32768
ubuntu hard nproc 32768
EOF
    
    # カーネルパラメータ最適化
    sudo tee -a /etc/sysctl.conf << EOF
# ネットワーク最適化
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 65536 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000

# ファイルシステム最適化
fs.file-max = 2097152
vm.swappiness = 10
EOF
    
    sudo sysctl -p
    
    log_info "システム最適化完了"
}

# ログ設定
setup_logging() {
    log_info "ログ設定を行っています..."
    
    # logrotateの設定
    sudo tee /etc/logrotate.d/docker << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
    
    # rsyslogの設定
    sudo tee -a /etc/rsyslog.conf << EOF
# アプリケーションログ
local0.*    /var/log/running-analysis.log
EOF
    
    sudo systemctl restart rsyslog
    
    log_info "ログ設定完了"
}

# Git設定
setup_git() {
    log_info "Git設定を行っています..."
    
    # デプロイキーまたはトークンでの認証設定
    # 注意: 実際の運用では適切な認証方法を使用してください
    
    log_info "Git設定完了（認証設定は手動で行ってください）"
}

# 自動アップデート設定
setup_auto_updates() {
    log_info "自動アップデートを設定中..."
    
    sudo apt-get install -y unattended-upgrades
    
    # 自動アップデート設定
    sudo tee /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
    
    sudo systemctl enable unattended-upgrades
    
    log_info "自動アップデート設定完了"
}

# メイン実行
main() {
    log_info "=== AWS EC2 初期設定開始 ==="
    log_info "OS: $(lsb_release -d | cut -f2)"
    log_info "時刻: $(date)"
    
    update_system
    install_docker
    install_nodejs
    setup_firewall
    optimize_system
    setup_logging
    setup_git
    setup_auto_updates
    
    log_info "=== 初期設定完了 ==="
    log_info "再起動が推奨されます: sudo reboot"
    log_info "再起動後、以下でDockerが利用可能になります:"
    log_info "  docker --version"
    log_info "  docker-compose --version"
}

# スクリプト実行
main "$@" 