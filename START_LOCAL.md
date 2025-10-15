# ローカル環境でのアプリケーション起動手順

## 前提条件

✅ Docker Desktopがインストールされている
✅ Docker Desktopが起動している（メニューバーにアイコンが表示されている）
✅ `.env` ファイルが作成されている

## 起動コマンド

### 初回起動（ビルドが必要）

```bash
cd /Users/harubookair_2023/vfm_dev_running/running-analysis-system
docker compose up --build
```

**注意**: 初回起動時は5-10分程度かかります（AIモデルのダウンロードなど）

### 2回目以降の起動

```bash
cd /Users/harubookair_2023/vfm_dev_running/running-analysis-system
docker compose up
```

### バックグラウンドで起動（推奨）

```bash
docker compose up -d
```

## アクセス先

起動後、以下のURLからアクセスできます：

- **フロントエンド（メインアプリ）**: http://localhost:3000
- **API Gateway**: http://localhost:80
- **Video Processing API**: http://localhost:8001/docs
- **Pose Estimation API**: http://localhost:8002/docs
- **Feature Extraction API**: http://localhost:8003/docs
- **Analysis API**: http://localhost:8004/docs
- **Advice Generation API**: http://localhost:8005/docs
- **Video Generation API**: http://localhost:8006/docs

## 停止コマンド

```bash
# コンテナを停止（データは保持）
docker compose down

# コンテナを停止してデータも削除
docker compose down -v
```

## ログの確認

```bash
# すべてのサービスのログを表示
docker compose logs -f

# 特定のサービスのログを表示
docker compose logs -f frontend
docker compose logs -f video_processing
```

## トラブルシューティング

### エラー: ポートが既に使用されている

```bash
# 使用中のポートを確認
lsof -i :3000
lsof -i :80

# 該当のプロセスを停止するか、docker-compose.ymlのポート番号を変更
```

### エラー: メモリ不足

Docker Desktopの設定を変更：
1. Docker Desktop > Settings（設定）
2. Resources（リソース）> Memory
3. 8GB以上に設定（推奨）
4. Apply & Restart

### コンテナを完全にリセット

```bash
# すべてのコンテナ、イメージ、ボリュームを削除
docker compose down -v
docker system prune -a

# 再ビルド
docker compose up --build
```

## 開発時のヒント

### 特定のサービスだけを起動

```bash
# フロントエンドのみ
docker compose up frontend

# バックエンドサービスのみ
docker compose up video_processing pose_estimation feature_extraction analysis advice_generation
```

### コンテナ内でコマンドを実行

```bash
# 例: video_processingサービス内でPythonスクリプトを実行
docker compose exec video_processing python3 your_script.py

# 例: データベース接続テスト
docker compose exec video_processing python3 db_utils.py
```

---

**最終更新**: 2025年10月15日




