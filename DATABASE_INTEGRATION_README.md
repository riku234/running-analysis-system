# データベース統合機能 - 実装ドキュメント

## 📋 概要

動画アップロード時に、以下のデータをすべてPostgreSQLデータベースに自動保存する機能を実装しました：

1. **動画情報**（アップロード情報、メタデータ）
2. **時系列キーポイントデータ**（全フレームの座標情報）
3. **解析結果**（Z値、角度、その他の計算結果）
4. **イベントデータ**（足接地・離地のタイミング）

---

## 🗄️ データベーススキーマ

### 1. `users` テーブル
ユーザー情報を管理

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. `runs` テーブル（メインテーブル）
走行記録とメタデータを管理

```sql
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    video_id VARCHAR(255) UNIQUE NOT NULL,
    video_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    video_fps FLOAT,
    video_duration FLOAT,
    total_frames INTEGER,
    analysis_status VARCHAR(50) DEFAULT 'processing',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

**analysis_status の値:**
- `'processing'`: 解析中
- `'completed'`: 完了
- `'failed'`: 失敗

### 3. `keypoints` テーブル
フレームごとのキーポイント座標を保存

```sql
CREATE TABLE keypoints (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    landmark_id INTEGER NOT NULL,
    landmark_name VARCHAR(100),
    x_coordinate FLOAT NOT NULL,
    y_coordinate FLOAT NOT NULL,
    z_coordinate FLOAT,
    visibility FLOAT,
    body_part VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
    UNIQUE (run_id, frame_number, landmark_id)
);
```

**保存されるランドマーク（MediaPipe 33個）:**
- nose, eyes, ears
- shoulders, elbows, wrists, hands
- hips, knees, ankles, heels, feet

### 4. `analysis_results` テーブル
計算された解析結果を保存

```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value NUMERIC NOT NULL,
    unit VARCHAR(50),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE,
    UNIQUE (run_id, metric_name)
);
```

**保存される指標例:**
- `Z値_right_strike_体幹角度`: -1.23
- `Z値_left_off_右大腿角度`: 0.85
- `角度_right_strike_体幹角度`: 5.2
- `角度_left_strike_左下腿角度`: 142.3

### 5. `events` テーブル
足接地・離地イベントを保存

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    frame_number INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    foot_side VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);
```

**event_type の値:**
- `'left_strike'`: 左足接地
- `'left_off'`: 左足離地
- `'right_strike'`: 右足接地
- `'right_off'`: 右足離地

### 6. `advice` テーブル
生成されたアドバイスを保存

```sql
CREATE TABLE advice (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    advice_text TEXT NOT NULL,
    advice_type VARCHAR(100),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);
```

---

## 🔧 実装されたPython関数

### `db_utils.py` に追加された関数

#### 1. `get_db_connection()` → Optional[connection]
PostgreSQLへの接続を確立

```python
from db_utils import get_db_connection

conn = get_db_connection()
if conn:
    # データベース操作
    conn.close()
```

#### 2. `create_run_record()` → Optional[int]
新しい走行記録を作成し、`run_id`を返す

```python
run_id = create_run_record(
    video_id="abc-123-def",
    user_id="user_001",
    video_path="/uploads/video.mp4",
    original_filename="running.mp4",
    video_fps=30.0,
    video_duration=10.5,
    total_frames=315
)
```

#### 3. `save_keypoints_data()` → bool
全フレームのキーポイントを一括保存

```python
keypoints_data = [
    {
        "frame": 0,
        "keypoints": [
            {"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.9},
            # ... 33個のキーポイント
        ]
    },
    # ... 全フレーム
]

success = save_keypoints_data(run_id, keypoints_data)
```

#### 4. `save_events_data()` → bool
イベント（足接地・離地）を保存

```python
events = [
    (10, 'right', 'strike'),
    (25, 'right', 'off'),
    (40, 'left', 'strike'),
    # ...
]

success = save_events_data(run_id, events)
```

#### 5. `save_analysis_results()` → bool
解析結果を保存

```python
results = {
    "Z値_right_strike_体幹角度": -1.23,
    "Z値_left_off_右大腿角度": 0.85,
    "角度_right_strike_体幹角度": 5.2,
    # ...
}

success = save_analysis_results(run_id, results)
```

#### 6. `update_run_status()` → bool
走行記録のステータスを更新

```python
# 処理開始時
update_run_status(run_id, 'processing')

# 完了時
update_run_status(run_id, 'completed')

# エラー時
update_run_status(run_id, 'failed')
```

---

