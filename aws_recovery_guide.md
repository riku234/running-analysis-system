# AWS EC2 復旧ガイド

## 🚨 現在の状況
- **EC2 IP**: 3.25.216.89
- **状態**: ネットワーク接続不可（100%パケットロス）
- **原因**: EC2インスタンス停止の可能性

## 🎯 復旧手順

### **方法1: AWSマネジメントコンソール (最も簡単)**

1. **AWSコンソールにログイン**
   ```
   https://aws.amazon.com/console/
   ```

2. **EC2ダッシュボードに移動**
   - Services → EC2 → Instances

3. **インスタンス状況確認**
   - Instance ID: `i-xxxxxxxxxxxxxxx` (あなたのインスタンス)
   - State: `stopped` の場合は停止中

4. **インスタンス開始**
   ```
   1. インスタンスを選択
   2. 「Actions」→「Instance State」→「Start」
   3. 数分待機
   ```

5. **新しいPublic IPを確認**
   - インスタンス詳細の「IPv4 Public IP」をメモ

### **方法2: AWS CLI (コマンドライン)**

```bash
# インスタンス状況確認
aws ec2 describe-instances --region ap-southeast-2

# インスタンス開始 (Instance IDを実際のものに置換)
aws ec2 start-instances --instance-ids i-xxxxxxxxxxxxxxx --region ap-southeast-2

# 状況確認
aws ec2 describe-instances --instance-ids i-xxxxxxxxxxxxxxx --region ap-southeast-2
```

## 🔧 復旧後の手順

### **1. 新しいIPでの接続確認**
```bash
# 新しいIPに置換
ping -c 3 [NEW_IP_ADDRESS]
curl http://[NEW_IP_ADDRESS]/
```

### **2. SSH接続でサーバー状況確認**
```bash
ssh -i ~/.ssh/runners-insight-key.pem ec2-user@[NEW_IP_ADDRESS]

# EC2内で実行
docker compose ps
docker compose logs
```

### **3. 必要に応じてサービス再起動**
```bash
# EC2内で実行
cd running-analysis-system
docker compose down
docker compose up -d
```

## 📋 SWAPメモリ追加（メモリ不足対策）

```bash
# create_swap.shを実行
sudo chmod +x create_swap.sh
sudo ./create_swap.sh
```

## 🚀 完全再構築（必要な場合）

```bash
# reset_and_build.shを実行
chmod +x reset_and_build.sh

# APIキーを設定してから実行
nano reset_and_build.sh  # GEMINI_API_KEYを設定
./reset_and_build.sh
```

## ⚠️ 重要な注意点

1. **Elastic IP未設定の場合**、インスタンス再起動でIPアドレスが変わります
2. **データの永続化**はDockerボリュームとGitに依存
3. **環境変数**（API KEYなど）は再設定が必要な場合があります

## 📞 問題が続く場合

1. セキュリティグループ設定確認（Port 80, 22, 8001-8005）
2. VPC/サブネット設定確認  
3. Elastic IP の設定検討 