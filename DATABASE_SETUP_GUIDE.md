# データベースセットアップガイド

## 📋 現在の設定状況

### ✅ 完了した作業

1. **データベース統合機能の実装** ✓
   - `db_utils.py` に全関数を実装
   - `video_processing` サービスに統合
   - Docker設定の更新完了

2. **環境変数の設定** ✓
   - `.env` ファイル作成済み
   - 接続情報を設定済み

3. **スクリプトの準備** ✓
   - `database_schema.sql` - テーブル定義
   - `test_db_connection.sh` - 接続テスト用
   - `setup_database.sh` - テーブル作成用

---

## 🔧 データベース接続情報

```
データベース名: running-analysis-db
エンドポイント: running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com
ポート: 5432
ユーザー: postgres
パスワード: vfmdev_01
```

---

## ⚠️ 現在の状態

**接続ステータス**: ❌ タイムアウト

**原因**:
- RDSインスタンスが停止している
- または、セキュリティグループでポート5432が開放されていない
- または、パブリックアクセスが無効になっている

---

## 🚀 セットアップ手順

### ステップ1: AWSコンソールでRDSの設定を確認・変更

#### 1-1. RDSインスタンスの起動確認

```
AWS Console → RDS → データベース
└─ running-analysis-db のステータスを確認
   ✓ 「利用可能」になっているか？
```

#### 1-2. セキュリティグループの設定

```
1. AWS Console → RDS → データベース
2. running-analysis-db をクリック
3. 「接続とセキュリティ」タブ
4. VPCセキュリティグループ（例：sg-xxxxx）をクリック
5. 「インバウンドルール」タブ → 「インバウンドルールを編集」
6. 以下のルールを追加:

┌──────────────────────────────────────────────────┐
│ タイプ: PostgreSQL                                │
│ プロトコル: TCP                                   │
│ ポート範囲: 5432                                  │
│ ソース: 0.0.0.0/0 （開発用）                      │
│        または、マイIP（セキュア）                  │
│        または、EC2のセキュリティグループ（本番用） │
└──────────────────────────────────────────────────┘

7. 「ルールを保存」をクリック
```

#### 1-3. パブリックアクセスの確認

```
AWS Console → RDS → running-analysis-db
└─ 接続とセキュリティ タブ
   └─ パブリックアクセス可能: 「はい」になっているか確認
```

**注意**: パブリックアクセスを有効にできない場合は、VPN経由またはEC2インスタンス経由での接続が必要です。

---

### ステップ2: 接続テスト

セキュリティグループを設定した後、以下のコマンドで接続をテスト：

```bash
cd /Users/onoriku/Projects/running-analysis-system
./test_db_connection.sh
```

**期待される出力:**
```
============================================================
🧪 データベース接続テスト
============================================================
🔌 データベースへの接続を試みています...
   ホスト: running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com
   ポート: 5432
   データベース: running-analysis-db
   ユーザー: postgres
✅ データベース接続成功!

📊 PostgreSQLバージョン:
   PostgreSQL 15.x on ...

🕐 サーバー時刻:
   2025-10-03 ...

✅ 接続テスト完了!
```

---

### ステップ3: テーブルの作成

#### オプション1: psqlコマンドを使用（推奨）

```bash
# ローカルにpsqlがインストールされている場合
PGPASSWORD="vfmdev_01" psql \
  -h running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com \
  -p 5432 \
  -U postgres \
  -d running-analysis-db \
  -f database_schema.sql
```

または、スクリプトを使用：

```bash
./setup_database.sh
```

#### オプション2: Dockerコンテナから実行

```bash
# PostgreSQLクライアントを含むDockerイメージを使用
docker run -it --rm \
  -v $(pwd)/database_schema.sql:/schema.sql \
  postgres:15 \
  psql -h running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com \
       -p 5432 \
       -U postgres \
       -d running-analysis-db \
       -f /schema.sql
```

パスワード入力時: `vfmdev_01`

#### オプション3: AWSコンソールのクエリエディタ

```
1. AWS Console → RDS → データベース
2. running-analysis-db を選択
3. 「アクション」→「クエリエディタ」
4. 認証情報を入力
5. database_schema.sql の内容をコピー&ペースト
6. 「実行」をクリック
```

---

### ステップ4: テーブル作成の確認

```sql
-- テーブル一覧を確認
\dt

-- 各テーブルの構造を確認
\d users
\d runs
\d keypoints
\d analysis_results
\d events
\d advice
```

