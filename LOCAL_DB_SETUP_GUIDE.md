# ローカル環境データベース設定ガイド

## 概要

ローカル開発環境でPostgreSQLデータベースを使用するための設定手順です。

## 前提条件

- Docker & Docker Compose がインストールされている
- ポート5432が使用可能

## ステップ1: .envファイルの設定

プロジェクトルートに`.env`ファイルを作成し、以下の設定を追加してください：

```bash
# ============================================================================
# データベース接続設定（ローカル開発環境用）
# ============================================================================
# Docker Compose環境内から接続する場合: db
# ローカルマシンから接続する場合: localhost
DB_HOST=localhost
DB_PORT=5432
DB_NAME=app
DB_USER=postgres
DB_PASSWORD=postgres

# ============================================================================
# AI API設定
# ============================================================================
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# ============================================================================
# その他の設定
# ============================================================================
ENABLE_DB_SAVE=false
VIDEO_GENERATION_PASSWORD=admin123
```

**重要**: 
- ローカルマシンからスクリプトを実行する場合: `DB_HOST=localhost`
- Dockerコンテナ内から接続する場合: `DB_HOST=db`

## ステップ2: データベースコンテナの起動

```bash
# データベースコンテナを起動
docker compose up -d db

# 起動確認
docker compose ps db
```

**期待される出力**:
```
NAME                              STATUS
running-analysis-system-db-1      Up X seconds (healthy)
```

## ステップ3: データベーススキーマの作成

### 方法1: コンテナ内で実行（推奨）

```bash
docker compose exec db psql -U postgres -d app -f /docker-entrypoint-initdb.d/01-schema.sql
```

### 方法2: ローカルから実行

```bash
psql -h localhost -U postgres -d app -f database_schema.sql
```

**パスワード**: `postgres`

## ステップ4: CSVデータの移行

```bash
# CSVファイルが格納されているディレクトリを指定
python backend/scripts/migrate_csv_to_db.py \
    --csv-dir /path/to/csv/files \
    --csv1 統計モデル検討.csv \
    --csv2 ランニング分類.csv \
    --csv3 コメント紐づけ.csv
```

**注意**: 
- CSVファイルのパスを実際のパスに置き換えてください
- スクリプトは自動的に`localhost`に接続を試みます（`db`で接続できない場合）

## ステップ5: データ確認

```bash
python backend/scripts/check_db_data.py
```

**期待される出力**:
```
✅ ルール定義の数: X 件
✅ アドバイス文章の数: Y 件
...
```

## ステップ6: サービスの再起動

```bash
# 設定を反映するため、advice_generationサービスを再起動
docker compose restart advice_generation

# ログを確認
docker compose logs advice_generation --tail 50
```

## トラブルシューティング

### エラー: データベースコンテナが起動しない

```bash
# ログを確認
docker compose logs db

# ポート5432が既に使用されている場合
lsof -i :5432
# 使用しているプロセスを停止するか、docker-compose.ymlのポートを変更
```

### エラー: 接続タイムアウト

```bash
# .envファイルのDB_HOSTを確認
cat .env | grep DB_HOST

# localhostに設定されているか確認
# ローカルマシンから実行する場合は localhost
# Dockerコンテナ内から実行する場合は db
```

### エラー: 認証に失敗

```bash
# パスワードを確認
# デフォルト: postgres

# データベースコンテナを再作成
docker compose down db
docker volume rm running-analysis-system_postgres_data
docker compose up -d db
```

## 本番環境への切り替え

本番環境（AWS RDS）を使用する場合は、`.env`ファイルを以下のように変更してください：

```bash
# AWS RDS用の設定
DB_HOST=running-analysis-db-single.cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
```

## 関連ドキュメント

- `DB_MIGRATION_GUIDE.md`: CSVデータ移行の詳細ガイド
- `database_schema.sql`: データベーススキーマ定義
- `backend/scripts/check_db_data.py`: データ確認スクリプト



