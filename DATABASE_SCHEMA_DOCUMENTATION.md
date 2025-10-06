# データベーススキーマ仕様書

## 概要

このドキュメントは、Running Analysis System（ランニング解析システム）のデータベース構造とデータ格納仕様を説明します。

---

## データベース情報

- **データベース名**: `postgres`
- **DBMS**: PostgreSQL 17.4
- **ホスト**: AWS RDS (running-analysis-db-single.cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com)
- **インスタンスタイプ**: Single Instance
- **文字エンコーディング**: UTF-8
- **最終更新日**: 2025-10-06

---

## テーブル一覧

| テーブル名 | 説明 | 主な用途 |
|-----------|------|---------|
| `users` | ユーザー情報 | ユーザー認証・管理 |
| `runs` | 走行記録 | 動画アップロード情報 |
| `keypoints` | キーポイントデータ | 骨格推定結果（33ランドマーク） |
| `analysis_results` | 解析結果 | Z値、角度などの計算結果 |
| `events` | イベントデータ | 足接地・離地のタイミング |
| `advice` | アドバイス | 生成されたアドバイス（将来の拡張用） |

---

## 1. users テーブル

ユーザー情報を管理するテーブル。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `user_id` | VARCHAR(255) | PRIMARY KEY | ユーザーID（一意） |
| `username` | VARCHAR(255) | NOT NULL | ユーザー名 |
| `email` | VARCHAR(255) | UNIQUE | メールアドレス |
| `created_at` | TIMESTAMP | DEFAULT NOW() | アカウント作成日時 |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 最終更新日時 |

### データ例

```sql
user_id: "default_user"
username: "Default User"
email: "default@example.com"
created_at: 2025-10-03 07:50:00
updated_at: 2025-10-03 07:50:00
```

### 用途

- 現在は `default_user` のみ使用
- 将来的にユーザー認証機能を追加する際の基盤

---

## 2. runs テーブル

動画アップロードごとの走行記録を管理するテーブル。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `id` | SERIAL | PRIMARY KEY | 走行ID（自動採番） |
| `user_id` | VARCHAR(255) | FOREIGN KEY → users(user_id) | ユーザーID |
| `video_id` | VARCHAR(255) | UNIQUE, NOT NULL | 動画の一意識別子（UUID） |
| `video_path` | TEXT | | 動画ファイルのサーバー上のパス |
| `original_filename` | VARCHAR(255) | | アップロードされた元のファイル名 |
| `video_fps` | DOUBLE PRECISION | | 動画のフレームレート |
| `video_duration` | DOUBLE PRECISION | | 動画の長さ（秒） |
| `total_frames` | INTEGER | | 動画の総フレーム数 |
| `analysis_status` | VARCHAR(50) | DEFAULT 'processing' | 解析ステータス |
| `created_at` | TIMESTAMP | DEFAULT NOW() | レコード作成日時 |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 最終更新日時 |

### analysis_status の値

- `processing`: 処理中
- `completed`: 完了
- `failed`: 失敗

### データ例

```sql
id: 6
user_id: "default_user"
video_id: "837fdeca-a276-4a06-8746-d539581f3afe"
video_path: "/app/uploads/837fdeca-a276-4a06-8746-d539581f3afe.mov"
original_filename: "前傾.mov"
video_fps: 30.00
video_duration: 4.17
total_frames: 125
analysis_status: "completed"
created_at: 2025-10-06 04:13:40
updated_at: 2025-10-06 04:13:50
```

### 用途

- 動画アップロード情報の管理
- 解析ステータスの追跡
- 他のテーブルとの関連付け（外部キー）

---

## 3. keypoints テーブル

