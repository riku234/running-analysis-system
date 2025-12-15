# ランニング動画自動解析システム - Gemini向けアプリ概要

**作成日**: 2025年1月26日  
**目的**: Gemini AIにこのアプリケーションの全体像と、特にアドバイス生成機能について詳しく説明するためのドキュメント

---

## 📋 目次

1. [アプリケーション概要](#1-アプリケーション概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [アドバイス生成機能の詳細](#3-アドバイス生成機能の詳細) ⭐ **重要：改善予定**
4. [データフロー](#4-データフロー)
5. [技術スタック](#5-技術スタック)
6. [主要機能](#6-主要機能)
7. [現在の課題と改善点](#7-現在の課題と改善点)

---

## 1. アプリケーション概要

### 1.1 プロジェクト名
**ランニング動画自動解析エキスパートシステム** (Running Analysis System)

### 1.2 目的
ランニング動画をアップロードすると、AIが自動的にフォームを解析し、詳細な評価と改善アドバイスを提供するWebアプリケーションです。

### 1.3 主な機能
- **動画アップロード**: MP4, AVI, MOV形式に対応
- **骨格検出**: MediaPipe Poseによる33個のランドマークを高精度検出
- **特徴量解析**: ストライド長、ケイデンス、関節角度、接地時間などを計算
- **Z値統計分析**: 標準モデルとの偏差を統計的に評価
- **改善アドバイス生成**: Gemini AIによる個別最適化されたアドバイス（⭐ 改善予定）

---

## 2. システムアーキテクチャ

### 2.1 マイクロサービス構成

```
┌─────────────────┐
│   Frontend      │  Next.js 14, TypeScript, Tailwind CSS
│   Port: 3000    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Gateway   │  Nginx (リバースプロキシ)
│   Port: 80      │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬──────────────┐
    │         │              │              │
    ▼         ▼              ▼              ▼
┌────────┐ ┌────────┐  ┌────────┐  ┌────────┐
│Video   │ │Pose    │  │Feature │  │Analysis│
│Process │ │Estimate│  │Extract │  │(Z-Score)│
│8001    │ │8002    │  │8003    │  │8004    │
└────────┘ └────────┘  └────────┘  └────┬───┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │Advice        │    │Video         │    │Database      │
            │Generation    │    │Generation    │    │(PostgreSQL)  │
            │8005          │    │8006          │    │              │
            └──────────────┘    └──────────────┘    └──────────────┘
```

### 2.2 サービス詳細

| サービス | 技術スタック | 役割 |
|---------|-------------|------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Zustand | ユーザーインターフェース |
| **API Gateway** | Nginx | リクエストルーティングと負荷分散 |
| **Video Processing** | FastAPI, OpenCV, FFmpeg | 動画前処理、フレーム抽出、ワークフロー制御 |
| **Pose Estimation** | FastAPI, MediaPipe Pose | 骨格キーポイント検出（33個のランドマーク） |
| **Feature Extraction** | FastAPI, NumPy, SciPy | 生体力学的特徴量計算（角度、メトリクス） |
| **Analysis (Z-Score)** | FastAPI, NumPy, SciPy | 接地・離地イベント検出、Z値統計分析 |
| **Advice Generation** | FastAPI, Google Gemini API | 改善アドバイス生成（⭐ 改善予定） |
| **Video Generation** | FastAPI, OpenAI Sora-2 API | 改善動画生成（オプション機能） |

---

## 3. アドバイス生成機能の詳細 ⭐ **重要：改善予定**

### 3.1 概要

アドバイス生成機能は、Z値分析で検出された課題を基に、**プロコーチアドバイス（データベース）**と**Gemini AI詳細アドバイス**を統合して、ユーザーに個別最適化された改善提案を提供します。

### 3.2 データフロー（アドバイス生成まで）

```
1. 動画アップロード
   ↓
2. 骨格検出 (Pose Estimation)
   ↓
3. 特徴量抽出 (Feature Extraction)
   ↓
4. Z値分析 (Analysis)
   ├─ 接地・離地イベント検出
   ├─ 各イベント時の角度を抽出
   ├─ 標準モデルとの偏差をZ値計算
   └─ 有意な偏差を検出（|Z| ≥ 2.0）
   ↓
5. 課題抽出 (Video Processing)
   ├─ Z値分析結果から課題リストを作成
   └─ 高レベル課題（high_level_issues）を生成
   ↓
6. 統合アドバイス生成 (Advice Generation) ⭐
   ├─ プロコーチアドバイス生成（データベース）
   ├─ Gemini AI詳細アドバイス生成（個別課題ごと）
   └─ 統合して最終アドバイスを作成
```

### 3.3 課題抽出の仕組み

#### 3.3.1 Z値分析結果の構造

Z値分析サービス（`backend/services/analysis/app/main.py`）は以下のような構造のデータを返します：

```python
{
  "status": "success",
  "analysis_summary": {
    "significant_deviations": [
      {
        "event": "right_strike",      # イベント種別（接地/離地）
        "angle": "右大腿角度",         # 角度名（日本語）
        "z_score": 2.5,               # Z値（|Z| ≥ 2.0が有意）
        "severity": "high"            # 重要度（high/medium）
      },
      {
        "event": "left_strike",
        "angle": "左下腿角度",
        "z_score": -2.8,
        "severity": "high"
      }
      # ... 他の偏差
    ]
  }
}
```

#### 3.3.2 課題リストへの変換

`video_processing`サービス（`backend/services/video_processing/app/main.py` 259-274行）で、Z値分析結果から課題リストを抽出します：

```python
# Z値分析結果から課題を抽出（統合アドバイス用）
high_level_issues = []
if z_score_data and z_score_data.get("analysis_summary", {}).get("significant_deviations"):
    for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
        # 角度名を簡略化（例: "右大腿角度" -> "右大腿角度大"）
        angle_mapping = {
            "右大腿角度": "右大腿角度大",
            "左大腿角度": "左大腿角度大", 
            "右下腿角度": "右下腿角度大",
            "左下腿角度": "左下腿角度大",
            "体幹角度": "体幹後傾" if deviation["z_score"] < 0 else "体幹前傾"
        }
        
        mapped_issue = angle_mapping.get(deviation["angle"], deviation["angle"])
        if mapped_issue not in high_level_issues:
            high_level_issues.append(mapped_issue)

# 課題がない場合はデフォルト
if not high_level_issues:
    high_level_issues = ["フォーム改善"]
```

**重要なポイント**:
- `severity == "high"` の偏差のみを抽出（`video_processing`では全偏差を抽出）
- 角度名を簡略化して、プロコーチアドバイスデータベースのキーと一致させる
- 課題がない場合は `["フォーム改善"]` をデフォルトとして使用

### 3.4 統合アドバイス生成の詳細

#### 3.4.1 エンドポイント

**`POST /generate-integrated`** (`backend/services/advice_generation/app/main.py` 1210-1275行)

#### 3.4.2 リクエスト形式

```python
{
  "video_id": "unique_video_id",
  "issues_list": ["右大腿角度大", "左下腿角度大", "体幹後傾"],
  "prompt_settings": {  # オプション
    "use_custom_prompt": true,
    "custom_prompt": "あなたは専門コーチです。{issue}について...",
    "temperature": 0.7,
    "top_p": 0.8,
    "max_output_tokens": 1000
  }
}
```

#### 3.4.3 処理フロー

統合アドバイス生成は以下の4ステップで実行されます：

##### ステップ1: 根本課題の特定

```python
def identify_main_finding(issues_list: List[str]) -> str:
    """
    課題リストから根本的な問題を特定する
    
    例:
    - ["右大腿角度大", "左下腿角度大"] → "オーバーストライド"
    - ["体幹後傾"] → "体幹後傾フォーム"
    - ["上下動大"] → "エネルギー効率の低下"
    """
```

**ロジック**:
1. 大腿角度大や下腿角度大が複数ある場合 → `"オーバーストライド"`
2. 体幹関連の問題がある場合 → `"体幹後傾フォーム"` または `"体幹前傾フォーム"`
3. 上下動大がある場合 → `"エネルギー効率の低下"`
4. ピッチ低がある場合 → `"ピッチ不足"`
5. その他 → `"ランニングフォームの効率性"` または `"フォーム全般"`

##### ステップ2: プロコーチアドバイス生成（データベース）

```python
def generate_advanced_advice(issues_list: List[str]) -> str:
    """
    複数の課題を考慮した高レベルなアドバイスを生成する
    
    データベース（get_advice_database()）から構造化されたアドバイスを取得
    """
```

**データベース構造** (`backend/services/advice_generation/app/main.py` 88-172行):

```python
advice_db = {
    # 単一の課題に対するアドバイス
    "体幹後傾": {
        "description": "走行中に体が後ろに傾いている（後傾している）可能性があります。",
        "action": "おへそから前に引っ張られるようなイメージで、自然な前傾姿勢を意識しましょう。",
        "drill": "補強ドリルとして、壁を使った前傾姿勢の練習（ウォールドリル）が効果的です。"
    },
    "右大腿角度大": {
        "description": "右足の大腿部の角度が大きく、オーバーストライドになっている可能性があります。",
        "action": "右足の着地位置を体の重心により近づけることを意識しましょう。",
        "drill": "右足を中心とした片足立ちバランス練習や、右脚のもも上げ運動が効果的です。"
    },
    # ... 他の課題
    
    # 複数の課題を組み合わせたアドバイス
    "大腿角度大_下腿角度大": {
        "description": "足が体の重心よりかなり前で着地しており、ブレーキがかかりやすい走り方になっています。",
        "action": "ストライドを無理に広げるのではなく、今よりも『真下』に着地する意識を持ちましょう。",
        "drill": "その場でのもも上げや、ミニハードルを使ったドリルで、足を素早く引き上げる動きを練習しましょう。"
    },
    # ... 他の複合課題
    
    # フォールバック
    "フォーム全般": {
        "description": "ランニングフォーム全般に改善の余地があり、総合的なアプローチが必要です。",
        "action": "基本的な姿勢から見直し、リラックスした状態で効率的な動きを身につけましょう。",
        "drill": "ウォーキングドリル、基本的な体幹トレーニング、ゆっくりとしたジョギングから始めましょう。"
    }
}
```

**選択ロジック**:
1. 複合的な課題が存在するかチェック（例: `"右大腿角度大_左下腿角度大"`）
2. 存在しない場合、優先度順で単一課題を選択
3. それでも見つからない場合は `"フォーム全般"` を使用

**出力形式**:
```
--- 🏃‍♂️ ランニングフォーム改善アドバイス ---

【📊 現状のフォームについて】
{description}

【🎯 改善のためのアクション】
{action}

【💪 おすすめの補強ドリル】
{drill}

【💡 ワンポイントアドバイス】
改善は一度に全てを変えようとせず、一つずつ段階的に取り組むことが大切です。
```

##### ステップ3: Gemini AI詳細アドバイス生成（個別課題ごと）

```python
async def generate_detailed_advice_for_issue(
    issue: str, 
    main_finding: str = None,
    prompt_settings: Dict[str, Any] = None
) -> dict:
    """
    個別の課題に対してGemini AIを使って詳細なアドバイスを生成する
    
    各課題ごとにGemini APIを呼び出し、説明とエクササイズを生成
    """
```

**プロンプト生成**:

**A. カスタムプロンプトを使用する場合**:
```python
if prompt_settings and prompt_settings.get('use_custom_prompt', False):
    custom_template = prompt_settings.get('custom_prompt', '')
    prompt = custom_template.replace('{issue}', issue)
```

**B. デフォルトプロンプト（根本課題あり）**:
```python
prompt = f"""
あなたは専門コーチです。{main_finding}の原因である「{issue}」について、プレーンテキストのみで説明してください。

重要：装飾記号は一切使用禁止です。通常の文章のみで回答してください。

説明: {issue}が{main_finding}を引き起こす理由をエネルギー効率の観点から80文字程度で説明してください。

エクササイズ: {issue}を改善する具体的な練習方法を60文字程度で提案してください。

形式例：
説明: 下腿角度が大きいと接地時にブレーキがかかり、推進力が減少してエネルギー効率が悪化します。
エクササイズ: 壁ドリルで足の引き上げを練習し、重心の真下で着地する感覚を習得しましょう。

このような通常の文章形式で回答してください。ハッシュ、アスタリスク、ハイフンなどの記号は絶対に使わないでください。
"""
```

**Gemini API呼び出し**:

```python
# モデル設定（カスタム設定がある場合は適用）
current_model = model  # デフォルト: gemini-flash-latest
if prompt_settings:
    custom_config = genai.types.GenerationConfig(
        temperature=prompt_settings.get('temperature', 0.5),
        top_p=prompt_settings.get('top_p', 0.8),
        max_output_tokens=prompt_settings.get('max_output_tokens', 1000),
    )
    current_model = genai.GenerativeModel(
        'gemini-flash-latest',
        generation_config=custom_config,
        safety_settings=[...]  # すべてBLOCK_NONE
    )

# レート制限対応: 最大3回リトライ
max_retries = 3
for attempt in range(max_retries):
    try:
        response = current_model.generate_content(prompt)
        break
    except Exception as api_error:
        if "429" in str(api_error) or "quota" in str(api_error).lower():
            # レート制限 - 5秒, 10秒, 15秒の間隔でリトライ
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                await asyncio.sleep(wait_time)
                continue
        elif "500" in str(api_error):
            # 内部エラー - リトライ
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                await asyncio.sleep(wait_time)
                continue
        # その他のエラー - フォールバック
        response = None
        break
```

**レスポンス解析**:

```python
# マークダウン記法を徹底的に除去
cleaned_text = re.sub(r'#{1,6}\s*', '', advice_text)  # ヘッダー
cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_text)  # 太字
cleaned_text = re.sub(r'^\s*[-*+]\s+', '', cleaned_text, flags=re.MULTILINE)  # リスト
# ... その他の記号除去

# 段落ベースで解析
paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
explanation_lines = []
exercise_lines = []
current_section = "explanation"

for paragraph in paragraphs:
    if any(keyword in paragraph for keyword in ['エクササイズ', '練習', 'ドリル']):
        current_section = "exercise"
    elif any(keyword in paragraph for keyword in ['説明', '影響', '問題']):
        current_section = "explanation"
    
    if current_section == "exercise":
        exercise_lines.append(paragraph)
    else:
        explanation_lines.append(paragraph)

explanation = ' '.join(explanation_lines).strip()
exercise = ' '.join(exercise_lines).strip()
```

**フォールバック**:

Gemini APIが失敗した場合、`get_fallback_advice_for_issue()` 関数でデフォルトアドバイスを返します。

**出力形式**:
```python
{
    "issue": "右大腿角度大",
    "explanation": "右足の大腿部の角度が基準値から大きく偏差しています。オーバーストライドや不効率な着地パターンの原因となり、怪我のリスクが高まる可能性があります。",
    "exercise": "短い歩幅での高頻度ランニング練習（ピッチアップドリル）を実施し、足の回転を意識した走法を身につけてください。"
}
```

##### ステップ4: 統合アドバイスの組み立て

```python
async def generate_integrated_advice(
    issues_list: List[str],
    prompt_settings: Dict[str, Any] = None
) -> str:
    """
    プロコーチアドバイス（データベース）とGemini AI詳細アドバイスを統合する
    """
```

**統合テキストの構造**:
```
{プロコーチアドバイス（ステップ2の出力）}

【個別課題の詳細解説】

1. {issue_name}
   詳細: {explanation}
   推奨エクササイズ: {exercise}

2. {issue_name}
   詳細: {explanation}
   推奨エクササイズ: {exercise}

...

【総合的な改善のポイント】
改善は段階的に取り組むことが重要です。まずは全体的なフォーム意識から始めて、個別の課題に順次対処していくことで、より効果的なランニングフォームを身につけることができます。
```

**最終的なマークダウン除去**:
統合テキスト全体から、再度マークダウン記法を除去します（念のため）。

### 3.5 カスタムプロンプト機能

#### 3.5.1 設定方法

フロントエンド（`frontend/app/page.tsx`）で、ユーザーがカスタムプロンプトを設定できます：

```typescript
const promptSettings = {
  use_custom_prompt: true,
  custom_prompt: "あなたは専門コーチです。{issue}について...",
  temperature: 0.7,
  top_p: 0.8,
  max_output_tokens: 1000
}
```

#### 3.5.2 適用範囲

カスタムプロンプトは**個別課題の詳細アドバイス生成（ステップ3）**にのみ適用されます。

- ✅ 適用される: `generate_detailed_advice_for_issue()` 関数
- ❌ 適用されない: `generate_advanced_advice()` 関数（プロコーチアドバイス）

#### 3.5.3 プロンプトテンプレート

カスタムプロンプト内で `{issue}` をプレースホルダーとして使用できます：

```python
custom_template = prompt_settings.get('custom_prompt', '')
prompt = custom_template.replace('{issue}', issue)
```

### 3.6 エラーハンドリングとフォールバック

#### 3.6.1 Gemini APIエラー

| エラー種別 | 検出方法 | 対応 |
|-----------|---------|------|
| **レート制限（429）** | `"429" in error_str or "quota" in error_str.lower()` | 最大3回リトライ（5秒、10秒、15秒間隔） |
| **内部エラー（500）** | `"500" in error_str or "InternalServerError" in error_str` | 最大3回リトライ（5秒、10秒、15秒間隔） |
| **Safety Filter** | `candidate.finish_reason == 2` | デフォルトアドバイスを返す |
| **API Key無効** | `"API key not valid"` | デフォルトアドバイスを返す |
| **その他のエラー** | 上記以外 | デフォルトアドバイスを返す |

#### 3.6.2 フォールバック階層

1. **Gemini API成功** → AI生成アドバイスを使用
2. **Gemini API失敗（個別課題）** → `get_fallback_advice_for_issue()` を使用
3. **統合アドバイス生成全体が失敗** → プロコーチアドバイスのみを返す
4. **最終フォールバック** → 汎用的なアドバイスを返す

### 3.7 現在の課題と改善点 ⭐

#### 3.7.1 課題抽出の精度

**現状の問題**:
- Z値分析で検出された偏差を、単純に角度名に変換しているだけ
- イベント種別（接地/離地）の情報が失われる
- 複数の偏差を統合するロジックが不十分

**改善案**:
- イベント種別を考慮した課題名の生成（例: `"右足接地時のオーバーストライド"`）
- 複数の偏差を統合して、より包括的な課題を特定
- Z値の大きさに応じた優先度付け

#### 3.7.2 Gemini APIの応答品質

**現状の問題**:
- マークダウン記法が混入することがある（除去処理をしているが完璧ではない）
- プロンプトの指示に従わない場合がある（文字数制限など）
- レスポンスの構造が一貫していない

**改善案**:
- プロンプトエンジニアリングの改善（より明確な指示）
- レスポンス形式の統一（JSON形式を強制するなど）
- 後処理の改善（マークダウン除去の精度向上）

#### 3.7.3 パフォーマンス

**現状の問題**:
- 各課題ごとにGemini APIを呼び出すため、課題数が多いと時間がかかる
- レート制限に引っかかりやすい

**改善案**:
- 複数の課題を一度に処理するプロンプトに変更
- キャッシュ機能の追加（同じ課題に対するアドバイスをキャッシュ）
- バッチ処理の実装

#### 3.7.4 エラーハンドリング

**現状の問題**:
- エラーが発生した場合のユーザーへのフィードバックが不十分
- ログが散在している

**改善案**:
- エラー情報をフロントエンドに返す
- ログの集約と可視化
- リトライ戦略の改善

#### 3.7.5 プロコーチアドバイスデータベース

**現状の問題**:
- ハードコードされたデータベース（コード内に直接記述）
- 新しい課題に対応するにはコード修正が必要

**改善案**:
- データベース（PostgreSQL）に移行
- 管理画面の追加（コーチがアドバイスを編集できる）
- バージョン管理機能

---

## 4. データフロー

### 4.1 動画アップロードからアドバイス生成まで

```
1. ユーザーが動画をアップロード
   ↓
2. Frontend → API Gateway → Video Processing
   ↓
3. Video Processing がワークフローを制御:
   a. Pose Estimation を呼び出し（骨格検出）
   b. Feature Extraction を呼び出し（特徴量計算）
   c. Analysis (Z-Score) を呼び出し（統計分析）
   d. Advice Generation を呼び出し（アドバイス生成）⭐
   ↓
4. 統合レスポンスを返却
   ↓
5. Frontend が結果を表示
```

### 4.2 アドバイス生成の詳細フロー

```
Video Processing (main.py)
  ↓
Z値分析結果から課題抽出
  ├─ significant_deviations を取得
  ├─ 角度名を簡略化（"右大腿角度" → "右大腿角度大"）
  └─ high_level_issues リストを作成
  ↓
Advice Generation にリクエスト送信
  POST /generate-integrated
  {
    "video_id": "...",
    "issues_list": ["右大腿角度大", "左下腿角度大"],
    "prompt_settings": {...}  # オプション
  }
  ↓
Advice Generation (main.py)
  ├─ identify_main_finding() → "オーバーストライド"
  ├─ generate_advanced_advice() → プロコーチアドバイス
  ├─ generate_detailed_advice_for_issue() × N回
  │   ├─ Gemini API呼び出し（各課題ごと）
  │   ├─ レスポンス解析
  │   └─ マークダウン除去
  └─ generate_integrated_advice() → 統合テキスト生成
  ↓
Video Processing に統合アドバイスを返却
  {
    "status": "success",
    "integrated_advice": "--- 🏃‍♂️ ランニングフォーム改善アドバイス ---\n..."
  }
  ↓
Frontend が表示
```

---

## 5. 技術スタック

### 5.1 バックエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| **Python** | 3.9+ | メイン言語 |
| **FastAPI** | 0.104+ | Webフレームワーク |
| **MediaPipe** | 0.10+ | 骨格検出 |
| **NumPy** | 1.24+ | 数値計算 |
| **SciPy** | 1.11+ | 信号処理（ピーク検出） |
| **OpenCV** | 4.8+ | 動画処理 |
| **Google Gemini API** | - | AIアドバイス生成 ⭐ |
| **PostgreSQL** | 14+ | データベース（オプション） |

### 5.2 フロントエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| **Next.js** | 14+ | Reactフレームワーク |
| **TypeScript** | 5+ | 型安全性 |
| **Tailwind CSS** | 3+ | スタイリング |
| **Zustand** | 4+ | 状態管理 |
| **Lucide React** | - | アイコン |

### 5.3 インフラ

| 技術 | 用途 |
|------|------|
| **Docker** | コンテナ化 |
| **Docker Compose** | ローカル開発環境 |
| **Nginx** | API Gateway |
| **AWS EC2** | 本番環境（Amazon Linux 2023） |

---

## 6. 主要機能

### 6.1 動画解析機能

- **骨格検出**: MediaPipe Poseによる33個のランドマーク検出
- **特徴量計算**: 角度、メトリクス（ケイデンス、上下動など）
- **Z値統計分析**: 標準モデルとの偏差を統計的に評価

### 6.2 可視化機能

- **スティックピクチャー**: リアルタイムで骨格を可視化
- **角度グラフ**: 各角度の時系列グラフ
- **Z値ハイライト**: 問題部位を赤く太く表示（新機能）

### 6.3 アドバイス生成機能 ⭐

- **プロコーチアドバイス**: データベースから構造化されたアドバイス
- **AI詳細アドバイス**: Gemini AIによる個別最適化されたアドバイス
- **統合アドバイス**: 上記2つを統合した包括的なアドバイス
- **カスタムプロンプト**: ユーザーがプロンプトをカスタマイズ可能

### 6.4 動画生成機能（オプション）

- **改善動画生成**: OpenAI Sora-2 APIを使用して改善動画を生成
- **パスワード保護**: 動画生成にはパスワード認証が必要

---

## 7. 現在の課題と改善点

### 7.1 アドバイス生成に関する課題 ⭐

#### 課題1: 課題抽出の精度向上

**現状**: Z値分析結果を単純に角度名に変換しているだけ

**改善案**:
- イベント種別（接地/離地）を考慮した課題名の生成
- 複数の偏差を統合して、より包括的な課題を特定
- Z値の大きさに応じた優先度付け

#### 課題2: Gemini APIの応答品質向上

**現状**: マークダウン記法が混入することがある

**改善案**:
- プロンプトエンジニアリングの改善
- レスポンス形式の統一（JSON形式を強制）
- 後処理の改善

#### 課題3: パフォーマンス改善

**現状**: 各課題ごとにGemini APIを呼び出すため時間がかかる

**改善案**:
- 複数の課題を一度に処理するプロンプトに変更
- キャッシュ機能の追加
- バッチ処理の実装

#### 課題4: エラーハンドリングの改善

**現状**: エラーが発生した場合のユーザーへのフィードバックが不十分

**改善案**:
- エラー情報をフロントエンドに返す
- ログの集約と可視化
- リトライ戦略の改善

#### 課題5: プロコーチアドバイスデータベースの改善

**現状**: ハードコードされたデータベース

**改善案**:
- データベース（PostgreSQL）に移行
- 管理画面の追加
- バージョン管理機能

### 7.2 その他の課題

- **Z値分析のサイクル検出精度**: 動画条件によってはサイクルが検出されない
- **フロントエンドのパフォーマンス**: 大きなデータを扱う際の最適化が必要
- **デプロイメントの自動化**: 現在は手動デプロイ

---

## 📚 関連ドキュメント

- `ADVICE_NOT_DISPLAYING_TROUBLESHOOTING.md`: アドバイスが表示されない問題のトラブルシューティング
- `VIDEO_REQUIREMENTS_FOR_ZSCORE_ANALYSIS.md`: Z値分析のための動画要件
- `PROMINENCE_EXPLANATION.md`: 接地・離地検出パラメータの説明
- `SYSTEM_SPECIFICATION.md`: システム仕様書（詳細）

---

## 🎯 まとめ

このアプリケーションは、ランニング動画を解析して改善アドバイスを提供するシステムです。特に**アドバイス生成機能**は、プロコーチアドバイス（データベース）とGemini AI詳細アドバイスを統合して、ユーザーに個別最適化された改善提案を提供します。

**今後の改善の重点**:
1. 課題抽出の精度向上
2. Gemini APIの応答品質向上
3. パフォーマンス改善
4. エラーハンドリングの改善
5. プロコーチアドバイスデータベースの改善

これらの改善により、より高品質で信頼性の高いアドバイス生成が可能になります。

---

**作成者**: Cursor AI  
**最終更新**: 2025年1月26日

