# AWS EC2 デプロイメントガイド

## 🚀 概要

このガイドでは、ランニング解析システムをAWS EC2にデプロイする手順を説明します。

## 📋 前提条件

- AWS アカウント
- SSH キーペア
- ドメイン名（オプション）
- Git リポジトリへのアクセス

## 🏗️ EC2インスタンス設定

### 1. EC2インスタンス作成

1. **AWS Management Console** にログイン
2. **EC2 Dashboard** に移動
3. **Launch Instance** をクリック

#### 推奨設定：
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t3.small (1 vCPU, 2GB RAM)
- **Storage**: 30GB gp3 EBS
- **Security Group**:
  - SSH (22): 自分のIPアドレス
  - HTTP (80): 0.0.0.0/0
  - HTTPS (443): 0.0.0.0/0
  - Custom TCP (3000): 0.0.0.0/0 (開発用)
  - Custom TCP (8001-8005): 0.0.0.0/0 (開発用)

### 2. SSH接続

```bash
# SSH接続
ssh -i "your-key.pem" ubuntu@your-ec2-public-ip

# キーの権限設定（必要に応じて）
chmod 400 your-key.pem
```

### 3. 初期設定実行

```bash
# 設定スクリプトをダウンロード
wget https://raw.githubusercontent.com/your-repo/running-analysis-system/main/setup-ec2.sh

# 実行権限を付与
chmod +x setup-ec2.sh

# 初期設定実行
./setup-ec2.sh

# 再起動
sudo reboot
```

## 📦 アプリケーションデプロイ

### 1. ソースコード取得

```bash
# リポジトリをクローン
git clone https://github.com/your-repo/running-analysis-system.git
cd running-analysis-system

# 本番用環境変数設定
cp env.production.example .env.production
vim .env.production  # 実際の値を設定
```

### 2. スクリプト権限設定

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy.sh
chmod +x setup-ec2.sh
```

### 3. デプロイ実行

```bash
# 基本デプロイ（HTTP）
./deploy.sh production

# HTTPS対応デプロイ（ドメイン必要）
./deploy.sh production your-domain.com
```

## 🔒 SSL証明書設定（HTTPS）

### Let's Encryptを使用する場合

```bash
# Certbotインストール
sudo apt-get install certbot

# 証明書取得
sudo certbot certonly --standalone -d your-domain.com

# 証明書を所定の場所にコピー
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/running-analysis/ssl-certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/running-analysis/ssl-certs/

# Dockerコンテナ再起動
docker-compose -f docker-compose.prod.yml restart api_gateway
```

### 自動更新設定

```bash
# crontabに追加
sudo crontab -e

# 以下の行を追加
0 12 * * * /usr/bin/certbot renew --quiet && docker-compose -f /home/ubuntu/running-analysis-system/docker-compose.prod.yml restart api_gateway
```

## 📊 監視・運用

### ログ確認

```bash
# アプリケーションログ
docker-compose -f docker-compose.prod.yml logs -f

# 特定サービスのログ
docker-compose -f docker-compose.prod.yml logs -f video_processing

# システムログ
sudo tail -f /var/log/running-analysis.log

# Nginxログ
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### サービス状態確認

```bash
# Dockerコンテナ状態
docker-compose -f docker-compose.prod.yml ps

# システムリソース
htop
df -h
free -m

# ネットワーク
netstat -tulpn
```

### ヘルスチェック

```bash
# APIゲートウェイ
curl http://localhost/health

# 各サービス
curl http://localhost:8001/health  # video_processing
curl http://localhost:8002/health  # pose_estimation
curl http://localhost:8003/health  # feature_extraction
curl http://localhost:8004/health  # analysis
curl http://localhost:8005/health  # advice_generation
```

## 🔄 更新・再デプロイ

### コード更新

```bash
# 最新コードを取得
git pull origin main

# 再デプロイ
./deploy.sh production
```

### 設定変更

```bash
# 環境変数更新
vim .env.production

# 設定反映
docker-compose -f docker-compose.prod.yml restart
```

### データベースバックアップ（必要に応じて）

```bash
# 手動バックアップ
sudo cp -r /opt/running-analysis/uploads /opt/backups/manual_backup_$(date +%Y%m%d_%H%M%S)

# 定期バックアップ設定
echo "0 2 * * * /usr/bin/rsync -av /opt/running-analysis/uploads/ /opt/backups/daily_backup_\$(date +\%Y\%m\%d)/" | crontab -
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. Docker build失敗

```bash
# ディスク容量確認
df -h

# Dockerキャッシュクリア
docker system prune -af

# 再ビルド
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### 2. サービス起動失敗

```bash
# ログ確認
docker-compose -f docker-compose.prod.yml logs service-name

# ポート確認
sudo netstat -tulpn | grep :8001

# コンテナ再起動
docker-compose -f docker-compose.prod.yml restart service-name
```

#### 3. SSL証明書エラー

```bash
# 証明書確認
sudo certbot certificates

# 手動更新
sudo certbot renew

# Nginxテスト
sudo nginx -t
```

#### 4. メモリ不足

```bash
# スワップ追加
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### ログレベル調整

```bash
# デバッグモード有効
echo "LOG_LEVEL=DEBUG" >> .env.production
docker-compose -f docker-compose.prod.yml restart
```

## 📈 スケーリング

### 垂直スケーリング（インスタンスサイズ変更）

1. EC2インスタンスを停止
2. インスタンスタイプを変更（例：t3.large → t3.xlarge）
3. インスタンスを開始

### 水平スケーリング（ロードバランサー使用）

- Application Load Balancer (ALB) 設定
- 複数EC2インスタンス構成
- RDS やS3などマネージドサービス活用

## 🔐 セキュリティ

### 基本セキュリティ

```bash
# セキュリティアップデート
sudo apt-get update && sudo apt-get upgrade -y

# 不要ポート確認
sudo ufw status

# ログイン試行監視
sudo tail -f /var/log/auth.log
```

### 追加セキュリティ対策

- IAM ロールの使用
- VPC設定
- CloudWatch監視
- AWS WAF設定

## 📞 サポート

問題が発生した場合：

1. ログファイルを確認
2. サービス状態を確認
3. ディスク容量・メモリを確認
4. GitHub Issuesに報告

---

**注意**: 本番環境では、適切なバックアップ、監視、セキュリティ対策を実装してください。 