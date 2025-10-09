# 動画生成機能パスワード保護 - 実装計画

## 📋 概要

**目的**: OpenAI Sora-2による動画生成は高コストのため、パスワード保護を実装して不正利用を防止する

**対象**: 結果画面の「トレーニング動画を生成」ボタン

**実装方針**: シンプルで効果的なパスワード認証

---

## 🎯 要件定義

### 機能要件

1. **パスワード入力UI**
   - 動画生成ボタンをクリックすると、パスワード入力モーダルが表示される
   - パスワードが正しい場合のみ動画生成を実行
   - パスワードが間違っている場合はエラーメッセージを表示

2. **セッション管理**
   - 一度認証に成功したら、同じセッション内では再入力不要
   - ブラウザを閉じるまで有効
   - （オプション）一定時間後に再認証を要求

3. **セキュリティ**
   - パスワードは環境変数で管理
   - フロントエンドでの簡易チェック + バックエンドでの厳密チェック
   - ブルートフォース攻撃対策（試行回数制限）

### 非機能要件

1. **ユーザビリティ**
   - シンプルで分かりやすいUI
   - エラーメッセージが明確
   - 認証済みユーザーには負担をかけない

2. **保守性**
   - パスワード変更が容易
   - 既存機能への影響を最小限に

---

## 🏗️ 実装方式の選択肢

### オプション1: フロントエンドのみでチェック（簡易版）

**メリット**:
- ✅ 実装が簡単
- ✅ レスポンスが速い
- ✅ バックエンド変更不要

**デメリット**:
- ❌ セキュリティが弱い（ブラウザの開発者ツールで回避可能）
- ❌ パスワードがフロントエンドコードに露出

**推奨度**: ⭐⭐☆☆☆（非推奨）

---

### オプション2: バックエンドでチェック（推奨）

**メリット**:
- ✅ セキュリティが高い
- ✅ パスワードがサーバー側で管理される
- ✅ ログ記録や試行回数制限が可能

**デメリット**:
- ⚠️ バックエンドの変更が必要
- ⚠️ 実装が少し複雑

**推奨度**: ⭐⭐⭐⭐⭐（推奨）

---

### オプション3: ハイブリッド方式（最適）

**メリット**:
- ✅ フロントエンドで即座にフィードバック（UX向上）
- ✅ バックエンドで厳密なチェック（セキュリティ確保）
- ✅ バランスが良い

**デメリット**:
- ⚠️ 実装箇所が2箇所

**推奨度**: ⭐⭐⭐⭐⭐（最推奨）

---

## 🎨 推奨実装: オプション3（ハイブリッド方式）

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│ フロントエンド (frontend/app/result/[id]/page.tsx)          │
│                                                               │
│  1. ユーザーが「動画生成」ボタンをクリック                   │
│  2. パスワード入力モーダルを表示                             │
│  3. パスワードを入力                                         │
│  4. フロントエンドで簡易チェック（即座にフィードバック）     │
│  5. バックエンドAPIに送信（パスワード + drill_text）        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ バックエンド (backend/services/video_generation/app/main.py)│
│                                                               │
│  1. パスワードを検証（環境変数と照合）                       │
│  2. 試行回数をチェック（ブルートフォース対策）               │
│  3. 検証成功 → 動画生成を実行                                │
│  4. 検証失敗 → 401 Unauthorized エラーを返す                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 実装詳細

### Phase 1: バックエンド実装

#### 1.1 環境変数の追加

**ファイル**: `.env`

```bash
# 動画生成パスワード
VIDEO_GENERATION_PASSWORD=your_secure_password_here
```

**ファイル**: `docker-compose.yml` & `docker-compose.prod.yml`

```yaml
video_generation:
  environment:
    - VIDEO_GENERATION_PASSWORD=${VIDEO_GENERATION_PASSWORD}
```

---

#### 1.2 パスワード検証機能の追加

**ファイル**: `backend/services/video_generation/app/main.py`

