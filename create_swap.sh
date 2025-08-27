#!/bin/bash

# =============================================================================
# AWS EC2 Amazon Linux 2023 - 4GB SWAP ファイル作成スクリプト
# =============================================================================
# 
# 【使用方法】
# sudo chmod +x create_swap.sh
# sudo ./create_swap.sh
#
# 【目的】
# メモリ不足によるビルド失敗を防ぐため、4GBのSWAPファイルを作成・有効化します
# =============================================================================

set -e  # エラーが発生した場合にスクリプトを停止

echo "🚀 AWS EC2 - 4GB SWAP ファイル作成を開始します..."

# root権限チェック
if [ "$EUID" -ne 0 ]; then
    echo "❌ エラー: このスクリプトはsudo権限で実行してください"
    echo "   実行例: sudo ./create_swap.sh"
    exit 1
fi

# 既存のSWAP確認
echo "📊 現在のメモリ・SWAP使用状況："
free -h

# 既存のswapfileがあるかチェック
if [ -f /swapfile ]; then
    echo "⚠️  既存のswapfileが見つかりました。削除して新しく作成します..."
    swapoff /swapfile 2>/dev/null || true
    rm -f /swapfile
fi

echo ""
echo "📁 ステップ1: 4GBのswapfileを作成中..."
# fallocateコマンドで4GB (4096MB) のswapfileを作成
fallocate -l 4G /swapfile

echo "🔒 ステップ2: swapfileのパーミッションを設定中..."
# セキュリティのため、所有者のみ読み書き可能に設定
chmod 600 /swapfile

echo "🛠️  ステップ3: ファイルをSWAP領域としてフォーマット中..."
# ファイルをSWAP領域としてフォーマット
mkswap /swapfile

echo "⚡ ステップ4: SWAPを有効化中..."
# 作成したSWAPを即座に有効にする
swapon /swapfile

echo "💾 ステップ5: 永続化設定中（再起動後も有効）..."
# /etc/fstabに追記して、再起動後も自動でSWAPが有効になるように設定
if ! grep -q "/swapfile" /etc/fstab; then
    echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
    echo "   ✅ /etc/fstabに設定を追記しました"
else
    echo "   ℹ️  /etc/fstabには既に設定済みです"
fi

echo ""
echo "🎉 SWAP作成完了！現在のメモリ・SWAP使用状況："
free -h

echo ""
echo "✅ 4GB SWAPファイルの作成・有効化が完了しました！"
echo ""
echo "📋 【確認方法】"
echo "   現在の状況: free -h"
echo "   SWAP詳細:  swapon --show"
echo "   fstab確認: cat /etc/fstab | grep swap"
echo ""
echo "🔄 【再起動後の確認】"
echo "   サーバー再起動後も以下のコマンドでSWAPが有効であることを確認してください："
echo "   free -h"
echo ""
echo "🚨 【注意事項】"
echo "   - SWAPはSSDの寿命を短くする可能性があります"
echo "   - 本格的な運用では、メモリ増設も検討してください"
echo "   - 不要になった場合: sudo swapoff /swapfile && sudo rm /swapfile" 