MediaPipe Poseで検出された骨格キーポイント（33ランドマーク）のデータを格納するテーブル。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `id` | SERIAL | PRIMARY KEY | レコードID（自動採番） |
| `run_id` | INTEGER | FOREIGN KEY → runs(id) | 走行ID |
| `frame_number` | INTEGER | NOT NULL | フレーム番号（0始まり） |
| `landmark_id` | INTEGER | NOT NULL | ランドマークID（0-32） |
| `landmark_name` | VARCHAR(50) | | ランドマーク名 |
| `x_coordinate` | DOUBLE PRECISION | | X座標（0.0-1.0の正規化値） |
| `y_coordinate` | DOUBLE PRECISION | | Y座標（0.0-1.0の正規化値） |
| `z_coordinate` | DOUBLE PRECISION | | Z座標（深度情報） |
| `visibility` | DOUBLE PRECISION | | 可視性スコア（0.0-1.0） |
| `created_at` | TIMESTAMP | DEFAULT NOW() | レコード作成日時 |

### 複合ユニーク制約

```sql
UNIQUE (run_id, frame_number, landmark_id)
```

### MediaPipe Pose ランドマーク一覧（33個）

| ID | landmark_name | 日本語名 |
|----|--------------|---------|
| 0 | nose | 鼻 |
| 1 | left_eye_inner | 左目（内側） |
| 2 | left_eye | 左目 |
| 3 | left_eye_outer | 左目（外側） |
| 4 | right_eye_inner | 右目（内側） |
| 5 | right_eye | 右目 |
| 6 | right_eye_outer | 右目（外側） |
| 7 | left_ear | 左耳 |
| 8 | right_ear | 右耳 |
| 9 | mouth_left | 口（左） |
| 10 | mouth_right | 口（右） |
| 11 | left_shoulder | 左肩 |
| 12 | right_shoulder | 右肩 |
| 13 | left_elbow | 左肘 |
| 14 | right_elbow | 右肘 |
| 15 | left_wrist | 左手首 |
| 16 | right_wrist | 右手首 |
| 17 | left_pinky | 左小指 |
| 18 | right_pinky | 右小指 |
| 19 | left_index | 左人差し指 |
| 20 | right_index | 右人差し指 |
| 21 | left_thumb | 左親指 |
| 22 | right_thumb | 右親指 |
| 23 | left_hip | 左腰 |
| 24 | right_hip | 右腰 |
| 25 | left_knee | 左膝 |
| 26 | right_knee | 右膝 |
| 27 | left_ankle | 左足首 |
| 28 | right_ankle | 右足首 |
| 29 | left_heel | 左かかと |
| 30 | right_heel | 右かかと |
| 31 | left_foot_index | 左足人差し指 |
| 32 | right_foot_index | 右足人差し指 |

### データ例

```sql
id: 12345
run_id: 6
frame_number: 50
landmark_id: 27
landmark_name: "left_ankle"
x_coordinate: 0.4523
y_coordinate: 0.8234
z_coordinate: -0.0123
visibility: 0.9567
created_at: 2025-10-06 04:13:45
```

### データ量

- **1フレームあたり**: 33レコード（33ランドマーク）
- **125フレームの動画**: 約4,125レコード（実際は検出できなかったフレームがある場合、それより少ない）
- **実測値（Run ID: 6）**: 119フレーム検出、3,927レコード保存（95.2%の検出率）

### 用途

- ランニングフォームの詳細分析
- 角度計算の基礎データ
- 時系列での動きの追跡

---

## 4. analysis_results テーブル

Z値分析や角度計算などの解析結果を格納するテーブル。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `id` | SERIAL | PRIMARY KEY | レコードID（自動採番） |
| `run_id` | INTEGER | FOREIGN KEY → runs(id) | 走行ID |
| `metric_name` | VARCHAR(255) | NOT NULL | 指標名 |
| `value` | DOUBLE PRECISION | NOT NULL | 計算値 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | レコード作成日時 |

### metric_name の命名規則

#### Z値データ

```
Z値_{イベント種類}_{角度名}
```

**イベント種類:**
- `right_strike`: 右足接地
- `right_off`: 右足離地
- `left_strike`: 左足接地
- `left_off`: 左足離地

