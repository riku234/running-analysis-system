# アドバイスが表示されない問題 - トラブルシューティングガイド

## 🔍 考えられる原因

アドバイスが表示されない場合、以下の原因が考えられます：

---

## 1️⃣ Z値分析の失敗（最も可能性が高い）

### 原因

Z値分析でサイクルが検出されない場合、`high_level_issues` が空になり、アドバイス生成がスキップされる可能性があります。

### コード（video_processing/app/main.py 266-277行）

```python
# Z値分析結果から課題を抽出
high_level_issues = []
if z_score_data and z_score_data.get("analysis_summary", {}).get("significant_deviations"):
    for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
        if deviation["severity"] == "high":
            high_level_issues.append(f"{deviation['angle']}の{deviation['event']}異常")

logger.info(f"抽出された課題: {high_level_issues}")

if not high_level_issues:
    logger.warning("❌ 重大な偏差が検出されませんでした。デフォルトのアドバイスを使用します")
    high_level_issues = ["フォーム改善"]
```

### 確認方法

ブラウザのコンソール（F12）で以下のログを確認：

```
📊 統合イベント数: XX
✅ 検出完了 - 左足: 接地X回, 離地Y回
✅ 検出完了 - 右足: 接地X回, 離地Y回
```

**問題パターン**:
- 統合イベント数が0または4未満
- 接地または離地が0回
- `❌ サイクルが検出されませんでした` というメッセージ

### 解決策

1. **動画撮影条件を改善** → `VIDEO_REQUIREMENTS_FOR_ZSCORE_ANALYSIS.md` を参照
2. **検出パラメータを緩和** → `PROMINENCE_EXPLANATION.md` を参照

---

## 2️⃣ Gemini APIの失敗

### 原因

Gemini APIが以下のエラーで失敗する場合、アドバイス生成がスキップされます：

- **API Quota超過（429エラー）**
- **API内部エラー（500エラー）**
- **Safety Filter（finish_reason=2）**
- **API Key無効**

### コード（advice_generation/app/main.py 279-312行）

```python
max_retries = 3
response = None
for attempt in range(max_retries):
    try:
        response = current_model.generate_content(prompt)
        break
    except Exception as api_error:
        error_str = str(api_error)
        if "429" in error_str or "quota" in error_str.lower():
            # レート制限 - リトライ
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                await asyncio.sleep(wait_time)
                continue
            else:
                response = None
                break
        elif "500" in error_str or "InternalServerError" in error_str:
            # 内部エラー - リトライ
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                await asyncio.sleep(wait_time)
                continue
            else:
                response = None
                break
        else:
            # その他のエラー - すぐにフォールバック
            response = None
            break
```

### 確認方法

#### フロントエンドのコンソール

```
🎯 統合アドバイス表示デバッグ（本番環境）:
  integratedAdvice: ❌ なし
  finalAdvice: ❌ なし
  result.advice_results: ❌ なし
  result.advice_analysis: ❌ なし
```

#### バックエンドのログ（Dockerログ）

```bash
# advice_generationサービスのログを確認
docker logs running-analysis-system-advice_generation-1 --tail 50
```

**問題パターン**:
```
❌ 予期しないエラー: 429 Resource has been exhausted
❌ Gemini API内部エラー、リトライ中...
⚠️ Safety Filter発動: finish_reason=2
❌ API key not valid
```

### 解決策

#### A. API Quota超過の場合

1. **Gemini APIの使用量を確認**
   - Google AI Studio → Usage → Quota を確認
   - 無料枠: 1分あたり15リクエスト、1日あたり1500リクエスト

2. **待機時間を設ける**
   - 1分待ってから再アップロード

3. **有料プランにアップグレード**
   - Google Cloud Console → Enable Billing

#### B. Safety Filterの場合

1. **プロンプトが問題の可能性**
   - カスタムプロンプトを使用している場合、デフォルトに戻す

2. **動画内容が問題の可能性**
   - 極端に異常なフォームがSafety Filterに引っかかる可能性（稀）

#### C. API Key無効の場合

1. **環境変数を確認**
   ```bash
   # EC2の場合
   ssh -i "your-key.pem" ubuntu@54.206.3.155
   cd ~/running-analysis-system
   cat .env | grep GEMINI_API_KEY
   ```

2. **コンテナを再起動**
   ```bash
   docker compose down
   docker compose up -d
   ```

---

## 3️⃣ タイムアウト

### 原因

`video_processing` サービスから `advice_generation` サービスへのリクエストがタイムアウトします。

### コード（video_processing/app/main.py 285-292行）

```python
integrated_advice_response = await client.post(
    f"http://advice_generation:8005/generate-integrated",
    json=integrated_advice_request,
    timeout=180.0  # 180秒（3分）のタイムアウト
)
```

### 確認方法

ブラウザのネットワークタブ（F12 → Network）で：
- アップロードリクエストが3分以上かかっている
- ステータスコードが `504 Gateway Timeout`

### 解決策

