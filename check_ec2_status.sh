#!/bin/bash
# EC2インスタンスとアプリケーションの状態確認スクリプト

set -e

# SSH接続情報
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"
EC2_USER="ec2-user"
EC2_HOST="54.206.3.155"

echo "🔍 EC2インスタンスの状態を確認します..."
echo ""

# EC2インスタンスへの接続確認
if ssh -i "$KEY_FILE" -o ConnectTimeout=5 ${EC2_USER}@${EC2_HOST} "echo '✅ SSH接続成功'" 2>/dev/null; then
    echo ""
    
    # systemdサービスの状態確認
    echo "📊 systemdサービスの状態:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ssh -i "$KEY_FILE" ${EC2_USER}@${EC2_HOST} "sudo systemctl is-active running-analysis.service && echo '✅ running-analysis.service: アクティブ' || echo '❌ running-analysis.service: 非アクティブ'"
    echo ""
    
    # Dockerコンテナの状態確認
    echo "🐳 Dockerコンテナの状態:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ssh -i "$KEY_FILE" ${EC2_USER}@${EC2_HOST} << 'ENDSSH'
cd running-analysis-system
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
ENDSSH
    echo ""
    
    # 各サービスのヘルスチェック
    echo "🏥 サービスヘルスチェック:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # API Gatewayのヘルスチェック
    if curl -s -o /dev/null -w "%{http_code}" http://${EC2_HOST}/health | grep -q "200"; then
        echo "✅ API Gateway: 正常稼働"
    else
        echo "❌ API Gateway: 応答なし"
    fi
    
    # Frontendのヘルスチェック
    if curl -s -o /dev/null -w "%{http_code}" http://${EC2_HOST}:3000 | grep -q "200"; then
        echo "✅ Frontend: 正常稼働"
    else
        echo "❌ Frontend: 応答なし"
    fi
    
    echo ""
    echo "🌐 アプリケーションURL:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   http://${EC2_HOST}"
    echo ""
    echo "✅ すべてのサービスが正常に稼働している場合、アプリケーションにアクセスできます！"
    
else
    echo "❌ EC2インスタンスに接続できません"
    echo "   - インスタンスが起動していない可能性があります"
    echo "   - ネットワーク接続を確認してください"
    exit 1
fi

