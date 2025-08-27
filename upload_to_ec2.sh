#!/bin/bash

# =============================================================================
# EC2へのファイルアップロード・接続ヘルパースクリプト
# =============================================================================

echo "🚀 EC2への接続・ファイルアップロード手順"
echo ""

# 設定値（実際の値に変更してください）
EC2_IP="3.25.216.89"
KEY_FILE="YOUR_KEY_FILE.pem"  # 実際のキーファイル名に変更
USER="ec2-user"

echo "📋 必要な設定:"
echo "   EC2 IP: ${EC2_IP}"
echo "   キーファイル: ${KEY_FILE}"
echo "   ユーザー: ${USER}"
echo ""

echo "🔍 ステップ1: キーファイルを探す"
echo "   以下のコマンドでキーファイルを探してください:"
echo "   find ~ -name '*.pem' -type f 2>/dev/null"
echo ""

echo "🔐 ステップ2: キーファイルのパーミッション設定"
echo "   chmod 400 /path/to/your-key.pem"
echo ""

echo "📤 ステップ3: ファイルをEC2にアップロード"
echo "   scp -i /path/to/your-key.pem reset_and_build.sh ${USER}@${EC2_IP}:~/"
echo "   scp -i /path/to/your-key.pem create_swap.sh ${USER}@${EC2_IP}:~/"
echo ""

echo "🔌 ステップ4: EC2に接続"
echo "   ssh -i /path/to/your-key.pem ${USER}@${EC2_IP}"
echo ""

echo "🎯 ステップ5: EC2でスクリプト実行"
echo "   # SWAPファイル作成（メモリ不足対策）"
echo "   sudo ./create_swap.sh"
echo ""
echo "   # APIキーを設定してからリセット・再構築"
echo "   nano reset_and_build.sh  # GEMINI_API_KEYを設定"
echo "   ./reset_and_build.sh"
echo ""

echo "💡 【トラブルシューティング】"
echo ""
echo "❌ Permission denied (publickey) エラーの場合:"
echo "   - キーファイルのパスが正しいか確認"
echo "   - キーファイルのパーミッションが400か確認"
echo "   - EC2インスタンスが起動しているか確認"
echo ""
echo "❌ キーファイルが見つからない場合:"
echo "   1. AWSコンソールでEC2インスタンスのキーペア名を確認"
echo "   2. ローカルPCでそのキーファイルを検索"
echo "   3. 必要に応じてAWSからキーペアを再作成"
echo ""
echo "📁 【よくあるキーファイルの場所】"
echo "   - ~/Downloads/your-key.pem"
echo "   - ~/.ssh/your-key.pem"
echo "   - ~/Desktop/your-key.pem"
echo ""
echo "🔧 【実行例】"
echo "   # キーファイルが ~/Downloads/my-ec2-key.pem にある場合"
echo "   chmod 400 ~/Downloads/my-ec2-key.pem"
echo "   scp -i ~/Downloads/my-ec2-key.pem reset_and_build.sh ${USER}@${EC2_IP}:~/"
echo "   ssh -i ~/Downloads/my-ec2-key.pem ${USER}@${EC2_IP}" 