通常は発生しません。Gemini APIのリトライが最大45秒（3回 × 15秒）なので、180秒のタイムアウトには余裕があります。

もし発生した場合：
```python
# timeout=180.0 を timeout=300.0 に延長
```

---

## 4️⃣ フロントエンドの表示条件

### 原因

フロントエンドでは以下の条件でアドバイスを表示します：

```typescript
const integratedAdvice = result?.advice_results?.integrated_advice || result?.advice_analysis?.integrated_advice;
const finalAdvice = integratedAdvice;

if (finalAdvice && finalAdvice.trim()) {
  // アドバイスを表示
} else {
  // 表示しない
}
```

**問題パターン**:
- `integrated_advice` が空文字列 `""`
- `integrated_advice` が空白のみ `"   "`
- `advice_results` と `advice_analysis` の両方が `undefined`

### 確認方法

ブラウザのコンソール（F12）で：

```javascript
// 以下のコマンドを実行
const savedResult = localStorage.getItem('analysisResult_最後にアップロードした動画ID');
const result = JSON.parse(savedResult);
console.log('advice_results:', result.advice_results);
console.log('advice_analysis:', result.advice_analysis);
console.log('integrated_advice:', result.advice_results?.integrated_advice);
```

### 解決策

バックエンドから正しくデータが返されているか確認。

---

## 5️⃣ データベース保存の失敗（EC2のみ）

### 原因

`ENABLE_DB_SAVE=true` の場合、データベースへの保存に失敗すると、アドバイスがデータベースに記録されません。

ただし、**フロントエンドの表示には影響しません**（レスポンスには含まれる）。

### コード（video_processing/app/main.py 420-432行）

```python
if ENABLE_DB_SAVE:
    try:
        # 統合アドバイスをデータベースに保存
        if advice_data and advice_data.get("integrated_advice"):
            advice_saved = save_integrated_advice(
                run_id=run_id,
                integrated_advice=advice_data["integrated_advice"]
            )
            if advice_saved:
                logger.info("✅ 統合アドバイスをDBに保存しました")
            else:
                logger.warning("⚠️  統合アドバイスのDB保存に失敗しました")
    except Exception as db_error:
        logger.warning(f"⚠️  DB保存中にエラーが発生しましたが、処理を続行します: {db_error}")
```

### 確認方法

EC2のDockerログで：
```bash
docker logs running-analysis-system-video_processing-1 --tail 50
```

**問題パターン**:
```
⚠️  統合アドバイスのDB保存に失敗しました
⚠️  DB保存中にエラーが発生しましたが、処理を続行します: ...
```

### 解決策

データベース接続を確認（ただし、フロントエンド表示には影響しない）。

---

## 6️⃣ LocalStorageの容量制限

### 原因

ブラウザの`localStorage`には容量制限（通常5-10MB）があり、大きなデータを保存しようとすると失敗します。

### 確認方法

ブラウザのコンソール（F12）で：
```javascript
// localStorage使用量を確認
let totalSize = 0;
for (let key in localStorage) {
  if (localStorage.hasOwnProperty(key)) {
    totalSize += localStorage[key].length + key.length;
  }
}
console.log('localStorage使用量:', (totalSize / 1024).toFixed(2), 'KB');
```

### 解決策

```javascript
// localStorageをクリア
localStorage.clear();
```

---

## 📊 診断フローチャート

```
動画アップロード
    ↓
┌────────────────────────────────────────┐
│ 1. Z値分析は成功したか？              │
└────────────────────────────────────────┘
    ↓ YES
┌────────────────────────────────────────┐
│ 2. high_level_issues が空でないか？   │
└────────────────────────────────────────┘
    ↓ YES
┌────────────────────────────────────────┐
│ 3. advice_generation サービスは起動？  │
└────────────────────────────────────────┘
    ↓ YES
┌────────────────────────────────────────┐
│ 4. Gemini APIは応答したか？           │
└────────────────────────────────────────┘
    ↓ YES
┌────────────────────────────────────────┐
│ 5. integrated_adviceは空でないか？    │
└────────────────────────────────────────┘
    ↓ YES
✅ アドバイス表示成功！
```

**どこでNOになったか**によって原因が特定できます。

---

## 🛠️ 包括的な確認方法

### ステップ1: サービスの状態確認

```bash
# すべてのサービスが起動しているか
docker compose ps

# 特にadvice_generationサービス
docker ps | grep advice_generation
```

**期待される出力**:
```
running-analysis-system-advice_generation-1  Up X minutes (healthy)
```

---

### ステップ2: Gemini API Keyの確認

```bash
# ローカル環境
cat .env | grep GEMINI_API_KEY

# EC2環境
ssh -i "your-key.pem" ubuntu@54.206.3.155
cat ~/running-analysis-system/.env | grep GEMINI_API_KEY
```

**期待される出力**:
```
GEMINI_API_KEY=AIzaSy...（有効なキー）
```

---

### ステップ3: 動画アップロード＋ログ確認

#### A. ブラウザのコンソールで確認（F12）

アップロード後、以下を確認：