**角度名:**
- `体幹角度`: 体幹の前傾角度
- `左大腿角度`: 左大腿の角度
- `右大腿角度`: 右大腿の角度
- `左下腿角度`: 左下腿の角度
- `右下腿角度`: 右下腿の角度

#### 角度データ

```
角度_{イベント種類}_{角度名}
```

### データ例

```sql
-- Z値データ
id: 1001
run_id: 6
metric_name: "Z値_left_off_体幹角度"
value: 4.088
created_at: 2025-10-06 04:13:48

-- 角度データ
id: 1021
run_id: 6
metric_name: "Z値_left_off_右下腿角度"
value: -10.248
created_at: 2025-10-06 04:13:48
```

### Z値の解釈

| Z値の範囲 | 評価 | 意味 |
|----------|------|------|
| \|Z\| < 2.0 | 正常範囲 | 標準的なフォーム |
| 2.0 ≤ \|Z\| < 3.0 | 注意 | やや標準から外れている |
| \|Z\| ≥ 3.0 | 要改善 | 標準から大きく外れている |

### データ量

- **1回の解析あたり**: 約15-40レコード（検出されたイベント数に依存）
  - Z値のみ保存（イベント種類 × 角度種類）
  - **実測値（Run ID: 6）**: 15レコード保存

### 用途

- フォーム分析結果の保存
- 経時的な改善の追跡
- 統計分析の基礎データ

---

## 5. events テーブル

足接地・離地のタイミング情報を格納するテーブル。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `id` | SERIAL | PRIMARY KEY | レコードID（自動採番） |
| `run_id` | INTEGER | FOREIGN KEY → runs(id) | 走行ID |
| `frame_number` | INTEGER | NOT NULL | イベント発生フレーム番号 |
| `foot_side` | VARCHAR(10) | NOT NULL | 足の左右（'left' or 'right'） |
| `event_type` | VARCHAR(20) | NOT NULL | イベント種類 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | レコード作成日時 |

### event_type の値

| 値 | 説明 |
|----|------|
| `left_strike` | 左足接地 |
| `left_off` | 左足離地 |
| `right_strike` | 右足接地 |
| `right_off` | 右足離地 |

### データ例

```sql
id: 501
run_id: 6
frame_number: 15
foot_side: "left"
event_type: "left_strike"
created_at: 2025-10-06 04:13:47
```

### データ量

- **1回の解析あたり**: 10-20レコード（動画の長さに依存）
- **平均的な4秒の動画**: 約19レコード
  - 左足接地: 5-6回
  - 左足離地: 5-6回
  - 右足接地: 4-5回
  - 右足離地: 4-5回
- **実測値（Run ID: 6）**: 19レコード
  - left_strike: 6件（フレーム 10〜115）
  - left_off: 5件（フレーム 19〜104）
  - right_strike: 4件（フレーム 5〜102）
  - right_off: 4件（フレーム 32〜114）

### 用途

- ランニングサイクルの特定
- ピッチ（歩数/分）の計算
- 接地時間の計算
- 左右バランスの分析

---

## 6. advice テーブル

生成されたアドバイス情報を格納するテーブル（将来の拡張用）。

### スキーマ

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| `id` | SERIAL | PRIMARY KEY | レコードID（自動採番） |
| `run_id` | INTEGER | FOREIGN KEY → runs(id) | 走行ID |
| `issue` | TEXT | | 検出された課題 |
| `advice_text` | TEXT | | アドバイス内容 |
| `priority` | VARCHAR(20) | | 優先度（'high', 'medium', 'low'） |
| `created_at` | TIMESTAMP | DEFAULT NOW() | レコード作成日時 |

### 現在の状態

- **現在は未使用**（0件）
- アドバイスは現在、API レスポンスとして返されるのみ
- 将来的に、過去のアドバイス履歴を保存・参照する機能を実装する際に使用予定

---

## データフロー

### 1. 動画アップロード時