```python
import os
from datetime import datetime, timedelta
from collections import defaultdict

# パスワード設定
VIDEO_GENERATION_PASSWORD = os.getenv("VIDEO_GENERATION_PASSWORD", "")

# ブルートフォース対策: IPアドレスごとの試行回数を記録
failed_attempts = defaultdict(lambda: {"count": 0, "last_attempt": None})
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

def verify_password(password: str, client_ip: str) -> tuple[bool, str]:
    """
    パスワードを検証する
    
    Args:
        password: 入力されたパスワード
        client_ip: クライアントのIPアドレス
    
    Returns:
        (検証結果, エラーメッセージ)
    """
    # ロックアウトチェック
    if client_ip in failed_attempts:
        attempt_info = failed_attempts[client_ip]
        if attempt_info["count"] >= MAX_ATTEMPTS:
            if attempt_info["last_attempt"]:
                time_since_last = datetime.now() - attempt_info["last_attempt"]
                if time_since_last < LOCKOUT_DURATION:
                    remaining = LOCKOUT_DURATION - time_since_last
                    return False, f"試行回数が上限に達しました。{int(remaining.total_seconds() / 60)}分後に再試行してください。"
                else:
                    # ロックアウト期間が過ぎたのでリセット
                    failed_attempts[client_ip] = {"count": 0, "last_attempt": None}
    
    # パスワードチェック
    if not VIDEO_GENERATION_PASSWORD:
        logger.warning("⚠️  VIDEO_GENERATION_PASSWORD が設定されていません")
        return False, "動画生成機能は現在利用できません"
    
    if password == VIDEO_GENERATION_PASSWORD:
        # 成功したので試行回数をリセット
        if client_ip in failed_attempts:
            del failed_attempts[client_ip]
        return True, ""
    else:
        # 失敗を記録
        failed_attempts[client_ip]["count"] += 1
        failed_attempts[client_ip]["last_attempt"] = datetime.now()
        remaining_attempts = MAX_ATTEMPTS - failed_attempts[client_ip]["count"]
        
        if remaining_attempts > 0:
            return False, f"パスワードが正しくありません（残り{remaining_attempts}回）"
        else:
            return False, f"試行回数が上限に達しました。{int(LOCKOUT_DURATION.total_seconds() / 60)}分後に再試行してください。"
```

---

#### 1.3 `/generate` エンドポイントの修正

**ファイル**: `backend/services/video_generation/app/main.py`

```python
from fastapi import Request

class VideoGenerationRequest(BaseModel):
    run_id: int
    drill_text: str
    size: str
    seconds: str
    password: str  # ← 追加

@app.post("/generate", response_model=VideoGenerationResult)
async def generate_video_endpoint(request: VideoGenerationRequest, req: Request):
    """
    トレーニング動画の生成リクエストを受け付け、OpenAI Sora-2 APIを呼び出す
    """
    logger.info("================================================================================")
    logger.info("🎬 動画生成リクエスト受信")
    logger.info(f"   Run ID: {request.run_id}")
    logger.info(f"   ドリルテキスト: {request.drill_text[:100]}...")
    
    # パスワード検証
    client_ip = req.client.host
    is_valid, error_message = verify_password(request.password, client_ip)
    
    if not is_valid:
        logger.warning(f"❌ パスワード検証失敗: {client_ip} - {error_message}")
        raise HTTPException(
            status_code=401,
            detail=error_message
        )
    
    logger.info(f"✅ パスワード検証成功: {client_ip}")
    
    # 以降は既存のロジック
    # ...
```

---

### Phase 2: フロントエンド実装

#### 2.1 パスワード入力モーダルの追加

**ファイル**: `frontend/app/result/[id]/page.tsx`

