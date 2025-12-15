# ルールベース診断 + Gemini生成 アドバイス機能

## 概要

新しいアドバイス生成方式として、「ルールベース診断 + Gemini生成」のハイブリッド方式を実装しました。

### 従来の方式との違い

| 項目 | 従来の方式 | 新しい方式（ルールベース） |
|------|-----------|------------------------|
| **診断方法** | Gemini AIに課題リストを渡して生成 | Z値データからルールベースで診断 |
| **専門家の知見** | データベースに保存されたアドバイス | マスタデータに定義されたルール |
| **Geminiの役割** | 課題から直接アドバイスを生成 | 診断結果を基に文章を生成 |
| **一貫性** | 生成内容が変動しやすい | ルールに基づく一貫した診断 |

## アーキテクチャ

```
Z値データ
  ↓
ルールベース診断エンジン (expert_engine.py)
  ├─ マスタデータと照合
  ├─ 閾値判定（Z値 < -2.0 または > 2.0）
  └─ 診断結果を生成
  ↓
Gemini API
  ├─ 診断結果をコンテキストとして受け取る
  ├─ 専門家の見解を基に文章を生成
  └─ JSON形式で返却
  ↓
統合アドバイス
```

## ファイル構成

- `expert_engine.py`: ルールベース診断エンジンとGemini連携機能
- `main.py`: FastAPIエンドポイント（`/generate-rule-based`）

## マスタデータ構造

`expert_engine.py` の `ADVICE_MASTER_DATA` に定義されています。

```python
{
    "ISSUE_TRUNK_BACKWARD": {
        "rule": {
            "target_event": "right_strike",  # イベント種別
            "target_metric": "体幹角度",      # 角度名
            "operator": "lt",                # 演算子（lt: より小さい, gt: より大きい）
            "threshold": -2.0,               # 閾値
            "severity": "high"               # 重要度
        },
        "content": {
            "name": "腰落ち（後傾）フォーム",
            "observation": "現象の説明",
            "cause": "原因の説明",
            "action": "改善策",
            "drill": {
                "name": "ドリル名",
                "url": "YouTube URL"
            }
        }
    }
}
```

## APIエンドポイント

### POST `/generate-rule-based`

ルールベース診断 + Gemini生成でアドバイスを生成します。

#### リクエスト

```json
{
    "video_id": "unique_video_id",
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
    },
    "prompt_settings": {}  # オプション
}
```

#### レスポンス

```json
{
    "status": "success",
    "message": "ルールベース診断 + Gemini生成アドバイスを生成しました",
    "video_id": "unique_video_id",
    "ai_advice": {
        "title": "フォーム改善アドバイス",
        "message": "メインメッセージ（300文字程度）",
        "key_points": ["ポイント1", "ポイント2"]
    },
    "raw_issues": [
        {
            "name": "腰落ち（後傾）フォーム",
            "drill": {
                "name": "ウォールドリル（壁押し）",
                "url": "https://youtube.com/example_wall_drill"
            },
            "severity": "high",
            "event": "right_strike",
            "angle": "体幹角度"
        }
    ]
}
```

## 使用方法

### 1. video_processingサービスからの呼び出し

`video_processing/app/main.py` で、Z値分析結果を取得した後、新しいエンドポイントを呼び出します：

```python
# Z値分析結果からZ値データを抽出
z_scores = z_score_data.get("z_scores", {})

# ルールベースアドバイス生成
rule_based_request = {
    "video_id": unique_id,
    "z_scores": z_scores
}

rule_based_response = await client.post(
    "http://advice_generation:8005/generate-rule-based",
    json=rule_based_request,
    timeout=180.0
)
```

### 2. 既存のエンドポイントとの併用

既存の `/generate-integrated` エンドポイントは引き続き使用可能です。新しい方式を試す場合は `/generate-rule-based` を使用してください。

## マスタデータの拡張

新しい課題を追加する場合は、`expert_engine.py` の `ADVICE_MASTER_DATA` に追加します。

### 例: 新しい課題の追加

```python
"ISSUE_NEW_PROBLEM": {
    "rule": {
        "target_event": "right_strike",
        "target_metric": "右大腿角度",
        "operator": "gt",
        "threshold": 2.5,
        "severity": "high"
    },
    "content": {
        "name": "新しい課題名",
        "observation": "現象の説明",
        "cause": "原因の説明",
        "action": "改善策",
        "drill": {
            "name": "ドリル名",
            "url": "YouTube URL"
        }
    }
}
```

## トラブルシューティング

### 1. インポートエラー

```
ModuleNotFoundError: No module named 'expert_engine'
```

**解決策**: `main.py` のインポート部分で、相対インポートと絶対インポートの両方を試行するようにしています。それでもエラーが発生する場合は、Dockerコンテナを再起動してください。

### 2. Gemini APIエラー

Gemini APIが失敗した場合、フォールバックとして基本的なアドバイスを返します。

### 3. Z値データが空

Z値データが空の場合、`"良好なフォームです"` というメッセージを返します。

## 今後の改善点

1. **マスタデータの外部化**: データベースや設定ファイルに移行
2. **ルールの柔軟性向上**: 複合条件（AND/OR）のサポート
3. **左右の自動判定**: 左右両方の角度を自動的にチェック
4. **診断結果の可視化**: どのルールが適用されたかを明確に表示

## 関連ドキュメント

- `GEMINI_APP_OVERVIEW.md`: アプリ全体の概要とアドバイス生成機能の説明
- `ADVICE_NOT_DISPLAYING_TROUBLESHOOTING.md`: アドバイスが表示されない問題のトラブルシューティング