```
1. users テーブル確認
   ↓
2. runs テーブルに新規レコード作成
   ├─ user_id: "default_user"
   ├─ video_id: UUID生成
   ├─ analysis_status: "processing"
   └─ 動画メタデータ（FPS、長さ、フレーム数）
   ↓
3. 骨格推定実行
   ↓
4. keypoints テーブルに一括保存
   └─ 全フレーム × 33ランドマーク
   ↓
5. Z値分析実行
   ↓
6. events テーブルに保存
   └─ 足接地・離地イベント
   ↓
7. analysis_results テーブルに保存
   ├─ Z値データ（20件）
   └─ 角度データ（20件）
   ↓
8. runs テーブルのステータス更新
   └─ analysis_status: "completed"
```

### 2. 結果表示時

```
1. runs テーブルから走行情報取得
   ↓
2. keypoints テーブルから骨格データ取得
   ↓
3. analysis_results テーブルから解析結果取得
   ↓
4. events テーブルからイベント情報取得
   ↓
5. フロントエンドで可視化
```

---

## インデックス

### 既存のインデックス

1. **PRIMARY KEY インデックス** (各テーブル)
   - 自動的に作成される

2. **UNIQUE制約インデックス**
   - `users(user_id)`
   - `runs(video_id)`
   - `keypoints(run_id, frame_number, landmark_id)`

3. **FOREIGN KEY インデックス**
   - 自動的に作成される

### 推奨される追加インデックス（将来の最適化用）

```sql
-- 頻繁に検索されるカラムにインデックスを追加
CREATE INDEX idx_runs_user_id ON runs(user_id);
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX idx_keypoints_run_id ON keypoints(run_id);
CREATE INDEX idx_keypoints_frame_number ON keypoints(run_id, frame_number);
CREATE INDEX idx_analysis_results_run_id ON analysis_results(run_id);
CREATE INDEX idx_events_run_id ON events(run_id);
```

---

## データサイズの見積もり

### 典型的な4秒の動画（125フレーム）の場合

| テーブル | レコード数 | 1レコードサイズ（概算） | 合計サイズ |
|---------|-----------|---------------------|-----------|
| runs | 1 | 500 bytes | 500 bytes |
| keypoints | 3,927 | 100 bytes | 約380 KB |
| analysis_results | 15 | 80 bytes | 約1.2 KB |
| events | 19 | 60 bytes | 約1.1 KB |
| **合計** | **3,962** | - | **約383 KB** |

**実測値（2025年10月6日時点）:**
- 総runs数: 3件
- 総keypoints数: 7,887件
- 総analysis_results数: 80件
- 総events数: 38件

### 年間のデータ増加見積もり

**仮定:**
- 1日あたり100動画アップロード
- 年間稼働日数: 365日

**年間データ量:**
- レコード数: 約145万レコード
- データサイズ: 約14 GB

---

## バックアップとメンテナンス

### 推奨事項

1. **定期バックアップ**
   - 日次: 自動バックアップ（AWS RDS機能）
   - 週次: 手動スナップショット

2. **古いデータのアーカイブ**
   - 6ヶ月以上前のデータは別テーブルに移動
   - または圧縮して保存

3. **インデックスの再構築**
   - 月次でVACUUM ANALYZE実行

---

## セキュリティ

### アクセス制御

- **アプリケーション用ユーザー**: 読み書き権限
- **管理者ユーザー**: 全権限
- **読み取り専用ユーザー**: SELECT権限のみ

### 機密データ

- 現在、個人情報は最小限（メールアドレスのみ）
- 将来的にユーザー認証を追加する場合は、パスワードのハッシュ化が必須

---

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0 | 2025-10-03 | 初版作成 |
| 1.1 | 2025-10-06 | データベースエンドポイント変更（cluster → single）、実測値追加、データ例更新 |

---

## 関連ドキュメント

- `database_schema.sql`: テーブル作成SQLスクリプト
- `DATABASE_INTEGRATION_README.md`: データベース統合の概要
- `DATABASE_SETUP_GUIDE.md`: データベースセットアップガイド