```
✅ 検出完了 - 左足: 接地X回, 離地Y回
✅ 検出完了 - 右足: 接地X回, 離地Y回
📊 統合イベント数: XX

🎯 統合アドバイス表示デバッグ:
  integratedAdvice: "〇〇..." ← これがあればOK
```

#### B. Dockerログで確認

```bash
# advice_generationサービスのログ
docker logs running-analysis-system-advice_generation-1 --tail 100

# video_processingサービスのログ
docker logs running-analysis-system-video_processing-1 --tail 100
```

**期待されるログ（advice_generation）**:
```
🎯 [INTEGRATED ADVICE SERVICE] 統合アドバイスリクエスト受信
   📹 動画ID: xxx
   📝 課題数: X
   🧠 統合アドバイス生成中...
   ✅ プロコーチアドバイス生成完了
   🤖 AI詳細アドバイス生成中: 体幹角度の接地異常
   📨 Gemini応答受信: <class 'google.generativeai.types.generation_types.GenerateContentResponse'>
   ✅ AI詳細アドバイス生成完了
   ✅ 統合アドバイス生成完了（XXXX文字）
```

**問題のあるログ**:
```
❌ レート制限検出、リトライ中...
❌ Gemini API内部エラー
⚠️ Safety Filter発動
❌ 最大リトライ回数に達しました
```

---

### ステップ4: localStorageの確認

ブラウザのコンソール（F12）で以下を実行：

```javascript
// 最後のアップロード結果を取得
const lastKey = Object.keys(localStorage).find(k => k.startsWith('analysisResult_'));
const result = JSON.parse(localStorage.getItem(lastKey));

// アドバイスデータを確認
console.log('advice_results:', result.advice_results);
console.log('integrated_advice:', result.advice_results?.integrated_advice);
console.log('advice length:', result.advice_results?.integrated_advice?.length);
```

**期待される出力**:
```
advice_results: {status: "success", message: "統合アドバイスを生成しました", ...}
integrated_advice: "【総合評価】..."
advice length: 2500（例）
```

---

## 📈 頻度別の原因ランキング

### 1位: Z値分析の失敗（サイクル未検出）

**頻度**: ⭐⭐⭐⭐⭐（非常に多い）

**原因**:
- 動画が短い（3秒未満）
- 撮影角度が斜め
- 離地が検出されない

**解決策**: 動画撮影条件を改善

---

### 2位: Gemini API Quota超過

**頻度**: ⭐⭐⭐（時々）

**原因**:
- 短時間に多数の動画をアップロード
- 無料枠の上限に達した

**解決策**: 1分待ってから再試行、または有料プランにアップグレード

---

### 3位: Gemini API Safety Filter

**頻度**: ⭐⭐（稀）

**原因**:
- カスタムプロンプトに問題のある表現
- 極端に異常なフォーム

**解決策**: デフォルトプロンプトを使用

---

### 4位: API Key無効

**頻度**: ⭐（非常に稀）

**原因**:
- デプロイ時に`.env`ファイルが更新されなかった
- API Keyの有効期限切れ

**解決策**: コンテナを再起動

---

### 5位: タイムアウト

**頻度**: ⭐（非常に稀）

**原因**:
- ネットワーク遅延
- Gemini APIの応答遅延

**解決策**: タイムアウトを延長

---

## 🔧 応急処置（緊急時）

### アドバイスが全く表示されない場合

#### 方法1: デフォルトアドバイスを表示（フォールバック）

`advice_generation/app/main.py` を修正：

```python
# generate_integrated_advice 関数内（624行付近）
try:
    print(f"   🔄 統合アドバイス生成開始 - 課題数: {len(issues_list)}")
    
    # Gemini APIをスキップして、プロコーチアドバイスのみを返す（緊急時）
    coach_advice = generate_advanced_advice(issues_list)
    return coach_advice  # ← これでGemini APIを使わずに返す
    
    # 以下のGemini API処理はスキップされる
    # ...
```

#### 方法2: Gemini APIのリトライを増やす

```python
# max_retries を 3 から 5 に変更
max_retries = 5
```

#### 方法3: Prominenceを緩和（Z値検出を増やす）

```python
# backend/services/analysis/app/main.py 183行
prominence=0.001  # 0.002 から 0.001 に緩和
```

---

## 🎯 まとめ

### 最も可能性が高い原因TOP3

1. **Z値分析でサイクルが検出されない**
   → 動画撮影条件を改善

2. **Gemini API Quota超過**
   → 1分待ってから再試行

3. **Gemini API Safety Filter**
   → デフォルトプロンプトを使用

### 確認手順

1. ブラウザコンソールで「統合イベント数」を確認
2. `docker logs` で `advice_generation` のログを確認
3. `localStorage` で `integrated_advice` の有無を確認

---

**作成日**: 2025年10月21日  
**関連ドキュメント**: 
- `VIDEO_REQUIREMENTS_FOR_ZSCORE_ANALYSIS.md`（Z値検出条件）
- `PROMINENCE_EXPLANATION.md`（接地・離地検出の仕組み）

