# CSVデータ移行ガイド

## 概要

CSVデータをPostgreSQLデータベースに移行し、アドバイス生成ロジックをDB駆動型にリファクタリングする手順です。

## 前提条件

- PostgreSQLデータベースが起動している
- `.env`ファイルにデータベース接続情報が設定されている
- CSVファイルが準備されている

## ステップ1: データベーススキーマの更新

### 方法1: psqlコマンドを使用

```bash
psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -f database_schema.sql
```

### 方法2: Dockerコンテナ内で実行

```bash
# データベースコンテナに接続
docker exec -i <postgres_container_name> psql -U <DB_USER> -d <DB_NAME> < database_schema.sql
```

### 方法3: Pythonスクリプトで実行

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT", "5432"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

with open('database_schema.sql', 'r') as f:
    sql = f.read()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()

conn.close()
```

## ステップ2: CSVデータの移行

### 必要なCSVファイル

1. **統計モデル検討.csv** - 診断ルールデータ
   - 必須カラム: `rule_code`, `target_metric`, `operator`, `threshold`, `severity`
   - オプションカラム: `rule_name`, `target_event`, `priority`

2. **ランニング分類.csv** - ランニング分類データ（現在は使用しません）

3. **コメント紐づけ.csv** - 専門家アドバイスデータ
   - 必須カラム: `rule_code`, `issue_name`
   - オプションカラム: `observation`, `cause`, `action`, `drill_name`, `drill_url`, `additional_notes`

### CSVファイルの配置

CSVファイルを任意のディレクトリに配置します。例：

```
/path/to/csv/files/
  ├── 統計モデル検討.csv
  ├── ランニング分類.csv
  └── コメント紐づけ.csv
```

### 移行スクリプトの実行

```bash
# 基本実行
python backend/scripts/migrate_csv_to_db.py \
    --csv-dir /path/to/csv/files

# CSV2をスキップする場合
python backend/scripts/migrate_csv_to_db.py \
    --csv-dir /path/to/csv/files \
    --skip-csv2

# カスタムファイル名を指定する場合
python backend/scripts/migrate_csv_to_db.py \
    --csv-dir /path/to/csv/files \
    --csv1 統計モデル検討.csv \
    --csv2 ランニング分類.csv \
    --csv3 コメント紐づけ.csv
```

### 実行例

```bash
# プロジェクトルートから実行
cd /Users/onoriku/Projects/running-analysis-system

# CSVファイルが ~/Downloads/csv_data/ にある場合
python backend/scripts/migrate_csv_to_db.py \
    --csv-dir ~/Downloads/csv_data
```

## ステップ3: 動作確認

### データベースの確認

```sql
-- 診断ルールの確認
SELECT * FROM diagnosis_rules ORDER BY priority DESC, rule_code;

-- 専門家アドバイスの確認
SELECT * FROM expert_advice ORDER BY rule_code;

-- ルールとアドバイスの結合確認
SELECT 
    dr.rule_code,
    dr.rule_name,
    dr.target_metric,
    dr.operator,
    dr.threshold,
    dr.severity,
    ea.issue_name,
    ea.observation,
    ea.cause,
    ea.action
FROM diagnosis_rules dr
LEFT JOIN expert_advice ea ON dr.rule_code = ea.rule_code
WHERE dr.is_active = TRUE
ORDER BY dr.priority DESC;
```

### サービスの再起動

```bash
# Docker Composeを使用している場合
docker-compose restart advice_generation

# または、完全に再ビルド
docker-compose up -d --build advice_generation
```

### APIエンドポイントのテスト

```bash
# ルールベースアドバイス生成エンドポイントをテスト
curl -X POST http://localhost:8005/generate-rule-based \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "test_video_001",
    "z_scores": {
      "right_strike": {
        "体幹角度": -2.5,
        "右大腿角度": 1.8,
        "右下腿角度": 2.3
      },
      "left_strike": {
        "体幹角度": -2.1,
        "左大腿角度": 1.5,
        "左下腿角度": 2.0
      }
    }
  }'
