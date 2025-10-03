#!/bin/bash
# EC2インスタンス再起動時にDocker Composeを自動起動する設定スクリプト

set -e

# SSH接続情報
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"
EC2_USER="ec2-user"
EC2_HOST="54.206.3.155"

echo "🚀 EC2にSSH接続してDocker自動起動を設定します..."

ssh -i "$KEY_FILE" ${EC2_USER}@${EC2_HOST} << 'ENDSSH'

echo "📝 systemdサービスファイルを作成します..."

# systemdサービスファイルを作成
sudo tee /etc/systemd/system/running-analysis.service > /dev/null << 'EOF'
[Unit]
Description=Running Analysis System Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/running-analysis-system
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemdサービスファイルを作成しました"

# systemdをリロード
echo "🔄 systemdをリロードします..."
sudo systemctl daemon-reload

# サービスを有効化（起動時に自動実行）
echo "⚙️  サービスを有効化します..."
sudo systemctl enable running-analysis.service

echo "✅ 自動起動設定が完了しました！"

# サービスの状態を確認
echo ""
echo "📊 サービスの状態:"
sudo systemctl status running-analysis.service --no-pager || true

echo ""
echo "🎉 設定完了!"
echo "次回のEC2再起動時にDocker Composeが自動的に起動します。"
echo ""
echo "📝 手動でサービスを管理する場合:"
echo "  開始: sudo systemctl start running-analysis.service"
echo "  停止: sudo systemctl stop running-analysis.service"
echo "  状態確認: sudo systemctl status running-analysis.service"
echo "  自動起動無効化: sudo systemctl disable running-analysis.service"

ENDSSH

echo ""
echo "✅ EC2への設定が完了しました！"

