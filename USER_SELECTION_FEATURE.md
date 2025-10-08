# 👥 ユーザー選択機能 実装完了

## 🎯 概要

動画アップロード時にユーザーを選択できる機能を実装しました。選択されたユーザーIDはデータベースに保存され、誰がアップロードしたかを追跡できます。

---

## 📊 登録済みユーザー（14名）

### VFスタッフ（3名）
- **VF矢治** (`vf_yaji`)
- **VF大野** (`vf_ono`)
- **VF広川** (`vf_hirokawa`)

### Xスタッフ（5名）
- **X阿江** (`x_ae`)
- **X増田** (`x_masuda`)
- **X小松** (`x_komatsu`)
- **X鈴木** (`x_suzuki`)
- **X近野** (`x_konno`)

### ゲスト（5名）
- **ゲスト1** (`guest1`)
- **ゲスト2** (`guest2`)
- **ゲスト3** (`guest3`)
- **ゲスト4** (`guest4`)
- **ゲスト5** (`guest5`)

### システム（1名）
- **デフォルトユーザー** (`default_user`) - 既存データ用

---

## 🎨 UI実装

### アップロード画面

```
┌─────────────────────────────────────────┐
│  動画をアップロードして開始              │
│  数分で詳細な解析結果とアドバイスを...   │
├─────────────────────────────────────────┤
│  ユーザー選択                           │
│  ┌───────────────────────────────────┐ │
│  │ VF矢治                        ▼ │ │ ← プルダウン
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │     📹 動画をドラッグ＆ドロップ    │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**特徴**:
- プルダウン形式で選択
- デフォルト値: `VF矢治` (vf_yaji)
- 表示名: 日本語名（例: VF矢治）
- 送信値: 英数字ID（例: vf_yaji）

---

## 🔧 技術実装

### 1. データベース（PostgreSQL）

**usersテーブル**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,  -- 例: vf_yaji
    username VARCHAR(255),                  -- 例: VF矢治
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**runsテーブル**:
```sql
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,         -- usersテーブルを参照
    video_id VARCHAR(255) UNIQUE NOT NULL,
    ...
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

### 2. フロントエンド（Next.js + TypeScript）

**ファイル**: `frontend/app/page.tsx`

**State管理**:
```typescript
const [selectedUser, setSelectedUser] = useState<string>('vf_yaji')

const users = [
  { id: 'vf_yaji', name: 'VF矢治' },
  { id: 'vf_ono', name: 'VF大野' },
  // ...
]
```

**FormData送信**:
```typescript
const formData = new FormData()
formData.append('file', selectedFile)
formData.append('user_id', selectedUser)  // ← ユーザーIDを追加
```

### 3. バックエンド（FastAPI + Python）

**ファイル**: `backend/services/video_processing/app/main.py`

**エンドポイント**:
```python
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    user_id: str = Form("default_user"),  # ← 追加
    prompt_settings: Optional[str] = Form(None)
):
```

**バリデーション**:
```python
valid_users = [
    "vf_yaji", "vf_ono", "vf_hirokawa",
    "x_ae", "x_masuda", "x_komatsu", "x_suzuki", "x_konno",
    "guest1", "guest2", "guest3", "guest4", "guest5",
    "default_user"
]

if user_id not in valid_users:
    logger.warning(f"⚠️ 無効なuser_id: {user_id}, default_userを使用")
    user_id = "default_user"
```

**データベース保存**:
```python
run_id = create_run_record(
    video_id=unique_id,
    user_id=user_id,  # ← 選択されたユーザーIDを保存
    video_path=str(file_path),
    # ...
)
```

---

## 📝 ユーザー登録スクリプト

**ファイル**: `setup_users.py`

**機能**:
- 14名のユーザーをデータベースに一括登録
- 既存ユーザーは更新（ON CONFLICT DO UPDATE）
- ローカルとEC2の両方で実行可能

**実行方法**:
```bash
# ローカル
docker compose cp setup_users.py video_processing:/app/setup_users.py
docker compose exec video_processing python3 /app/setup_users.py

# EC2
docker-compose cp setup_users.py video_processing:/app/setup_users.py
docker-compose exec video_processing python3 /app/setup_users.py
```

