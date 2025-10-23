# ランニング動画自動解析エキスパートシステム - システム仕様書

**バージョン**: 3.0.0  
**最終更新日**: 2025年10月20日  
**プロジェクト名**: Running Analysis System

---

## 📋 目次

1. [システム概要](#1-システム概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [技術スタック](#3-技術スタック)
4. [主要機能](#4-主要機能)
5. [データフロー](#5-データフロー)
6. [APIエンドポイント仕様](#6-apiエンドポイント仕様)
7. [データベース設計](#7-データベース設計)
8. [AI・機械学習モデル](#8-ai機械学習モデル)
9. [フロントエンド仕様](#9-フロントエンド仕様)
10. [デプロイメント構成](#10-デプロイメント構成)
11. [セキュリティ](#11-セキュリティ)
12. [パフォーマンス](#12-パフォーマンス)
13. [開発環境](#13-開発環境)
14. [運用・保守](#14-運用保守)

---

## 1. システム概要

### 1.1 プロジェクト概要

**ランニング動画自動解析エキスパートシステム**は、ランニング動画をアップロードするだけで、AIが自動的にフォームを解析し、詳細な評価と改善アドバイスを提供する次世代型Webアプリケーションです。

### 1.2 目的

- ランナーのパフォーマンス向上を支援
- 怪我リスクを事前に検知し予防
- 専門コーチの知見をAIで民主化
- データに基づく科学的なフォーム改善

### 1.3 主要ターゲットユーザー

- アマチュアランナー
- 陸上競技選手
- ランニングコーチ
- スポーツトレーナー
- フィットネス施設

### 1.4 システムの特徴

| 特徴 | 説明 |
|------|------|
| **AI骨格検出** | MediaPipe Poseによる33個のランドマークを高精度検出 |
| **Z値統計分析** | 標準モデルとの偏差を統計的に評価 |
| **マイクロサービス** | 6つの独立したサービスで構成 |
| **リアルタイム解析** | 平均30-60秒で解析完了 |
| **カスタムアドバイス** | Gemini AIによる個別最適化されたアドバイス |

---

## 2. システムアーキテクチャ

### 2.1 全体アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                         クライアント                          │
│                    (Next.js Frontend)                        │
│                      Port: 3000                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                        (Nginx)                               │
│                       Port: 80                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│Video          │  │Pose           │  │Feature        │
│Processing     │  │Estimation     │  │Extraction     │
│Port: 8001     │  │Port: 8002     │  │Port: 8003     │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│Analysis       │  │Advice         │  │Video          │
│(Z-Score)      │  │Generation     │  │Generation     │
│Port: 8004     │  │Port: 8005     │  │Port: 8006     │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    PostgreSQL RDS       │
              │  (AWS ap-southeast-2)   │
              └─────────────────────────┘
```

### 2.2 マイクロサービス構成

| サービス名 | ポート | 役割 | 主要技術 |
|-----------|-------|------|---------|
| **Frontend** | 3000 | UIとユーザー操作 | Next.js 14, TypeScript |
| **API Gateway** | 80 | リクエストルーティング | Nginx |
| **Video Processing** | 8001 | 動画アップロード・前処理 | FastAPI, OpenCV |
| **Pose Estimation** | 8002 | 骨格キーポイント検出 | FastAPI, MediaPipe |
| **Feature Extraction** | 8003 | 特徴量計算 | FastAPI, NumPy, SciPy |
| **Analysis** | 8004 | Z値統計分析 | FastAPI, NumPy |
| **Advice Generation** | 8005 | AIアドバイス生成 | FastAPI, Gemini AI |
| **Video Generation** | 8006 | 解析動画生成（オプション） | FastAPI, OpenCV |

### 2.3 データストレージ

```
┌─────────────────────────────────────────────────────┐
│                  Data Storage                        │
├─────────────────────────────────────────────────────┤
│  • PostgreSQL (RDS): メタデータ、解析結果           │
│  • Docker Volume: アップロード動画ファイル           │
│  • Docker Volume: AIモデルキャッシュ                 │
│  • LocalStorage: クライアント側一時データ            │
└─────────────────────────────────────────────────────┘
```

---

## 3. 技術スタック

### 3.1 フロントエンド

| 技術 | バージョン | 用途 |
|------|----------|------|
| **Next.js** | 14.x | React フレームワーク |
| **TypeScript** | 5.x | 型安全な開発 |
| **Tailwind CSS** | 3.x | スタイリング |
| **Zustand** | - | 状態管理 |
| **Recharts** | - | データ可視化 |

### 3.2 バックエンド

| 技術 | バージョン | 用途 |
|------|----------|------|
| **Python** | 3.11+ | バックエンド言語 |
| **FastAPI** | 0.104+ | RESTful API フレームワーク |
| **Uvicorn** | - | ASGIサーバー |
| **Pydantic** | 2.x | データバリデーション |

### 3.3 AI・機械学習

| 技術 | バージョン | 用途 |
|------|----------|------|
| **MediaPipe** | 0.10.7+ | 骨格検出 |
| **OpenCV** | 4.8+ | 画像処理 |
| **NumPy** | 1.24+ | 数値計算 |
| **SciPy** | 1.11+ | 科学計算 |
| **Google Gemini AI** | - | アドバイス生成 |

### 3.4 インフラ

| 技術 | バージョン | 用途 |
|------|----------|------|
| **Docker** | 24.x | コンテナ化 |
| **Docker Compose** | 2.x | マルチコンテナ管理 |
| **Nginx** | latest | リバースプロキシ |
| **PostgreSQL** | 17.4 | データベース |
| **AWS RDS** | - | マネージドDB |
| **AWS EC2** | - | ホスティング |

---

## 4. 主要機能

### 4.1 動画アップロード機能

**機能概要**
- ドラッグ&ドロップによるファイルアップロード
- 対応形式: MP4, AVI, MOV, MKV, WMV
- 最大ファイルサイズ: 500MB
- ユーザー選択機能（14種類のユーザープロファイル）

**技術仕様**
```typescript
// アップロードリクエスト
POST /api/video/upload
Content-Type: multipart/form-data

FormData:
  - file: File (動画ファイル)
  - user_id: string (ユーザーID)
  - prompt_settings: JSON string (オプション)
```

### 4.2 骨格検出機能

**機能概要**
- MediaPipe Poseによる33個のランドマーク検出
- フレーム単位での骨格追跡
- 信頼度スコアの計算

**検出ランドマーク一覧**

| ID | 名称 | 説明 |
|----|------|------|
| 0 | nose | 鼻 |
| 11-12 | shoulders | 左右肩 |
| 13-14 | elbows | 左右肘 |
| 23-24 | hips | 左右腰 |
| 25-26 | knees | 左右膝 |
| 27-28 | ankles | 左右足首 |
| 29-30 | heels | 左右かかと |
| 31-32 | foot_index | 左右足指 |

**出力データ構造**
```json
{
  "frame_number": 0,
  "timestamp": 0.0,
  "keypoints": [
    {
      "x": 0.5,
      "y": 0.3,
      "z": -0.1,
      "visibility": 0.95
    }
  ],
  "landmarks_detected": true,
  "confidence_score": 0.92
}
```

### 4.3 特徴量計算機能

**機能概要**
- 5つの主要角度を計算
  - 体幹角度（垂直線との角度）
  - 左右大腿角度
  - 左右下腿角度
- ランニングメトリクス計算
  - ケイデンス（歩数/分）
  - 上下動（Vertical Oscillation）

**角度計算仕様**

```python
# 体幹角度（垂直線との角度）
trunk_angle = atan2(
    shoulder_center.x - hip_center.x,
    shoulder_center.y - hip_center.y
) * 180 / π

# 大腿角度（垂直線との角度）
thigh_angle = atan2(
    hip.x - knee.x,
    hip.y - knee.y
) * 180 / π

# 下腿角度（垂直線との角度）
lower_leg_angle = atan2(
    knee.x - ankle.x,
    knee.y - ankle.y
) * 180 / π
```

### 4.4 足接地・離地検出機能

**機能概要**
- 足首のY座標変化から接地・離地タイミングを自動検出
- 4種類のイベントを検出
  - 右足接地 (right_strike)
  - 右足離地 (right_off)
  - 左足接地 (left_strike)
  - 左足離地 (left_off)

**検出アルゴリズム**
1. ガウシアンフィルタによる平滑化
2. scipy.signal.find_peaksによる極値検出
3. 接地 = 足首Y座標の極小値
4. 離地 = 足首Y座標の極大値

### 4.5 Z値統計分析機能

**機能概要**
- イベント別に角度を標準モデルと比較
- Z値（標準偏差）を計算して偏差を評価
- 有意な偏差を自動検出

**標準モデルデータ**

| イベント | 角度 | 平均 (μ) | 標準偏差 (σ) |
|---------|------|---------|------------|
| right_strike | 体幹角度 | 3.96° | 3.36° |
| right_strike | 右大腿角度 | -14.60° | 12.62° |
| left_off | 体幹角度 | 4.36° | 3.17° |
| ... | ... | ... | ... |

**Z値計算式**
```
Z = (観測値 - 標準平均) / 標準偏差
```

**評価基準**

| Z値範囲 | 評価 | 重要度 |
|--------|------|--------|
| \|Z\| < 2.0 | 正常範囲 | 低 |
| 2.0 ≤ \|Z\| < 3.0 | 注意 | 中 |
| \|Z\| ≥ 3.0 | 要改善 | 高 |

### 4.6 AIアドバイス生成機能

**機能概要**
- Google Gemini AIを使用したパーソナライズされたアドバイス生成
- 統合アドバイスと個別課題解説の2段階生成
- カスタムプロンプト設定対応

**アドバイス生成フロー**
1. Z値分析から有意な偏差を抽出
2. 課題リストの作成（例: 体幹前傾、左下腿角度大）
3. Gemini AIへのリクエスト送信
4. Markdown形式のアドバイス受信
5. フロントエンドでの表示

**プロンプト設定パラメータ**
```json
{
  "custom_prompt": "カスタムプロンプトテキスト",
  "use_custom_prompt": true,
  "temperature": 0.5,
  "top_p": 0.8,
  "max_output_tokens": 1000
}
```

### 4.7 解析動画生成機能（オプション）

**機能概要**
- 骨格スケルトンをオーバーレイした解析動画の生成
- 角度・イベントのビジュアル表示
- パスワード保護

---

## 5. データフロー

### 5.1 解析パイプライン全体フロー

```
┌──────────────────────────────────────────────────────────┐
│ 1. 動画アップロード (Frontend)                            │
│    - ユーザーが動画を選択                                  │
│    - FormDataでPOSTリクエスト送信                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. 動画受信・保存 (Video Processing Service)             │
│    - ファイル検証（形式、サイズ）                          │
│    - UUIDベースのファイル名生成                            │
│    - uploads/ ディレクトリに保存                          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. 骨格検出 (Pose Estimation Service)                    │
│    - MediaPipe Poseで全フレームを処理                    │
│    - 33個のランドマーク × 全フレーム検出                 │
│    - 信頼度スコア計算                                      │
│    出力: pose_data (キーポイント配列)                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. 特徴量計算 (Feature Extraction Service)               │
│    - 5つの角度を全フレームで計算                          │
│      - 体幹角度、左右大腿角度、左右下腿角度                │
│    - ランニングメトリクス計算                             │
│      - ケイデンス、上下動                                  │
│    出力: angle_data, running_metrics                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 5. Z値分析 (Analysis Service)                            │
│    - 足接地・離地イベント検出                              │
│    - 各イベント時の角度を抽出                              │
│    - 標準モデルとの偏差をZ値計算                          │
│    - 有意な偏差を検出（|Z| ≥ 2.0）                       │
│    出力: z_scores, significant_deviations                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 6. アドバイス生成 (Advice Generation Service)            │
│    - 課題リストを作成                                      │
│    - Gemini AIに統合アドバイスをリクエスト                │
│    - カスタムプロンプト適用（オプション）                  │
│    出力: integrated_advice (Markdown形式)                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 7. データベース保存 (オプション)                          │
│    - runs テーブル: 走行記録                              │
│    - keypoints テーブル: 骨格データ                       │
│    - frame_angles テーブル: 角度時系列                    │
│    - events テーブル: 接地・離地イベント                  │
│    - analysis_results テーブル: Z値                      │
│    - integrated_advice テーブル: アドバイス              │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 8. 結果返却 (Video Processing Service)                   │
│    - 全サービスの結果を統合                                │
│    - JSONレスポンスを生成                                  │
│    - フロントエンドに返却                                  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 9. 結果表示 (Frontend)                                    │
│    - LocalStorageに軽量データを保存                       │
│    - Zustandに骨格データを保存                            │
│    - 結果ページへリダイレクト                              │
│    - グラフとアドバイスを表示                              │
└──────────────────────────────────────────────────────────┘
```

### 5.2 処理時間の内訳（目安）

| ステップ | 処理時間（10秒動画） | 主な処理内容 |
|---------|------------------|-------------|
| 動画アップロード | 2-5秒 | ネットワーク転送 |
| 骨格検出 | 15-30秒 | MediaPipe処理 |
| 特徴量計算 | 1-3秒 | 角度計算 |
| Z値分析 | 2-5秒 | 統計計算 |
| アドバイス生成 | 5-15秒 | Gemini API |
| DB保存 | 2-5秒 | データベース書き込み |
| **合計** | **30-60秒** | |

---

## 6. APIエンドポイント仕様

### 6.1 Video Processing Service (Port 8001)

#### POST /upload
動画ファイルをアップロードして全解析パイプラインを実行

**リクエスト**
```
POST /upload
Content-Type: multipart/form-data

FormData:
  file: File (動画ファイル)
  user_id: string (default: "default_user")
  prompt_settings: JSON string (オプション)
```

**レスポンス**
```json
{
  "status": "success",
  "message": "動画アップロード、骨格解析、特徴量計算、課題分析が完了しました",
  "upload_info": {
    "file_id": "uuid",
    "original_filename": "前傾.mov",
    "file_size": 12345678,
    "upload_timestamp": "2025-10-20T10:00:00"
  },
  "pose_analysis": {
    "status": "success",
    "video_info": {
      "fps": 30.0,
      "total_frames": 300,
      "duration_seconds": 10.0
    },
    "pose_data": [ /* 骨格データ配列 */ ],
    "summary": {
      "total_processed_frames": 300,
      "detected_pose_frames": 295,
      "detection_rate": 0.983
    }
  },
  "feature_analysis": {
    "features": {
      "angle_statistics": { /* 角度統計 */ },
      "running_metrics": {
        "cadence": 180,
        "vertical_oscillation": 8.5
      }
    }
  },
  "z_score_analysis": {
    "z_scores": {
      "right_strike": {
        "体幹角度": 2.5,
        "右大腿角度": -1.2
      }
    },
    "analysis_summary": {
      "significant_deviations": [
        {
          "event": "right_strike",
          "angle": "体幹角度",
          "z_score": 2.5,
          "severity": "medium"
        }
      ]
    }
  },
  "advice_results": {
    "status": "success",
    "integrated_advice": "# ランニングフォーム改善アドバイス\n...",
    "high_level_issues": ["体幹前傾", "左下腿角度大"]
  },
  "run_id": 123
}
```

#### GET /stream/{filename}
保存された動画ファイルをストリーミング配信

**リクエスト**
```
GET /stream/{filename}
```

**レスポンス**
```
Content-Type: video/mp4
Body: Video Stream
```

#### GET /result/{video_id}
指定されたvideo_idの解析結果を取得（再解析を実行）

### 6.2 Pose Estimation Service (Port 8002)

#### POST /estimate
動画から骨格キーポイントを検出

**リクエスト**
```json
{
  "video_path": "uploads/filename.mp4",
  "confidence_threshold": 0.5
}
```

**レスポンス**
```json
{
  "status": "success",
  "message": "骨格検出が完了しました。295/300フレームで姿勢を検出",
  "video_info": {
    "fps": 30.0,
    "total_frames": 300,
    "duration_seconds": 10.0,
    "width": 1920,
    "height": 1080
  },
  "pose_data": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "keypoints": [
        {"x": 0.5, "y": 0.3, "z": -0.1, "visibility": 0.95}
      ],
      "landmarks_detected": true,
      "confidence_score": 0.92
    }
  ],
  "summary": {
    "total_processed_frames": 300,
    "detected_pose_frames": 295,
    "detection_rate": 0.983,
    "average_confidence": 0.92,
    "mediapipe_landmarks_count": 33
  }
}
```

### 6.3 Feature Extraction Service (Port 8003)

#### POST /extract
骨格データから特徴量を計算

**リクエスト**
```json
{
  "pose_data": [ /* 骨格データ配列 */ ],
  "video_info": {
    "fps": 30.0,
    "duration": 10.0,
    "total_frames": 300
  }
}
```

**レスポンス**
```json
{
  "status": "success",
  "message": "特徴量抽出が完了しました",
  "features": {
    "angle_statistics": {
      "trunk_angle": {
        "mean": 5.2,
        "std": 2.1,
        "max": 10.5,
        "min": 0.8
      }
    },
    "angle_data": [
      {
        "frame_number": 0,
        "trunk_angle": 5.2,
        "left_thigh_angle": -15.3,
        "right_thigh_angle": -12.8
      }
    ],
    "running_metrics": {
      "cadence": 180,
      "vertical_oscillation": 8.5
    }
  }
}
```

### 6.4 Analysis Service (Port 8004)

#### POST /analyze-z-score
Z値統計分析を実行

**リクエスト**
```json
{
  "keypoints_data": [ /* 骨格データ配列 */ ],
  "video_fps": 30.0
}
```

**レスポンス**
```json
{
  "status": "success",
  "message": "Z値分析が完了しました",
  "z_scores": {
    "right_strike": {
      "体幹角度": 2.5,
      "右大腿角度": -1.2,
      "右下腿角度": 0.8
    }
  },
  "event_angles": {
    "right_strike": {
      "体幹角度": 12.5,
      "右大腿角度": -25.3
    }
  },
  "events_detected": [
    {
      "frame_number": 15,
      "foot_side": "right",
      "event_type": "strike"
    }
  ],
  "analysis_summary": {
    "total_events": 20,
    "significant_deviations": [
      {
        "event": "right_strike",
        "angle": "体幹角度",
        "z_score": 2.5,
        "severity": "medium",
        "description": "標準から中程度の偏差"
      }
    ]
  }
}
```

### 6.5 Advice Generation Service (Port 8005)

#### POST /generate-integrated
統合アドバイスを生成

**リクエスト**
```json
{
  "video_id": "uuid",
  "issues_list": ["体幹前傾", "左下腿角度大"],
  "prompt_settings": {
    "custom_prompt": "カスタムプロンプト",
    "use_custom_prompt": true,
    "temperature": 0.5,
    "top_p": 0.8,
    "max_output_tokens": 1000
  }
}
```

**レスポンス**
```json
{
  "status": "success",
  "video_id": "uuid",
  "integrated_advice": "# ランニングフォーム総合アドバイス\n\n## 検出された課題\n..."
}
```

### 6.6 Video Generation Service (Port 8006)

#### POST /generate
解析動画を生成（パスワード保護）

**リクエスト**
```json
{
  "video_id": "uuid",
  "password": "admin123"
}
```

---

## 7. データベース設計

### 7.1 データベース情報

| 項目 | 値 |
|------|-----|
| **DBMS** | PostgreSQL 17.4 |
| **ホスト** | AWS RDS (ap-southeast-2) |
| **エンドポイント** | running-analysis-db-single.cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com |
| **データベース名** | postgres |
| **文字エンコーディング** | UTF-8 |

### 7.2 テーブル設計

#### 7.2.1 users テーブル

ユーザー情報を管理

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| user_id | VARCHAR(255) | PRIMARY KEY | ユーザーID |
| username | VARCHAR(255) | NOT NULL | ユーザー名 |
| email | VARCHAR(255) | UNIQUE | メールアドレス |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新日時 |

#### 7.2.2 runs テーブル

走行記録を管理

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | 走行ID |
| user_id | VARCHAR(255) | FOREIGN KEY | ユーザーID |
| video_id | VARCHAR(255) | UNIQUE, NOT NULL | 動画UUID |
| video_path | TEXT | | 動画パス |
| original_filename | VARCHAR(255) | | 元のファイル名 |
| video_fps | DOUBLE PRECISION | | フレームレート |
| video_duration | DOUBLE PRECISION | | 動画長（秒） |
| total_frames | INTEGER | | 総フレーム数 |
| analysis_status | VARCHAR(50) | DEFAULT 'processing' | ステータス |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新日時 |

**analysis_status 値**
- `processing`: 処理中
- `completed`: 完了
- `failed`: 失敗

#### 7.2.3 keypoints テーブル

骨格キーポイントデータを格納（33ランドマーク × 全フレーム）

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | レコードID |
| run_id | INTEGER | FOREIGN KEY | 走行ID |
| frame_number | INTEGER | NOT NULL | フレーム番号 |
| landmark_id | INTEGER | NOT NULL | ランドマークID (0-32) |
| landmark_name | VARCHAR(50) | | ランドマーク名 |
| x_coordinate | DOUBLE PRECISION | | X座標 (0.0-1.0) |
| y_coordinate | DOUBLE PRECISION | | Y座標 (0.0-1.0) |
| z_coordinate | DOUBLE PRECISION | | Z座標（深度） |
| visibility | DOUBLE PRECISION | | 可視性 (0.0-1.0) |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |

**複合ユニーク制約**: `(run_id, frame_number, landmark_id)`

**データ量見積もり**
- 10秒動画（300フレーム）: 約9,900レコード（33 × 300）
- 1レコード: 約100 bytes
- 合計: 約1MB

#### 7.2.4 frame_angles テーブル

フレームごとの角度時系列データを格納

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | レコードID |
| run_id | INTEGER | FOREIGN KEY | 走行ID |
| frame_number | INTEGER | NOT NULL | フレーム番号 |
| trunk_angle | DOUBLE PRECISION | | 体幹角度 |
| left_thigh_angle | DOUBLE PRECISION | | 左大腿角度 |
| right_thigh_angle | DOUBLE PRECISION | | 右大腿角度 |
| left_lower_leg_angle | DOUBLE PRECISION | | 左下腿角度 |
| right_lower_leg_angle | DOUBLE PRECISION | | 右下腿角度 |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |

**複合ユニーク制約**: `(run_id, frame_number)`

#### 7.2.5 events テーブル

足接地・離地イベントを格納

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | レコードID |
| run_id | INTEGER | FOREIGN KEY | 走行ID |
| frame_number | INTEGER | NOT NULL | フレーム番号 |
| foot_side | VARCHAR(10) | NOT NULL | 足の左右 |
| event_type | VARCHAR(20) | NOT NULL | イベント種類 |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |

**event_type 値**
- `left_strike`: 左足接地
- `left_off`: 左足離地
- `right_strike`: 右足接地
- `right_off`: 右足離地

**データ量見積もり**
- 10秒動画: 約20イベント

#### 7.2.6 analysis_results テーブル

Z値分析結果を格納

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | レコードID |
| run_id | INTEGER | FOREIGN KEY | 走行ID |
| metric_name | VARCHAR(255) | NOT NULL | 指標名 |
| value | DOUBLE PRECISION | NOT NULL | 計算値 |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |

**metric_name 命名規則**
- `Z値_{イベント種類}_{角度名}`
  - 例: `Z値_right_strike_体幹角度`
- `角度_{イベント種類}_{角度名}`
  - 例: `角度_right_strike_体幹角度`

**データ量見積もり**
- 1回の解析: 約40レコード（Z値20個 + 角度20個）

#### 7.2.7 integrated_advice テーブル

統合アドバイスを格納

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | SERIAL | PRIMARY KEY | レコードID |
| run_id | INTEGER | FOREIGN KEY | 走行ID |
| advice_text | TEXT | NOT NULL | アドバイス本文 |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |

### 7.3 ER図

```
users
  │
  └──< runs (1:N)
        │
        ├──< keypoints (1:N)
        ├──< frame_angles (1:N)
        ├──< events (1:N)
        ├──< analysis_results (1:N)
        └──< integrated_advice (1:1)
```

### 7.4 インデックス戦略

```sql
-- 既存の主キーとユニーク制約によるインデックス
-- 追加推奨インデックス（パフォーマンス最適化用）

CREATE INDEX idx_runs_user_id ON runs(user_id);
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX idx_keypoints_run_id ON keypoints(run_id);
CREATE INDEX idx_keypoints_frame_number ON keypoints(run_id, frame_number);
CREATE INDEX idx_frame_angles_run_id ON frame_angles(run_id);
CREATE INDEX idx_analysis_results_run_id ON analysis_results(run_id);
CREATE INDEX idx_events_run_id ON events(run_id);
```

---

## 8. AI・機械学習モデル

### 8.1 MediaPipe Pose

**概要**
- Googleが開発したオープンソースの姿勢推定モデル
- 33個の3D体ランドマークを検出
- リアルタイム性能に優れる

**モデル設定**
```python
mp_pose.Pose(
    static_image_mode=False,      # 動画モード
    model_complexity=1,            # モデル複雑度（0-2）
    enable_segmentation=False,     # セグメンテーション無効
    min_detection_confidence=0.5,  # 検出信頼度閾値
    min_tracking_confidence=0.5    # トラッキング信頼度閾値
)
```

**出力データ**
- x, y座標: 0.0-1.0の正規化値
- z座標: 深度情報（相対値）
- visibility: 可視性スコア（0.0-1.0）

### 8.2 Google Gemini AI

**概要**
- Googleの最新生成AIモデル
- 自然言語でのアドバイス生成に使用
- Markdown形式での構造化出力

**モデル設定**
```python
model = genai.GenerativeModel('gemini-pro')

generation_config = genai.types.GenerationConfig(
    temperature=0.5,          # 創造性（0.0-1.0）
    top_p=0.8,                # 多様性（0.0-1.0）
    max_output_tokens=1000,   # 最大出力トークン数
)
```

**プロンプト構造**
```
あなたは専門ランニングコーチです。
以下のフォーム課題に基づいて、総合的な改善アドバイスを提供してください。

検出された課題:
- 体幹前傾
- 左下腿角度大

アドバイスの構成:
1. 総合評価
2. 優先課題
3. 具体的な改善方法
4. エクササイズプラン
```

### 8.3 標準モデル（Z値分析用）

**概要**
- 理想的なランニングフォームの統計データ
- 4つのイベント × 5つの角度 = 20パターンの平均・標準偏差

**データソース**
- エリートランナーのフォームデータ
- 国内外のスポーツ科学研究
- 専門コーチの知見

**更新頻度**
- 定期的に新しいデータで更新予定

---

## 9. フロントエンド仕様

### 9.1 技術構成

| 技術 | 用途 |
|------|------|
| **Next.js 14 (App Router)** | フレームワーク |
| **TypeScript** | 型安全性 |
| **Tailwind CSS** | スタイリング |
| **Zustand** | 大容量データ管理 |
| **Recharts** | グラフ描画 |
| **React Markdown** | Markdown表示 |

### 9.2 ページ構成

```
/
├─ page.tsx                  # トップページ（動画アップロード）
├─ result/[id]/page.tsx     # 解析結果表示ページ
└─ test-z-score/page.tsx    # Z値テストページ（開発用）
```

### 9.3 主要コンポーネント

#### 9.3.1 動画アップロードコンポーネント

**機能**
- ドラッグ&ドロップ対応
- ファイル形式検証
- アップロード進捗表示
- ユーザー選択
- プロンプト設定

**実装ファイル**: `frontend/app/page.tsx`

#### 9.3.2 結果表示コンポーネント

**機能**
- 動画プレーヤー
- 角度時系列グラフ
- Z値分析結果表示
- AIアドバイス表示（Markdown対応）
- イベント一覧表示

**実装ファイル**: `frontend/app/result/[id]/page.tsx`

### 9.4 状態管理（Zustand）

**ストア構造**
```typescript
interface ResultStore {
  poseData: any[];           // 骨格データ（大容量）
  videoInfo: VideoInfo | null;
  uploadInfo: UploadInfo | null;
  
  setPoseData: (data: any[]) => void;
  setVideoInfo: (info: VideoInfo) => void;
  setUploadInfo: (info: UploadInfo) => void;
  clearData: () => void;
}
```

**使用理由**
- 骨格データ（10秒動画で約1-2MB）をlocalStorageに保存すると容量超過
- Zustandでメモリ上に保持

### 9.5 データ永続化戦略

```
┌─────────────────────────────────────────────┐
│          データ永続化戦略                     │
├─────────────────────────────────────────────┤
│  • 骨格データ (pose_data)                    │
│    → Zustandストア（メモリ上）                │
│                                              │
│  • 軽量データ                                 │
│    - 解析結果 (z_score_analysis)            │
│    - アドバイス (advice_results)             │
│    - 角度統計 (angle_statistics)             │
│    → localStorage                           │
│                                              │
│  • 動画ファイル                               │
│    → サーバー（Docker Volume）                │
└─────────────────────────────────────────────┘
```

### 9.6 UIデザイン

**デザインコンセプト**
- Spire（オンライン会議ツール）風のモダンなデザイン
- グラデーションボタン（青〜藍色）
- シャドウとボーダーで奥行き表現
- レスポンシブ対応

**カラーパレット**
```css
Primary: #2563EB (青)
Secondary: #4F46E5 (藍)
Success: #10B981 (緑)
Warning: #F59E0B (オレンジ)
Danger: #EF4444 (赤)
Gray: #6B7280 (グレー)
```

---

## 10. デプロイメント構成

### 10.1 ローカル開発環境

**起動方法**
```bash
docker-compose up -d
```

**アクセスURL**
- フロントエンド: http://localhost:3000
- API Gateway: http://localhost:80
- 各サービス: http://localhost:8001-8006

**環境変数**
```bash
# .env ファイル
ENABLE_DB_SAVE=false              # ローカルではDB保存無効
OPENAI_API_KEY=your_api_key       # Gemini API キー
VIDEO_GENERATION_PASSWORD=admin123
```

### 10.2 本番環境（AWS EC2）

**インフラ構成**
```
┌─────────────────────────────────────────────┐
│              AWS インフラ                     │
├─────────────────────────────────────────────┤
│                                              │
│  EC2 Instance (Amazon Linux 2023)           │
│    - Docker & Docker Compose                │
│    - 全マイクロサービス                       │
│    - Nginx (Port 80)                        │
│                                              │
│  RDS PostgreSQL 17.4                        │
│    - エンドポイント: running-analysis-db-    │
│      single.cbqqcwic00jv.ap-southeast-2.    │
│      rds.amazonaws.com                      │
│    - Single Instance                        │
│                                              │
│  リージョン: ap-southeast-2 (Sydney)          │
└─────────────────────────────────────────────┘
```

**デプロイスクリプト**
```bash
# 本番環境デプロイ
./deploy_to_ec2.sh

# フロントエンドのみ更新
./update_ec2_frontend.sh
```

**環境変数（本番）**
```bash
# .env ファイル（EC2上）
ENABLE_DB_SAVE=true                           # 本番ではDB保存有効
DB_HOST=running-analysis-db-single...         # RDSエンドポイント
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
OPENAI_API_KEY=your_api_key
VIDEO_GENERATION_PASSWORD=admin123
```

### 10.3 Docker Compose構成

**本番環境用設定**
```yaml
# docker-compose.prod.yml
services:
  frontend:
    environment:
      - NODE_ENV=production
    restart: always
  
  video_processing:
    environment:
      - ENABLE_DB_SAVE=true
    volumes:
      - /data/uploads:/app/uploads
    restart: always
```

---

## 11. セキュリティ

### 11.1 セキュリティ対策

| 対策項目 | 実装内容 |
|---------|---------|
| **ファイルアップロード** | ファイル形式検証、サイズ制限（500MB） |
| **SQLインジェクション** | Pydantic + パラメータ化クエリ |
| **XSS対策** | Next.jsの自動エスケープ |
| **CORS** | 適切なCORS設定 |
| **認証** | ユーザーID検証（将来的にJWT導入予定） |
| **API保護** | 動画生成APIはパスワード保護 |

### 11.2 データ保護

```
┌─────────────────────────────────────────────┐
│            データ保護戦略                      │
├─────────────────────────────────────────────┤
│  • 動画ファイル                               │
│    → UUID命名でファイル名衝突を防止            │
│    → アップロード後の検証                      │
│                                              │
│  • 個人情報                                   │
│    → メールアドレスのみ（現時点）              │
│    → 将来的にパスワードはbcryptでハッシュ化    │
│                                              │
│  • データベース                               │
│    → AWS RDS セキュリティグループで保護        │
│    → SSL/TLS接続                             │
└─────────────────────────────────────────────┘
```

---

## 12. パフォーマンス

### 12.1 パフォーマンス指標

| 指標 | 目標値 | 実測値 |
|------|-------|-------|
| **動画アップロード** | 5秒以内 | 2-5秒 |
| **骨格検出** | 30秒以内 | 15-30秒 |
| **全解析パイプライン** | 60秒以内 | 30-60秒 |
| **ページ読み込み** | 2秒以内 | 1-2秒 |
| **データベースクエリ** | 100ms以内 | 50-100ms |

### 12.2 最適化戦略

**フロントエンド**
- 大容量データ（骨格データ）はZustandで管理
- 軽量データのみlocalStorageに保存
- グラフの遅延レンダリング

**バックエンド**
- 各サービスの独立したコンテナ化
- 非同期処理（FastAPI + async/await）
- データベースインデックス

**インフラ**
- Docker Volumeによるディスク最適化
- Nginxによるリバースプロキシ
- ヘルスチェック機能

---

## 13. 開発環境

### 13.1 必要なツール

| ツール | バージョン | 用途 |
|-------|----------|------|
| **Docker** | 24.x+ | コンテナ実行 |
| **Docker Compose** | 2.x+ | マルチコンテナ管理 |
| **Git** | 2.x+ | バージョン管理 |
| **Cursor / VS Code** | latest | コードエディタ |
| **Node.js** | 18.x+ | フロントエンド開発 |
| **Python** | 3.11+ | バックエンド開発 |

### 13.2 セットアップ手順

```bash
# 1. リポジトリクローン
git clone https://github.com/riku234/running-analysis-system.git
cd running-analysis-system

# 2. 環境変数ファイル作成
cat > .env << EOF
ENABLE_DB_SAVE=false
OPENAI_API_KEY=your_api_key
VIDEO_GENERATION_PASSWORD=admin123
EOF

# 3. 全サービス起動
docker-compose up -d

# 4. ログ確認
docker-compose logs -f
```

**詳細**: `DEVELOPMENT_SETUP_GUIDE.md` 参照

### 13.3 開発フロー

```
┌─────────────────────────────────────────────┐
│             Git開発フロー                     │
├─────────────────────────────────────────────┤
│  1. mainブランチから作業ブランチ作成          │
│     git checkout -b feature/new-feature     │
│                                              │
│  2. コード変更・テスト                        │
│                                              │
│  3. コミット                                  │
│     git add .                               │
│     git commit -m "説明"                    │
│                                              │
│  4. プッシュ                                  │
│     git push origin feature/new-feature     │
│                                              │
│  5. プルリクエスト作成                        │
│     GitHub上で main ← feature/new-feature  │
│                                              │
│  6. レビュー後マージ                          │
└─────────────────────────────────────────────┘
```

---

## 14. 運用・保守

### 14.1 ログ管理

**ログレベル**
```python
# Pythonサービス
logging.basicConfig(level=logging.INFO)

# ログレベル設定
DEBUG   # 詳細デバッグ情報
INFO    # 通常動作情報
WARNING # 警告
ERROR   # エラー
```

**ログ確認コマンド**
```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f video_processing

# エラーログのみ表示
docker-compose logs | grep ERROR
```

### 14.2 ヘルスチェック

各サービスにヘルスチェックエンドポイントを実装

```bash
# サービスヘルスチェック
curl http://localhost:8001/  # Video Processing
curl http://localhost:8002/  # Pose Estimation
curl http://localhost:8003/  # Feature Extraction
curl http://localhost:8004/  # Analysis
curl http://localhost:8005/  # Advice Generation
curl http://localhost:8006/  # Video Generation
```

### 14.3 バックアップ戦略

**データベース**
```bash
# 手動バックアップ
pg_dump -h <RDS_ENDPOINT> -U postgres postgres > backup.sql

# 復元
psql -h <RDS_ENDPOINT> -U postgres postgres < backup.sql
```

**動画ファイル**
- Docker Volumeのバックアップ
- 定期的にS3へアーカイブ（将来実装）

### 14.4 監視項目

| 監視項目 | 閾値 | アラート条件 |
|---------|------|-------------|
| **CPU使用率** | 80% | 継続5分以上 |
| **メモリ使用率** | 85% | 継続5分以上 |
| **ディスク容量** | 90% | 即座 |
| **応答時間** | 3秒 | 3回連続 |
| **エラー率** | 5% | 1時間あたり |

### 14.5 トラブルシューティング

**よくある問題と解決方法**

| 問題 | 原因 | 解決方法 |
|------|------|---------|
| コンテナ起動失敗 | ポート競合 | `docker-compose down` 後に再起動 |
| メモリ不足 | Dockerメモリ制限 | Docker Desktop設定で8GB以上に増加 |
| DB接続エラー | 環境変数未設定 | `.env`ファイルを確認 |
| アップロード失敗 | ファイルサイズ超過 | 500MB以下に圧縮 |
| AIモデルエラー | モデル未ダウンロード | コンテナ再ビルド |

**詳細**: `aws_recovery_guide.md` 参照

---

## 15. 今後の拡張計画

### 15.1 短期計画（3ヶ月以内）

- [ ] ユーザー認証機能（JWT）
- [ ] 過去の解析履歴表示
- [ ] 解析結果のPDFエクスポート
- [ ] 動画のグレースケール処理機能

### 15.2 中期計画（6ヶ月以内）

- [ ] リアルタイム解析（WebSocket）
- [ ] スマホアプリ対応（PWA）
- [ ] 複数カメラアングル対応
- [ ] AIモデルの精度向上

### 15.3 長期計画（1年以内）

- [ ] SaaS化（サブスクリプションモデル）
- [ ] コーチング機能（チャット）
- [ ] SNS連携（結果共有）
- [ ] 多言語対応（英語・中国語）

---

## 16. 参考資料

### 16.1 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `README.md` | プロジェクト概要・クイックスタート |
| `DEVELOPMENT_SETUP_GUIDE.md` | 開発環境セットアップ詳細 |
| `DATABASE_SCHEMA_DOCUMENTATION.md` | データベース仕様詳細 |
| `DATABASE_SETUP_GUIDE.md` | データベースセットアップ |
| `GITHUB_SETUP_GUIDE.md` | Git運用ガイド |
| `aws_recovery_guide.md` | AWS復旧手順 |
| `project_progress.md` | プロジェクト進捗管理 |

### 16.2 外部リンク

- [MediaPipe Documentation](https://developers.google.com/mediapipe)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

## 17. 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0.0 | 2025-01-26 | 初版作成 |
| 2.0.0 | 2025-10-06 | Z値分析機能追加、DB統合 |
| 3.0.0 | 2025-10-20 | 統合アドバイス機能、プロンプト設定追加 |

---

## 18. ライセンス

本プロジェクトはMITライセンスの下で公開されています。

---

**Document Version**: 3.0.0  
**Last Updated**: 2025年10月20日  
**Author**: Running Analysis System Development Team