## 🔄 処理フロー

### 動画アップロード時の処理順序

```
1. 動画ファイル受信
   ↓
2. ファイル保存（/uploads/）
   ↓
3. 骨格推定サービス呼び出し → キーポイントデータ取得
   ↓
4. 特徴量抽出サービス呼び出し
   ↓
5. 解析サービス呼び出し → Z値計算
   ↓
6. アドバイス生成サービス呼び出し
   ↓
7. 【データベース保存】
   ├─ run_id = create_run_record()
   ├─ save_keypoints_data(run_id, keypoints)
   ├─ save_events_data(run_id, events)
   ├─ save_analysis_results(run_id, results)
   └─ update_run_status(run_id, 'completed')
   ↓
8. 結果をフロントエンドに返却
```

---

## 📦 環境変数設定

`.env` ファイルに以下の環境変数を設定：

```env
# RDSデータベースへの接続情報
DB_HOST=running-analysis-db.cluster-xxxxx.ap-southeast-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
```

---

## 🚀 デプロイ手順

### 1. データベースの準備

```bash
# RDSでPostgreSQLインスタンスを作成
# セキュリティグループでポート5432を開放

# テーブルを作成
psql -h <RDS_ENDPOINT> -U postgres -d postgres -f database_schema.sql
```

### 2. .envファイルの設定

```bash
# プロジェクトルートに.envファイルを作成
vi .env

# 接続情報を記入（上記の環境変数設定を参照）
```

### 3. Dockerコンテナの再ビルド

```bash
# ローカル環境
docker compose build video_processing analysis advice_generation
docker compose up -d

# EC2環境
ssh -i "key.pem" ec2-user@<EC2_IP>
cd running-analysis-system
git pull origin main
docker compose build video_processing analysis advice_generation
docker compose up -d
```

---

## ✅ テスト方法

### 1. データベース接続テスト

```bash
# Dockerコンテナ内でテスト実行
docker compose run --rm video_processing python3 db_utils.py
```

期待される出力:
```
============================================================
🧪 データベース接続テスト
============================================================
🔌 データベースへの接続を試みています...
   ホスト: running-analysis-db.cluster-xxxxx.rds.amazonaws.com
   ポート: 5432
   データベース: postgres
   ユーザー: postgres
✅ データベース接続成功!
```

### 2. 動画アップロードテスト

```bash
# フロントエンドから動画をアップロード
# または cURLでテスト:

curl -X POST http://localhost/api/upload/upload \
  -F "file=@test_video.mp4"
```

### 3. データ確認

```sql
-- 走行記録の確認
SELECT * FROM runs ORDER BY created_at DESC LIMIT 10;

-- キーポイント数の確認
SELECT run_id, COUNT(*) as keypoint_count 
FROM keypoints 
GROUP BY run_id;

-- 解析結果の確認
SELECT run_id, metric_name, value 
FROM analysis_results 
WHERE run_id = 1;

-- イベントの確認
SELECT * FROM events WHERE run_id = 1 ORDER BY frame_number;
```

---

## 🎯 今後の拡張案

1. **ユーザー認証機能の追加**
   - 現在は `default_user` を使用
   - JWT認証を実装してuser_idを取得

2. **履歴表示機能**
   - 過去の解析結果を一覧表示
   - 比較機能（現在 vs 過去）

3. **統計分析機能**
   - 複数回のランニングデータを集計
   - 進捗グラフの生成

4. **データエクスポート機能**
   - CSV/JSON形式でエクスポート
   - レポート自動生成

5. **リアルタイム通知**
   - 解析完了時にメール/プッシュ通知

---

## 📝 注意事項

1. **セキュリティ**
   - `.env`ファイルは`.gitignore`に追加済み
   - 本番環境では環境変数を使用推奨

2. **パフォーマンス**
   - キーポイントデータは大量になる可能性あり
   - バッチ処理で1000件ずつ挿入

3. **エラーハンドリング**
   - データベースエラーが発生しても解析結果は返却
   - ステータスを'failed'に更新してログ記録

4. **データ容量**
   - 1動画あたり約10,000〜50,000レコード（キーポイント）
   - 定期的なアーカイブ・削除ポリシーの検討を推奨

---

## 📚 参考資料

- PostgreSQL公式ドキュメント: https://www.postgresql.org/docs/
- psycopg2ドキュメント: https://www.psycopg.org/docs/
- AWS RDS for PostgreSQL: https://aws.amazon.com/rds/postgresql/

---

**実装日**: 2025年10月3日  
**バージョン**: 1.0.0