**出力例**:
```
============================================================
ユーザー登録スクリプト開始
============================================================

📊 既存ユーザー: 1名
   - default_user: Default User

✅ 新規登録: vf_yaji (VF矢治)
✅ 新規登録: vf_ono (VF大野)
...

============================================================
📊 登録結果
============================================================
✅ 新規登録: 13名
🔄 更新: 1名
📝 合計: 14名

💾 データベース内の総ユーザー数: 14名
```

---

## 🔍 データベース確認方法

### ユーザー一覧の確認

```bash
docker compose exec video_processing python3 << 'PYTHON'
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()
cursor.execute("SELECT user_id, username FROM users ORDER BY user_id")
for user_id, username in cursor.fetchall():
    print(f"{user_id:20s} → {username}")
PYTHON
```

### 最新のアップロード記録の確認

```bash
docker compose exec video_processing python3 << 'PYTHON'
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()
cursor.execute("""
    SELECT r.id, r.user_id, u.username, r.video_id, r.created_at
    FROM runs r
    JOIN users u ON r.user_id = u.user_id
    ORDER BY r.created_at DESC
    LIMIT 5
""")
for run_id, user_id, username, video_id, created_at in cursor.fetchall():
    print(f"Run #{run_id}: {username} ({user_id}) - {created_at}")
PYTHON
```

---

## ✅ テスト手順

### 1. ローカル環境でテスト

1. ブラウザで `http://localhost:3000` にアクセス
2. ユーザー選択プルダウンで任意のユーザーを選択（例: VF大野）
3. 動画をアップロード
4. データベースを確認:
   ```bash
   docker compose exec video_processing python3 -c "
   import psycopg2, os
   from dotenv import load_dotenv
   load_dotenv()
   conn = psycopg2.connect(
       host=os.getenv('DB_HOST'),
       port=os.getenv('DB_PORT'),
       database=os.getenv('DB_NAME'),
       user=os.getenv('DB_USER'),
       password=os.getenv('DB_PASSWORD')
   )
   cursor = conn.cursor()
   cursor.execute('SELECT user_id, video_id FROM runs ORDER BY created_at DESC LIMIT 1')
   print(cursor.fetchone())
   "
   ```
5. 選択したユーザーIDが保存されていることを確認

### 2. EC2本番環境でテスト

1. ブラウザで `http://54.206.3.155` にアクセス
2. Basic認証（ID: xebio, PW: 20251001）
3. ユーザー選択プルダウンで任意のユーザーを選択
4. 動画をアップロード
5. EC2でデータベースを確認（上記と同じコマンド）

---

## 📦 デプロイ済み環境

### ローカル環境
- ✅ データベース: 14名登録済み
- ✅ フロントエンド: ユーザー選択UI実装済み
- ✅ バックエンド: user_id受け取り・検証・保存実装済み

### EC2本番環境
- ✅ データベース: 14名登録済み
- ✅ フロントエンド: ユーザー選択UI実装済み
- ✅ バックエンド: user_id受け取り・検証・保存実装済み
- ✅ サイトURL: http://54.206.3.155

---

## 🔄 今後のユーザー追加方法

### 新しいユーザーを追加する場合

1. **setup_users.py を編集**:
   ```python
   USERS = [
       # ... 既存ユーザー ...
       ("new_user_id", "新しいユーザー名"),  # ← 追加
   ]
   ```

2. **フロントエンドを編集** (`frontend/app/page.tsx`):
   ```typescript
   const users = [
       // ... 既存ユーザー ...
       { id: 'new_user_id', name: '新しいユーザー名' },  // ← 追加
   ]
   ```

3. **バックエンドを編集** (`backend/services/video_processing/app/main.py`):
   ```python
   valid_users = [
       # ... 既存ユーザー ...
       "new_user_id",  # ← 追加
   ]
   ```

4. **デプロイ**:
   ```bash
   # コミット
   git add setup_users.py frontend/app/page.tsx backend/services/video_processing/app/main.py
   git commit -m "Add new user: 新しいユーザー名"
   git push origin main
   
   # EC2にデプロイ
   ssh ec2-user@54.206.3.155
   cd ~/running-analysis-system
   git pull origin main
   docker-compose build frontend video_processing
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
   docker-compose cp setup_users.py video_processing:/app/setup_users.py
   docker-compose exec video_processing python3 /app/setup_users.py
   ```

---

## 🎉 完了

ユーザー選択機能が完全に実装され、ローカルとEC2の両方でデプロイ完了しました。

**動作確認**: http://54.206.3.155

お疲れ様でした！