```typescript
// 状態管理に追加
const [showPasswordModal, setShowPasswordModal] = useState(false)
const [videoPassword, setVideoPassword] = useState("")
const [passwordError, setPasswordError] = useState<string | null>(null)
const [pendingDrillText, setPendingDrillText] = useState<string | null>(null)

// パスワード検証（フロントエンド側の簡易チェック）
const validatePasswordFormat = (password: string): boolean => {
  // 最低限の形式チェック（空でないこと）
  return password.trim().length > 0
}

// パスワード入力ハンドラー
const handlePasswordSubmit = async () => {
  if (!validatePasswordFormat(videoPassword)) {
    setPasswordError("パスワードを入力してください")
    return
  }
  
  if (!pendingDrillText) {
    setPasswordError("エラーが発生しました")
    return
  }
  
  // モーダルを閉じて動画生成を実行
  setShowPasswordModal(false)
  setPasswordError(null)
  
  // 動画生成を実行（パスワード付き）
  await generateTrainingVideoWithPassword(pendingDrillText, videoPassword)
  
  // パスワードをクリア
  setVideoPassword("")
  setPendingDrillText(null)
}

// 動画生成ボタンのクリックハンドラー（修正版）
const handleGenerateVideoClick = (drillText: string) => {
  setPendingDrillText(drillText)
  setShowPasswordModal(true)
  setPasswordError(null)
}

// 動画生成関数（パスワード付き）
const generateTrainingVideoWithPassword = async (drillText: string, password: string) => {
  if (videoGenerating) return
  
  setVideoGenerating(true)
  setVideoError(null)
  
  try {
    console.log('🎬 トレーニング動画生成開始（パスワード認証付き）')
    
    const requestData = {
      run_id: parseInt(params.id) || 999,
      drill_text: drillText,
      size: "1280x720",
      seconds: "4",
      password: password  // ← 追加
    }
    
    const response = await fetch('/api/video-generation/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    })
    
    if (response.status === 401) {
      // パスワード認証失敗
      const errorData = await response.json()
      throw new Error(errorData.detail || 'パスワードが正しくありません')
    }
    
    if (!response.ok) {
      throw new Error(`動画生成API呼び出しエラー: ${response.status}`)
    }
    
    const videoResult = await response.json()
    console.log('🎬 動画生成結果:', videoResult)
    
    if (videoResult.status === 'success' && videoResult.video_url) {
      setTrainingVideoUrl(videoResult.video_url)
      console.log('✅ 動画URL取得成功:', videoResult.video_url)
    } else {
      throw new Error(videoResult.error || '動画生成に失敗しました')
    }
  } catch (error) {
    console.error('❌ 動画生成エラー:', error)
    setVideoError(`動画生成に失敗しました: ${error}`)
  } finally {
    setVideoGenerating(false)
  }
}
```

---

#### 2.2 パスワードモーダルのUI

**ファイル**: `frontend/app/result/[id]/page.tsx`

```tsx
{/* パスワード入力モーダル */}
{showPasswordModal && (
  <div 
    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    onClick={() => {
      setShowPasswordModal(false)
      setPasswordError(null)
      setVideoPassword("")
      setPendingDrillText(null)
    }}
  >
    <div 
      className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
      onClick={(e) => e.stopPropagation()}
    >
      <h3 className="text-xl font-bold mb-4 text-gray-800">
        🔒 動画生成の認証
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        動画生成機能を利用するにはパスワードが必要です
      </p>
      
      <input
        type="password"
        value={videoPassword}
        onChange={(e) => {
          setVideoPassword(e.target.value)
          setPasswordError(null)
        }}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handlePasswordSubmit()
          }
        }}
        placeholder="パスワードを入力"
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 mb-2"
        autoFocus
      />
      
      {passwordError && (
        <p className="text-sm text-red-600 mb-4">
          ⚠️ {passwordError}
        </p>
      )}
      
      <div className="flex gap-3">
        <Button
          onClick={handlePasswordSubmit}
          className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
        >
          確認
        </Button>
        <Button
          onClick={() => {
            setShowPasswordModal(false)
            setPasswordError(null)
            setVideoPassword("")
            setPendingDrillText(null)
          }}
          variant="outline"
          className="flex-1"
        >
          キャンセル
        </Button>
      </div>
    </div>
  </div>
)}
```

---

#### 2.3 生成ボタンの修正

**ファイル**: `frontend/app/result/[id]/page.tsx`

```tsx
<Button
  onClick={() => {
    const drillSection = finalAdvice.match(/【💪 おすすめの補強ドリル】[\s\S]*?(?=【|$)/)?.[0]
    if (drillSection) {
      handleGenerateVideoClick(drillSection)  // ← 修正
    } else {
      handleGenerateVideoClick(finalAdvice.substring(0, 200))  // ← 修正
    }
  }}
  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
>
  <PlayCircle className="w-4 h-4 mr-2" />
  トレーニング動画を生成
</Button>
```

---

### Phase 3: デプロイと設定

#### 3.1 パスワードの設定

