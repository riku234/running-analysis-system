# トレーニング動画生成機能 実装計画

## 📌 安全なロールバックポイント
```
Commit: 4cc2981fcc16d5f8a80245a28be1c48bd44845fc
Branch: main
Date: 2025-10-09
Message: Add angle time-series data feature - STABLE CHECKPOINT
```

**ロールバック方法**:
```bash
git checkout 4cc2981fcc16d5f8a80245a28be1c48bd44845fc
# または
git reset --hard 4cc2981fcc16d5f8a80245a28be1c48bd44845fc
```

---

## 🎯 機能概要

### 目的
統合アドバイス内の「おすすめの補強ドリル」の文章を元に、OpenAI Sora-2を使ってトレーニング動画を自動生成し、アドバイスカードの最下部に表示する。

### 対象データ
- **入力**: 統合アドバイスの「【💪 おすすめの補強ドリル】」セクションのテキスト
- **出力**: 生成された動画URL（一時的、保存なし）
- **表示場所**: フロントエンドの結果画面 > アドバイスカード > 最下部

### 修正点
- ✅ 動画ファイルの保存は不要（一時URLのみ使用）
- ✅ コスト制限なし（無制限）
- ✅ OpenAI APIキー提供済み

---

## 🏗️ アーキテクチャ設計

### システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  - 結果画面でアドバイスカードに動画プレイヤーを表示          │
│  - 動画生成ステータスの表示（生成中/完了/エラー）            │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (Nginx)                        │
│  - /api/video-generation/* へのルーティング                  │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│              Video Generation Service (NEW)                  │
│  - FastAPI                                                   │
│  - OpenAI API統合（responses.create）                        │
│  - 動画生成リクエスト処理                                     │
│  - 一時URLの返却のみ（保存なし）                             │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                    OpenAI API                                │
│  - model: gpt-5-nano                                         │
│  - responses.create() でテキストから動画URL生成              │
│  - 一時URLを返す（保存なし）                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL RDS) - 簡略化              │
│  - generated_videos テーブル（NEW）                          │
│  - run_id, generation_status のみ（URLは保存しない）        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 実装ステップ

### Phase 1: 環境設定とAPI統合準備 (Day 1)

#### 1.1 OpenAI API設定
- [x] OpenAI APIキーの取得（提供済み）
- [x] APIキーは`.env`ファイルに保存（セキュリティ保護）
- [ ] `.env`ファイルに`OPENAI_API_KEY`を追加
- [x] コスト制限なし（確認済み）

#### 1.2 依存関係の追加
```bash
# backend/services/video_generation/requirements.txt
openai==1.54.0
httpx==0.27.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9
fastapi==0.115.0
uvicorn==0.30.0
boto3==1.35.0  # S3使用の場合
```

#### 1.3 ディレクトリ構造の作成
```
backend/services/video_generation/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI アプリケーション
│   ├── sora_client.py   # OpenAI Sora-2 API クライアント
│   └── models.py        # Pydantic モデル
└── db_utils.py          # データベースユーティリティ
```

---

### Phase 2: データベーススキーマ拡張 (Day 1)

#### 2.1 新規テーブル作成

```sql
-- 生成動画テーブル（簡略版 - URLは保存しない）
CREATE TABLE IF NOT EXISTS generated_videos (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    generation_status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'generating', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_generated_videos_run_id ON generated_videos(run_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_status ON generated_videos(generation_status);
```

**簡略化のポイント**:
- `video_url`, `video_path` は不要（一時URLのみ使用）
- `sora_task_id` は不要（同期処理）
- `duration_seconds`, `file_size_bytes` は不要（保存しないため）

#### 2.2 データベースユーティリティ関数
- `save_video_generation_request(run_id, prompt_text)`
- `update_video_generation_status(video_id, status, video_url)`
- `get_video_by_run_id(run_id)`

---

### Phase 3: Video Generation Service実装 (Day 2-3)

#### 3.1 OpenAI Sora-2 APIクライアント

```python
# backend/services/video_generation/app/openai_client.py

import os
from openai import OpenAI

class VideoGenerationClient:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate_video(self, prompt: str) -> dict:
        """
        OpenAI responses.create() APIを使って動画URLを生成
        
        Args:
            prompt: 動画生成プロンプト（トレーニング内容）
        
        Returns:
            {
                "status": "completed",
                "video_url": "https://...",
                "output_text": "..."
            }
        
        使用例:
            prompt = "プランクのトレーニング動画: 体幹を鍛える基本エクササイズ"
            result = await client.generate_video(prompt)
        """
        try:
            # OpenAI responses.create() API呼び出し
            response = self.client.responses.create(
                model="gpt-5-nano",
                input=prompt,
                store=True
            )
            
            # 動画URLの取得（実際のレスポンス構造に合わせて調整）
            video_url = getattr(response, 'video_url', None) or getattr(response, 'output_video_url', None)
            output_text = getattr(response, 'output_text', '')
            
            return {
                "status": "completed",
                "video_url": video_url,
                "output_text": output_text
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "video_url": None,
                "error": str(e)
            }
```

#### 3.2 FastAPI エンドポイント

```python
# backend/services/video_generation/app/main.py

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

class VideoGenerationRequest(BaseModel):
    run_id: int
    prompt_text: str
    duration: int = 5

class VideoGenerationResponse(BaseModel):
    status: str
    message: str
    video_id: int
    generation_status: str

@app.post("/generate", response_model=VideoGenerationResponse)
async def generate_training_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    トレーニング動画を生成する（非同期）
    """
    # 1. データベースにリクエストを保存
    video_id = save_video_generation_request(
        run_id=request.run_id,
        prompt_text=request.prompt_text
    )
    
    # 2. バックグラウンドで動画生成を開始
    background_tasks.add_task(
        generate_video_task,
        video_id=video_id,
        prompt_text=request.prompt_text,
        duration=request.duration
    )
    
    return VideoGenerationResponse(
        status="success",
        message="動画生成を開始しました",
        video_id=video_id,
        generation_status="generating"
    )

@app.get("/status/{run_id}")
async def get_video_status(run_id: int):
    """
    動画生成のステータスを取得
    """
    video = get_video_by_run_id(run_id)
    
    if not video:
        return {"status": "not_found"}
    
    return {
        "status": "success",
        "generation_status": video["generation_status"],
        "video_url": video["video_url"],
        "error_message": video["error_message"]
    }

async def generate_video_task(video_id: int, prompt_text: str, duration: int):
    """
    バックグラウンドで動画を生成
    """
    try:
        # ステータスを「生成中」に更新
        update_video_generation_status(video_id, "generating", None)
        
        # Sora-2 APIで動画生成
        sora_client = SoraClient()
        result = await sora_client.generate_video(prompt_text, duration)
        
        # 生成完了を待つ（ポーリング）
        while result["status"] == "generating":
            await asyncio.sleep(5)
            result = await sora_client.check_generation_status(result["task_id"])
        
        if result["status"] == "completed":
            # 動画URLを保存
            update_video_generation_status(
                video_id,
                "completed",
                result["video_url"]
            )
        else:
            # エラー処理
            update_video_generation_status(
                video_id,
                "failed",
                None,
                error_message=result.get("error", "Unknown error")
            )
    
    except Exception as e:
        logger.error(f"動画生成エラー: {e}")
        update_video_generation_status(
            video_id,
            "failed",
            None,
            error_message=str(e)
        )
```

---

### Phase 4: Video Processing統合 (Day 3)

#### 4.1 アドバイス生成後に動画生成をトリガー

```python
# backend/services/video_processing/app/main.py

# アドバイス保存後に動画生成をリクエスト
if ENABLE_DB_SAVE and advice_data:
    integrated_advice = advice_data.get("integrated_advice", "")
    
    # 「おすすめの補強ドリル」セクションを抽出
    drill_section = extract_drill_section(integrated_advice)
    
    if drill_section:
        # Video Generation Serviceに動画生成をリクエスト
        video_gen_response = await client.post(
            "http://video_generation:8006/generate",
            json={
                "run_id": run_id,
                "prompt_text": f"トレーニング動画: {drill_section}",
                "duration": 5
            },
            timeout=10.0
        )
```

---

### Phase 5: フロントエンド実装 (Day 4)

#### 5.1 動画プレイヤーコンポーネント

```typescript
// frontend/app/components/TrainingVideoPlayer.tsx

interface TrainingVideoPlayerProps {
  runId: number;
}

export function TrainingVideoPlayer({ runId }: TrainingVideoPlayerProps) {
  const [videoStatus, setVideoStatus] = useState<string>("loading");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  
  useEffect(() => {
    // 動画生成ステータスをポーリング
    const pollStatus = async () => {
      const response = await fetch(`/api/video-generation/status/${runId}`);
      const data = await response.json();
      
      setVideoStatus(data.generation_status);
      if (data.video_url) {
        setVideoUrl(data.video_url);
      }
    };
    
    const interval = setInterval(pollStatus, 5000);
    pollStatus();
    
    return () => clearInterval(interval);
  }, [runId]);
  
  if (videoStatus === "generating") {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="animate-spin mr-2" />
        <span>トレーニング動画を生成中...</span>
      </div>
    );
  }
  
  if (videoStatus === "completed" && videoUrl) {
    return (
      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">
          💪 おすすめトレーニング動画
        </h3>
        <video
          src={videoUrl}
          controls
          className="w-full rounded-lg"
        />
      </div>
    );
  }
  
  return null;
}
```

#### 5.2 結果画面への統合

```typescript
// frontend/app/result/[id]/page.tsx

// アドバイスカードの最下部に追加
<Card>
  <CardHeader>
    <CardTitle>🎯 改善アドバイス</CardTitle>
  </CardHeader>
  <CardContent>
    {/* 既存のアドバイス表示 */}
    <div dangerouslySetInnerHTML={{ __html: formattedAdvice }} />
    
    {/* 新規: トレーニング動画プレイヤー */}
    <TrainingVideoPlayer runId={runId} />
  </CardContent>