**期待される出力:**
```
           List of relations
 Schema |       Name        | Type  |  Owner   
--------+-------------------+-------+----------
 public | users             | table | postgres
 public | runs              | table | postgres
 public | keypoints         | table | postgres
 public | analysis_results  | table | postgres
 public | events            | table | postgres
 public | advice            | table | postgres
```

---

### ステップ5: アプリケーションからの接続テスト

```bash
# Dockerコンテナから接続テスト
docker compose run --rm video_processing python3 db_utils.py
```

**期待される結果:**
- ✅ データベース接続成功
- ✅ テストデータの保存成功

---

### ステップ6: 動画アップロードテスト

```bash
# ローカル環境でアプリケーションを起動
docker compose up -d

# フロントエンドにアクセス
open http://localhost:3000
```

1. 動画ファイルをアップロード
2. 解析完了を待つ
3. データベースを確認：

```sql
-- 最新の走行記録を確認
SELECT * FROM runs ORDER BY created_at DESC LIMIT 1;

-- 保存されたデータ数を確認
SELECT 
  (SELECT COUNT(*) FROM runs) as runs_count,
  (SELECT COUNT(*) FROM keypoints) as keypoints_count,
  (SELECT COUNT(*) FROM analysis_results) as results_count,
  (SELECT COUNT(*) FROM events) as events_count;
```

---

## 🔍 トラブルシューティング

### 問題1: 接続タイムアウト

**症状:**
```
connection to server ... timeout expired
```

**解決策:**
1. セキュリティグループでポート5432を開放
2. RDSインスタンスが起動していることを確認
3. パブリックアクセスを有効化

---

### 問題2: 認証エラー

**症状:**
```
FATAL: password authentication failed
```

**解決策:**
1. `.env`ファイルのパスワードを確認
2. RDSのマスターパスワードを再設定（必要に応じて）

---

### 問題3: データベースが存在しない

**症状:**
```
FATAL: database "running-analysis-db" does not exist
```

**解決策:**
```sql
-- postgresデータベースに接続してデータベースを作成
CREATE DATABASE "running-analysis-db";
```

---

### 問題4: テーブルが既に存在する

**症状:**
```
ERROR: relation "users" already exists
```

**解決策:**
```sql
-- テーブルを削除してから再作成（データは失われます）
DROP TABLE IF EXISTS advice CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS keypoints CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- その後、database_schema.sqlを再実行
```

---

## 📊 データベース管理ツール

### 推奨ツール

1. **pgAdmin 4** (GUI)
   - https://www.pgadmin.org/
   - Windows/Mac/Linux対応

2. **DBeaver** (GUI)
   - https://dbeaver.io/
   - 無料、クロスプラットフォーム

3. **TablePlus** (GUI, Mac/Windows)
   - https://tableplus.com/
   - 美しいUI

4. **psql** (CLI)
   - PostgreSQL公式CLIツール

### 接続設定例（pgAdmin）

```
ホスト: running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com
ポート: 5432
データベース: running-analysis-db
ユーザー名: postgres
パスワード: vfmdev_01
SSL モード: prefer
```

---

## 🎯 次のステップ

### データベース接続が確立できたら：

1. ✅ テーブルを作成
2. ✅ 動画をアップロードしてデータを保存
3. ✅ データが正しく保存されているか確認
4. ✅ EC2環境にも同じ設定をデプロイ

### 本番環境への展開：

```bash
# EC2にSSH接続
ssh -i "Runners Insight Key.pem" ec2-user@54.206.3.155

# リポジトリを更新
cd running-analysis-system
git pull origin main

# .envファイルを作成（EC2上で）
vi .env
# （接続情報を記入）

# Dockerコンテナを再ビルド・再起動
docker compose build video_processing analysis advice_generation
docker compose up -d
```

---

## 📝 チェックリスト

セットアップ完了の確認：

- [ ] RDSインスタンスが起動している
- [ ] セキュリティグループでポート5432が開放されている
- [ ] ローカルから接続テストが成功する
- [ ] テーブルが正常に作成されている
- [ ] 動画アップロードでデータが保存される
- [ ] EC2環境でも接続が確立できる
- [ ] 本番環境で動作確認が完了している

---

## 📚 参考資料

- [AWS RDS for PostgreSQL ドキュメント](https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [PostgreSQL 公式ドキュメント](https://www.postgresql.org/docs/)
- [psycopg2 ドキュメント](https://www.psycopg.org/docs/)

---

**最終更新**: 2025年10月3日  
**ステータス**: データベース接続設定待ち（セキュリティグループ設定が必要）