1. **ローカル環境**:
   ```bash
   echo "VIDEO_GENERATION_PASSWORD=your_secure_password" >> .env
   ```

2. **EC2環境**:
   ```bash
   ssh ec2-user@54.206.3.155
   cd ~/running-analysis-system
   echo "VIDEO_GENERATION_PASSWORD=your_secure_password" >> .env
   ```

#### 3.2 サービスの再起動

```bash
# ローカル
docker-compose build video_generation frontend
docker-compose up -d video_generation frontend

# EC2
ssh ec2-user@54.206.3.155
cd ~/running-analysis-system
docker-compose build video_generation frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d video_generation frontend
```

---

## 🔐 セキュリティ考慮事項

### 1. パスワードの強度

**推奨**:
- 最低12文字以上
- 大文字、小文字、数字、記号を含む
- 辞書に載っていない単語

**例**: `Vfm2025!RunGen#Secure`

### 2. パスワードの管理

- ✅ 環境変数で管理（`.env`ファイル）
- ✅ `.env`ファイルは`.gitignore`に含める
- ✅ 定期的にパスワードを変更
- ✅ 必要最小限の人数にのみ共有

### 3. ブルートフォース対策

- ✅ 試行回数制限（5回）
- ✅ ロックアウト期間（15分）
- ✅ IPアドレスベースの制限

### 4. ログ記録

```python
# 成功・失敗をログに記録
logger.info(f"✅ 動画生成認証成功: IP={client_ip}, Run ID={request.run_id}")
logger.warning(f"❌ 動画生成認証失敗: IP={client_ip}, 試行回数={attempt_count}")
```

---

## 📊 実装スケジュール

| フェーズ | タスク | 所要時間 | 優先度 |
|---------|--------|---------|--------|
| **Phase 1** | バックエンド実装 | 1-2時間 | 高 |
| - | 環境変数追加 | 15分 | 高 |
| - | パスワード検証機能 | 30分 | 高 |
| - | エンドポイント修正 | 30分 | 高 |
| - | テスト | 30分 | 高 |
| **Phase 2** | フロントエンド実装 | 1-2時間 | 高 |
| - | 状態管理追加 | 15分 | 高 |
| - | モーダルUI作成 | 45分 | 高 |
| - | 生成ボタン修正 | 15分 | 高 |
| - | テスト | 30分 | 高 |
| **Phase 3** | デプロイ | 30分 | 高 |
| - | ローカル環境設定 | 10分 | 高 |
| - | EC2環境設定 | 10分 | 高 |
| - | 動作確認 | 10分 | 高 |

**合計所要時間**: 約3-4時間

---

## ✅ テストシナリオ

### 1. 正常系

1. ✅ 正しいパスワードで動画生成が成功する
2. ✅ 一度認証に成功したら、同じセッション内では再入力不要（オプション）

### 2. 異常系

1. ✅ 間違ったパスワードでエラーメッセージが表示される
2. ✅ 5回失敗すると15分間ロックアウトされる
3. ✅ パスワード未入力でエラーメッセージが表示される
4. ✅ キャンセルボタンでモーダルが閉じる

### 3. セキュリティ

1. ✅ パスワードがフロントエンドコードに露出していない
2. ✅ パスワードがネットワークログに平文で記録されない（HTTPS使用）
3. ✅ ブルートフォース攻撃が防がれる

---

## 🚀 将来の拡張案

### オプション機能

1. **セッション管理の改善**
   - JWTトークンによる認証
   - 有効期限付きトークン

2. **ユーザー管理**
   - 複数のパスワード（ユーザーごと）
   - 使用回数制限

3. **監視とアラート**
   - 動画生成回数の監視
   - 異常なアクセスパターンの検出
   - Slackへの通知

4. **コスト管理**
   - 1日あたりの生成回数制限
   - ユーザーごとの使用量トラッキング

---

## 📝 まとめ

この計画により、以下が実現されます：

✅ **コスト削減**: 不正利用を防止し、動画生成コストを管理
✅ **セキュリティ**: パスワード保護とブルートフォース対策
✅ **ユーザビリティ**: シンプルで分かりやすいUI
✅ **保守性**: 環境変数による柔軟な管理

**推奨実装方式**: オプション3（ハイブリッド方式）

**実装開始の準備ができたら、お知らせください！**