</Card>
```

---

### Phase 6: Docker統合 (Day 4)

#### 6.1 Dockerfile作成

```dockerfile
# backend/services/video_generation/Dockerfile

FROM public.ecr.aws/amazonlinux/amazonlinux:2023

WORKDIR /app

RUN dnf update -y && \
    dnf install -y python3 python3-pip && \
    dnf clean all

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY db_utils.py .

EXPOSE 8006

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
```

#### 6.2 docker-compose.yml更新

```yaml
services:
  # ... 既存のサービス ...
  
  video_generation:
    build:
      context: ./backend/services/video_generation
    container_name: running-analysis-system-video_generation-1
    ports:
      - "8006:8006"
    env_file:
      - .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./videos:/app/videos  # 動画保存用（S3使用時は不要）
    depends_on:
      - video_processing
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/docs"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### 6.3 Nginx設定更新

```nginx
# backend/api_gateway/nginx.conf

location /api/video-generation/ {
    proxy_pass http://video_generation:8006/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 300s;  # 動画生成に時間がかかる
}
```

---

## 🔐 セキュリティ管理

### API キー管理
```bash
# .env
OPENAI_API_KEY=<provided_by_user>

# .gitignore に追加済みを確認
echo ".env" >> .gitignore
```

**注意**: APIキーは`.env`ファイルに保存し、Gitにはコミットしません。

### 簡略化
- ✅ コスト制限なし（無制限）
- ✅ 動画保存なし（一時URLのみ）
- ✅ レート制限なし

---

## 📊 データフロー

```
1. 動画アップロード
   ↓
2. 解析実行
   ↓
3. アドバイス生成（Gemini）
   ↓
4. 「おすすめの補強ドリル」抽出
   ↓
5. Video Generation Serviceにリクエスト
   ↓
6. データベースに生成リクエスト保存（status: generating）
   ↓
7. Sora-2 APIで動画生成（バックグラウンド）
   ↓
8. 生成完了後、video_urlを保存（status: completed）
   ↓
9. フロントエンドがポーリングで動画URLを取得
   ↓
10. 動画プレイヤーで表示
```

---

## 🧪 テスト計画

### Phase 1: ローカルテスト
1. OpenAI API接続テスト
2. Sora-2 API動画生成テスト
3. データベース保存テスト
4. フロントエンド表示テスト

### Phase 2: 統合テスト
1. エンドツーエンドテスト
2. エラーハンドリングテスト
3. タイムアウトテスト
4. 同時リクエストテスト

### Phase 3: 本番デプロイ
1. EC2環境でのテスト
2. パフォーマンステスト
3. コスト監視

---

## 📅 実装スケジュール

| Phase | タスク | 所要時間 |
|-------|--------|----------|
| 1 | 環境設定とAPI統合準備 | 4時間 |
| 2 | データベーススキーマ拡張 | 2時間 |
| 3 | Video Generation Service実装 | 8時間 |
| 4 | Video Processing統合 | 4時間 |
| 5 | フロントエンド実装 | 6時間 |
| 6 | Docker統合 | 3時間 |
| 7 | テストとデバッグ | 5時間 |
| **合計** | | **32時間（4日間）** |

---

## ⚠️ リスクと対策

### リスク1: Sora-2 API利用不可
- **対策**: 代替として、既存の動画ライブラリから類似動画を検索・表示

### リスク2: 生成時間が長い
- **対策**: バックグラウンド処理 + ポーリング + 進行状況表示

### リスク3: コスト超過
- **対策**: 生成回数制限 + コスト監視アラート

### リスク4: 動画品質が低い
- **対策**: プロンプトエンジニアリング + 事前テスト

---

## 🔄 ロールバック手順

問題が発生した場合:

```bash
# 安全なチェックポイントに戻る
cd /Users/onoriku/Projects/running-analysis-system
git checkout 4cc2981fcc16d5f8a80245a28be1c48bd44845fc

# または強制リセット
git reset --hard 4cc2981fcc16d5f8a80245a28be1c48bd44845fc

# リモートにも反映（注意！）
git push origin main --force
```

---

## 📝 次のステップ

1. ✅ 安全なチェックポイント作成完了
2. ⏭️ OpenAI APIキーの取得と設定
3. ⏭️ Sora-2 APIアクセス権限の確認
4. ⏭️ Phase 1の実装開始

---

**この計画で実装を進めてよろしいでしょうか？**
**または、修正・追加したい点がありますか？**

