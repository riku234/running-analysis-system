# AWS Elastic IPアドレス変更ログ

## IPアドレス変更履歴

### 2025年8月27日 - Elastic IPアドレス関連付け

**変更内容:**
- **旧IPアドレス**: `3.25.216.89` (パブリックIP)
- **新IPアドレス**: `54.206.3.155` (Elastic IP)

**対応作業:**
1. ✅ SSH接続確認 - 新しいIPアドレスでの接続成功
2. ✅ ホストキー追加 - ~/.ssh/known_hostsに新しいIPアドレスを追加
3. ✅ Dockerサービス状況確認 - 全7サービスが正常稼働中
4. ✅ Webアプリケーション動作確認 - http://54.206.3.155 でアクセス可能
5. ✅ 特徴量抽出サービス確認 - v3.0.0 絶対角度計算システムが正常動作

**影響なし項目:**
- Docker Composeネットワーク設定（内部通信のため）
- next.config.js APIプロキシ設定（API Gateway経由のため）
- マイクロサービス間通信（同一Docker network内のため）

**新しいアクセスURL:**
- **Webアプリケーション**: http://54.206.3.155
- **動画アップロード・解析**: 新仕様の絶対角度システム対応済み

**稼働中サービス:**
1. Frontend (3000) - Next.js Webアプリケーション
2. API Gateway (80) - Nginx リバースプロキシ
3. Video Processing (8001) - 動画アップロード・統合処理
4. Pose Estimation (8002) - MediaPipe骨格推定
5. Feature Extraction (8003) - 絶対角度計算 (v3.0.0)
6. Analysis (8004) - 課題分析
7. Advice Generation (8005) - Gemini AIアドバイス生成

**システム状態:**
- 🟢 全サービス正常稼働
- 🟢 新仕様の絶対角度計算システム稼働中
- 🟢 Elastic IP関連付け完了
- 🟢 動画アップロードテスト準備完了

## 使用方法

新しいIPアドレスでの操作:

```bash
# SSH接続
ssh -i "/Users/onoriku/Downloads/Runners Insight Key.pem" ec2-user@54.206.3.155

# Webアプリケーションアクセス
http://54.206.3.155

# システム状況確認
docker-compose ps
docker-compose logs [service_name]
```

## 備考

- Elastic IPアドレスは固定されているため、今後EC2インスタンスを再起動してもIPアドレスは変更されません
- すべてのサービスがコンテナ化されているため、IPアドレス変更による設定変更は不要
- 新仕様の絶対角度計算システム（体幹・大腿・下腿の鉛直軸基準角度）が正常に動作中 