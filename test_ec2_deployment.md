# EC2デプロイ前の確認事項

## ✅ 変更内容の確認

### 1. ローカル環境（現在）
- **ENABLE_DB_SAVE=false**
- データベース保存をスキップ
- 高速アップロード ⚡
- Z値分析は正常に実行される
- フロントエンドでZ値が即座に表示される

### 2. EC2本番環境（デプロイ後）
- **ENABLE_DB_SAVE=true**
- データベース保存を実行
- RDSと同一リージョン（ap-southeast-2）なので高速
- Z値分析結果もデータベースに保存される
- フロントエンドでZ値が即座に表示される（今回の修正）

## 🔍 デプロイ時の動作フロー

### デプロイコマンド
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 環境変数の優先順位
1. `docker-compose.prod.yml` の `ENABLE_DB_SAVE=true` （最優先）
2. `.env` ファイルの DB接続情報
3. `docker-compose.yml` の基本設定

### 処理フロー（EC2）
```
動画アップロード
  ↓
骨格推定 ✅
  ↓
特徴量計算 ✅
  ↓
Z値分析 ✅ ← response_data に含まれる
  ↓
統合アドバイス生成 ✅ ← response_data に含まれる
  ↓
データベース保存 ✅ （ENABLE_DB_SAVE=true）
  ├─ 走行記録
  ├─ キーポイント
  ├─ イベント
  ├─ 解析結果
  └─ アドバイス
  ↓
レスポンス返却 ✅
  ├─ z_score_analysis ← フロントエンドで即座に表示
  └─ advice_results ← フロントエンドで即座に表示
```

## 🚨 潜在的な問題とその対策

### 問題1: docker-compose.prod.yml がEC2に存在しない
**対策**: デプロイスクリプトがgit pullするので自動的に取得される ✅

### 問題2: 既存のコンテナが古い設定で起動している
**対策**: `docker-compose up -d` で自動的に再作成される ✅

### 問題3: systemdサービスが古い設定を使用
**対策**: `setup_auto_start_on_ec2.sh` を再実行する必要がある ⚠️

## 📋 安全なデプロイ手順

### ステップ1: 通常のデプロイ
```bash
./deploy_to_ec2.sh
```

### ステップ2: systemdサービスの更新（必要に応じて）
```bash
./setup_auto_start_on_ec2.sh
```

### ステップ3: 動作確認
1. EC2サイトにアクセス
2. 動画をアップロード
3. Z値が即座に表示されることを確認
4. データベースに保存されていることを確認

## 🧪 テスト方法

### EC2でのログ確認
```bash
ssh -i "path/to/key.pem" ec2-user@54.206.3.155
cd ~/running-analysis-system
docker logs running-analysis-system-video_processing-1 --tail 50 | grep "データベース保存"
```

**期待される出力:**
```
INFO:app.main:📊 データベース保存: 有効
INFO:app.main:💾 データベースへの保存を開始します...
INFO:app.main:✅ 走行記録を作成しました: run_id=XX
INFO:app.main:✅ キーポイントデータを保存しました
INFO:app.main:✅ イベントデータを保存しました
INFO:app.main:✅ 解析結果を保存しました
INFO:app.main:✅ 統合アドバイスを保存しました
INFO:app.main:✅ 全てのデータをデータベースに保存しました
```

## ✅ 結論

**EC2デプロイは安全です。**

理由:
1. ✅ 環境変数の制御により、EC2では自動的に `ENABLE_DB_SAVE=true` になる
2. ✅ ローカルとEC2で異なる設定が適用される
3. ✅ Z値分析結果は `response_data` に含まれるため、フロントエンドで即座に表示される
4. ✅ データベース保存は EC2（同一リージョン）では高速
5. ✅ 既存の機能に影響なし

**唯一の注意点:**
- systemdサービスを更新するために `setup_auto_start_on_ec2.sh` を再実行する必要がある
- これにより、EC2再起動時も正しい設定で起動する

