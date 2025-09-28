#!/bin/bash

# EC2設定
EC2_IP="54.206.3.155"
KEY_FILE="/Users/onoriku/Downloads/Runners Insight Key.pem"

echo "🧹 EC2ディスクスペースクリーンアップ開始..."

echo "📊 現在のディスク使用量を確認..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "df -h"

echo "🐳 Docker unused images削除..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "docker image prune -a -f"

echo "🗂️ Docker unused volumes削除..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "docker volume prune -f"

echo "🧮 Docker unused containers削除..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "docker container prune -f"

echo "📝 システムログクリーンアップ..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "sudo journalctl --vacuum-time=1d"

echo "📊 クリーンアップ後のディスク使用量..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP "df -h"

echo "✅ クリーンアップ完了！"
