# ランニング動画自動解析エキスパートシステム

ランニング動画をアップロードすると、AIがフォームを自動で解析し、骨格検出、特徴量計算、フォーム評価を行い、具体的な改善アドバイスを生成・提供するWebアプリケーションです。

## 🏃‍♂️ 機能概要

- **動画アップロード**: MP4, AVI, MOV形式の動画ファイルに対応
- **骨格検出**: YOLO + MediaPipeによる高精度な人体骨格検出
- **特徴量解析**: ストライド長、ケイデンス、関節角度、接地時間などの詳細分析
- **フォーム評価**: 総合スコア、効率性評価、怪我リスク評価
- **改善アドバイス**: 個人最適化された具体的な改善提案とエクササイズプラン

## 🏗️ アーキテクチャ

### マイクロサービス構成

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │
│   (Next.js)     │────│   (Nginx)       │
│   Port: 3000    │    │   Port: 80      │
└─────────────────┘    └─────────┬───────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
         ┌──────────▼──┐  ┌──────▼──┐  ┌─────▼──────┐
         │Video        │  │Pose     │  │Feature     │
         │Processing   │  │Estimation│  │Extraction  │
         │Port: 8001   │  │Port: 8002│  │Port: 8003  │
         └─────────────┘  └─────────┘  └────────────┘
                    
                    ┌─────────────┐  ┌─────────────┐
                    │Analysis     │  │Advice       │
                    │Port: 8004   │  │Generation   │
                    └─────────────┘  │Port: 8005   │
                                     └─────────────┘
```

### サービス詳細

| サービス | 技術スタック | 役割 |
|---------|-------------|------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | ユーザーインターフェース |
| **API Gateway** | Nginx | リクエストルーティングと負荷分散 |
| **Video Processing** | FastAPI, OpenCV, FFmpeg | 動画前処理、フレーム抽出 |
| **Pose Estimation** | FastAPI, YOLO v8, MediaPipe | 骨格キーポイント検出 |
| **Feature Extraction** | FastAPI, NumPy, SciPy | 生体力学的特徴量計算 |
| **Analysis** | FastAPI, scikit-learn | フォーム問題点分析 |
| **Advice Generation** | FastAPI | 改善アドバイス生成 |

## 🚀 クイックスタート

### 前提条件

- Docker & Docker Compose
- Git

### インストールと起動

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd ランニング解析
```

2. **全サービスの起動**
```bash
docker-compose up --build
```

3. **アクセス**
- フロントエンド: http://localhost:3000
- API Gateway: http://localhost:80
- 各マイクロサービス: http://localhost:8001-8005

### 初回起動時の注意

初回起動時は以下の処理のため5-10分程度時間がかかります：
- Dockerイメージのビルド
- AI models (YOLO, MediaPipe) のダウンロード
- 依存関係のインストール

## 📊 使用方法

### 1. 動画アップロード
1. ブラウザで http://localhost:3000 にアクセス
2. 「動画ファイルを選択」ボタンをクリック
3. ランニング動画をアップロード（推奨：横撮り、10秒以上）
4. 「解析を開始」ボタンをクリック

### 2. 解析結果確認
- 総合スコア（1-10点）
- 効率性評価（A+ ～ D）
- 怪我リスクレベル（低・中・高）
- 詳細な問題点とアドバイス

### 3. 改善プラン
- 個別最適化された改善提案
- 具体的なエクササイズプラン
- フォローアップスケジュール

## 🛠️ 開発

### 個別サービスの起動

特定のサービスのみを起動する場合：

```bash
# フロントエンドのみ
docker-compose up frontend

# バックエンドサービスのみ
docker-compose up video_processing pose_estimation
```

### API エンドポイント

| サービス | エンドポイント | 説明 |
|---------|---------------|------|
| Video Processing | `POST /api/video/process` | 動画アップロード・前処理 |
| Pose Estimation | `POST /api/pose/estimate` | 骨格検出 |
| Feature Extraction | `POST /api/features/extract` | 特徴量抽出 |
| Analysis | `POST /api/analysis/analyze` | フォーム分析 |
| Advice Generation | `POST /api/advice/generate` | アドバイス生成 |

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f video_processing
```

## 🔧 設定

### 環境変数

各サービスの動作をカスタマイズするための環境変数：

```bash
# Video Processing
VIDEO_MAX_SIZE=100MB
FRAME_RATE=30

# Pose Estimation  
YOLO_MODEL=yolov8n.pt
MEDIAPIPE_CONFIDENCE=0.7

# Analysis
ANALYSIS_CONFIDENCE_THRESHOLD=0.8
```

### パフォーマンス調整

高負荷環境での推奨設定：

```yaml
# docker-compose.override.yml
services:
  pose_estimation:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

## 📈 監視とメトリクス

### ヘルスチェック

各サービスのヘルスチェックエンドポイント：

```bash
curl http://localhost:8001/  # Video Processing
curl http://localhost:8002/  # Pose Estimation
curl http://localhost:8003/  # Feature Extraction
curl http://localhost:8004/  # Analysis
curl http://localhost:8005/  # Advice Generation
```

### パフォーマンスメトリクス

- 動画処理時間: 平均30-60秒（10秒動画）
- 骨格検出精度: 95%以上
- システム応答時間: 5秒以内

## 🚨 トラブルシューティング

### よくある問題

#### 1. メモリ不足エラー
```bash
# 解決方法：Dockerのメモリ割り当てを増加
# Docker Desktop > Settings > Resources > Memory: 8GB以上
```

#### 2. ポート競合エラー
```bash
# 使用中のポートを確認
lsof -i :3000
lsof -i :80

# 設定変更
# docker-compose.yml の ports セクションを変更
```

#### 3. AI モデルダウンロードエラー
```bash
# 手動でモデルを再ダウンロード
docker-compose exec pose_estimation python -c "
import ultralytics; ultralytics.YOLO('yolov8n.pt')
"
```

### ログレベル設定

デバッグ時のログレベル変更：

```bash
# 詳細ログを有効化
export LOG_LEVEL=DEBUG
docker-compose up --build
```

## 📝 ライセンス

本プロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

プルリクエストやイシューの報告を歓迎します。

1. プロジェクトをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

## 📧 サポート

技術的な質問や問題については、GitHubのIssuesセクションをご利用ください。

---

**バージョン**: 1.0.0  
**最終更新**: 2025年1月26日 