```

## CSVファイルの構造例

### 統計モデル検討.csv

```csv
rule_code,rule_name,target_event,target_metric,operator,threshold,severity,priority
ISSUE_TRUNK_BACKWARD,腰落ち（後傾）フォーム,right_strike,体幹角度,lt,-2.0,high,10
ISSUE_TRUNK_FORWARD,突っ込みフォーム,right_strike,体幹角度,gt,2.0,high,10
ISSUE_OVERSTRIDE,オーバーストライド,right_strike,右下腿角度,gt,2.0,high,8
ISSUE_KNEE_COLLAPSE,膝の沈み込み,right_strike,右大腿角度,gt,2.0,medium,5
```

### コメント紐づけ.csv

```csv
rule_code,issue_name,observation,cause,action,drill_name,drill_url,additional_notes
ISSUE_TRUNK_BACKWARD,腰落ち（後傾）フォーム,重心が後ろに残り、ブレーキがかかっています。脚の筋肉への負担が大きい走り方です。,骨盤が後傾しており、着地時にお尻が落ちてしまっています。,おへそからロープで前に引っ張られるようなイメージを持ち、自然な前傾姿勢を作りましょう。,ウォールドリル（壁押し）,https://youtube.com/example_wall_drill,
ISSUE_TRUNK_FORWARD,突っ込みフォーム,上半身が前に倒れすぎており、足の回転が追いついていません。,股関節からの前傾ではなく、腰から上が折れ曲がっている状態です。,頭のてっぺんを空から吊るされている意識を持ち、背筋を伸ばしたまま前傾しましょう。,トロッティング（小走り）,https://youtube.com/example_trotting,
```

## トラブルシューティング

### エラー: データベース接続に失敗

**原因**: `.env`ファイルの設定が不足している、またはデータベースが起動していない

**解決策**:
1. `.env`ファイルを確認
   ```bash
   cat .env | grep DB_
   ```
2. データベースが起動しているか確認
   ```bash
   docker ps | grep postgres
   ```

### エラー: CSVファイルが見つからない

**原因**: ファイルパスが間違っている

**解決策**:
1. ファイルパスを確認
   ```bash
   ls -la /path/to/csv/files/
   ```
2. 絶対パスを使用
   ```bash
   python backend/scripts/migrate_csv_to_db.py \
       --csv-dir /absolute/path/to/csv/files
   ```

### エラー: 必須カラムが見つからない

**原因**: CSVファイルのカラム名が想定と異なる

**解決策**:
1. CSVファイルのカラム名を確認
   ```bash
   head -1 /path/to/csv/files/統計モデル検討.csv
   ```
2. スクリプトのカラムマッピングを確認（`migrate_csv_to_db.py`の`load_and_process_csv1`関数）

### エラー: データが投入されない

**原因**: データ形式が不正、または制約違反

**解決策**:
1. ログを確認
   ```bash
   python backend/scripts/migrate_csv_to_db.py --csv-dir /path/to/csv/files 2>&1 | tee migration.log
   ```
2. データベースを直接確認
   ```sql
   SELECT COUNT(*) FROM diagnosis_rules;
   SELECT COUNT(*) FROM expert_advice;
   ```

## 次のステップ

1. **video_processingサービスの修正**: 新しいエンドポイントを呼び出すように変更
2. **フロントエンドの修正**: 新しいレスポンス形式に対応
3. **マスタデータの拡張**: 必要に応じて新しいルールを追加

## 関連ドキュメント

- `RULE_BASED_ADVICE_README.md`: ルールベースアドバイス機能の詳細
- `database_schema.sql`: データベーススキーマ定義
- `backend/scripts/migrate_csv_to_db.py`: 移行スクリプトのソースコード



