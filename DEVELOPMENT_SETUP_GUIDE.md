# 開発環境セットアップガイド

このドキュメントは、複数人でこのプロジェクトを開発するための環境セットアップ手順を説明します。

---

## 📋 目次

1. [必要なツール](#必要なツール)
2. [初回セットアップ](#初回セットアップ)
3. [環境変数の設定](#環境変数の設定)
4. [Dockerコンテナの起動](#dockerコンテナの起動)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)
7. [よくある質問](#よくある質問)

---

## 必要なツール

### 1. Cursor（推奨エディタ）

**ダウンロード**: https://cursor.sh/

- このプロジェクトはCursorでの開発を前提としています
- VS Codeベースのため、VS Codeユーザーも問題なく使用できます

### 2. Docker Desktop

**ダウンロード**: https://www.docker.com/products/docker-desktop/

- **macOS**: Docker Desktop for Mac
- **Windows**: Docker Desktop for Windows
- **Linux**: Docker Engine

**インストール確認**:
```bash
docker --version
docker-compose --version
```

期待される出力例:
```
Docker version 24.0.0, build ...
Docker Compose version v2.20.0
```

### 3. Git

**ダウンロード**: https://git-scm.com/downloads

**インストール確認**:
```bash
git --version
```

期待される出力例:
```
git version 2.40.0
```

---

## 初回セットアップ

### ステップ 1: リポジトリのクローン

```bash
# リポジトリをクローン
git clone https://github.com/riku234/running-analysis-system.git

# プロジェクトディレクトリに移動
cd running-analysis-system
```

### ステップ 2: Cursorでプロジェクトを開く

1. Cursorを起動
2. `File` → `Open Folder...`
3. クローンした`running-analysis-system`フォルダを選択
4. フォルダが開かれます

---

## 環境変数の設定

### ステップ 1: `.env`ファイルの作成

プロジェクトルートに`.env`ファイルを作成します。

**方法1: Cursorで作成**
1. Cursorの左サイドバーでプロジェクトルートを右クリック
2. `New File`を選択
3. ファイル名: `.env`

**方法2: ターミナルで作成**
```bash
touch .env
```

### ステップ 2: `.env`ファイルの内容

以下の内容を`.env`ファイルに貼り付けます:

```env
# ============================================================================
# RDSデータベースへの接続情報
# ============================================================================
# ⚠️ ローカル開発ではデータベース保存は無効化されています（ENABLE_DB_SAVE=false）
# データベース接続情報は、EC2デプロイ時に使用されます

# データベースのエンドポイント
DB_HOST=running-analysis-db-single.cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com

# データベースのポート番号（通常は5432）
DB_PORT=5432

# データベース名
DB_NAME=postgres

# マスターユーザー名
DB_USER=postgres

# マスターパスワード
DB_PASSWORD=vfmdev_01

# ============================================================================
# API設定
# ============================================================================

# Gemini API設定（個別課題アドバイス生成用）
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API設定（Sora-2 トレーニング動画生成用）
OPENAI_API_KEY=your_openai_api_key_here

# 動画生成パスワード
VIDEO_GENERATION_PASSWORD=xebio-generate
```

### ステップ 3: `.env`ファイルの確認

```bash
# .envファイルの存在を確認
ls -la | grep .env

# .envファイルの内容を確認（オプション）
cat .env
```

⚠️ **重要**: `.env`ファイルは`.gitignore`に含まれているため、Gitにコミットされません（セキュリティのため）

---

## Dockerコンテナの起動

### ステップ 1: Docker Desktopの起動

1. Docker Desktopアプリケーションを起動
2. Docker Desktopが完全に起動するまで待つ（数秒〜数分）

### ステップ 2: Dockerイメージのビルド

Cursorのターミナル（または外部ターミナル）で以下を実行:

```bash
# すべてのDockerイメージをビルド
docker-compose build
```

**所要時間**: 初回は5〜10分程度かかります

**期待される出力**:
```
Building pose_estimation
Building feature_extraction
Building analysis
Building advice_generation
Building video_processing
Building frontend
Building api_gateway
Building video_generation
Successfully built ...
```

### ステップ 3: コンテナの起動

```bash
# すべてのコンテナをバックグラウンドで起動
docker-compose up -d
```

**期待される出力**:
```
Creating network "running-analysis-system_app_network" ...
Creating running-analysis-system-pose_estimation-1 ... done
Creating running-analysis-system-feature_extraction-1 ... done
Creating running-analysis-system-analysis-1 ... done
Creating running-analysis-system-advice_generation-1 ... done
Creating running-analysis-system-video_processing-1 ... done
Creating running-analysis-system-frontend-1 ... done
Creating running-analysis-system-api_gateway-1 ... done
Creating running-analysis-system-video_generation-1 ... done
```

### ステップ 4: コンテナの起動確認

```bash
# 起動中のコンテナを確認
docker-compose ps
```

**期待される出力**:
すべてのコンテナのSTATUSが`Up`または`Up (healthy)`になっていることを確認

---

## 動作確認

### 1. フロントエンドへのアクセス

ブラウザで以下のURLにアクセス:

```
http://localhost
```

**期待される表示**:
- ランニング解析システムのアップロード画面が表示される

### 2. テスト動画のアップロード

1. 「ファイルを選択」ボタンをクリック
2. テスト用のランニング動画を選択
3. 「アップロードして解析開始」ボタンをクリック
4. 解析が完了すると結果ページに遷移

### 3. 動作確認チェックリスト

- ✅ 動画アップロードが成功する
- ✅ 骨格検出が動作する
- ✅ 動画プレイヤーに骨格が表示される
- ✅ Z-score分析結果が表示される
- ✅ アドバイスカードが表示される
- ✅ グレースケール切り替えボタンが表示される

---

## トラブルシューティング

### 問題1: `docker-compose: command not found`

**原因**: Docker Desktopがインストールされていないか、PATHが通っていない

**解決策**:
1. Docker Desktopをインストール
2. ターミナルを再起動
3. Docker Desktopが起動していることを確認

### 問題2: ポート競合エラー

**エラーメッセージ例**:
```
Error: Bind for 0.0.0.0:80 failed: port is already allocated
```

**原因**: ポート80が他のプロセスで使用されている

**解決策**:
```bash
# ポート80を使用しているプロセスを確認
lsof -i :80

# 該当するプロセスを終了
kill -9 <PID>

# または、docker-compose.ymlでポート番号を変更
# api_gateway:
#   ports:
#     - "8080:80"  # ポート8080に変更
```

### 問題3: コンテナが起動しない

**確認コマンド**:
```bash
# ログを確認
docker-compose logs <サービス名>

# 例: frontendのログを確認
docker-compose logs frontend
```

**よくある原因**:
- `.env`ファイルが存在しない → ステップ3を再確認
- Docker Desktopが起動していない → Docker Desktopを起動
- メモリ不足 → Docker Desktopのメモリ設定を増やす

### 問題4: フロントエンドが表示されない

**確認手順**:
```bash
# フロントエンドのログを確認
docker-compose logs frontend

# API Gatewayのログを確認
docker-compose logs api_gateway
```

**解決策**:
```bash
# コンテナを再起動
docker-compose restart frontend api_gateway

# または、すべてのコンテナを再起動
docker-compose restart
```

### 問題5: `.env`ファイルが反映されない

**原因**: コンテナ起動後に`.env`ファイルを変更した

**解決策**:
```bash
# コンテナを完全に削除して再作成
docker-compose down
docker-compose up -d
```

---

## よくある質問

### Q1: ローカル開発でデータベースは必要ですか？

**A**: いいえ、ローカル開発ではデータベース保存は無効化されています（`ENABLE_DB_SAVE=false`）。データベース接続情報は、EC2デプロイ時のみ使用されます。

### Q2: Gemini APIキーとOpenAI APIキーは必要ですか？

**A**: はい、以下の機能で使用されます:
- **Gemini API**: 個別課題の解説生成
- **OpenAI API**: トレーニング動画生成（Sora-2）

APIキーがない場合、デフォルトのフォールバックメッセージが表示されます。

### Q3: コンテナを停止するには？

**A**:
```bash
# すべてのコンテナを停止
docker-compose stop

# すべてのコンテナを停止して削除
docker-compose down
```

### Q4: コンテナを再起動するには？

**A**:
```bash
# すべてのコンテナを再起動
docker-compose restart

# 特定のコンテナのみ再起動
docker-compose restart frontend
```

### Q5: コードを変更した後、反映するには？

**A**:

**フロントエンド（React/Next.js）**:
```bash
# フロントエンドを再ビルド＆再起動
docker-compose build frontend
docker-compose up -d frontend
```

**バックエンド（Python/FastAPI）**:
```bash
# 特定のサービスを再ビルド＆再起動
docker-compose build video_processing
docker-compose up -d video_processing
```

**すべて**:
```bash
# すべてのサービスを再ビルド＆再起動
docker-compose build
docker-compose up -d
```

### Q6: ログをリアルタイムで確認するには？

**A**:
```bash
# すべてのコンテナのログをリアルタイム表示
docker-compose logs -f

# 特定のコンテナのログをリアルタイム表示
docker-compose logs -f frontend

# Ctrl+C で終了
```

### Q7: Docker環境をクリーンアップするには？

**A**:
```bash
# コンテナを停止して削除
docker-compose down

# コンテナ、ネットワーク、ボリュームをすべて削除
docker-compose down -v

# 未使用のDockerイメージを削除
docker system prune -a
```

---

## 開発フロー

### 日常的な開発フロー

1. **朝の起動**:
```bash
# Docker Desktopを起動
# ターミナルでプロジェクトディレクトリに移動
cd running-analysis-system

# コンテナを起動
docker-compose up -d

# ブラウザでhttp://localhostを開く
```

2. **コード変更**:
- Cursorでコードを編集
- 変更を保存

3. **変更の反映**:
```bash
# フロントエンド変更時
docker-compose build frontend
docker-compose up -d frontend

# バックエンド変更時
docker-compose build <サービス名>
docker-compose up -d <サービス名>
```

4. **動作確認**:
- ブラウザでhttp://localhostをリロード
- テスト実行

5. **終了時**:
```bash
# コンテナを停止（オプション）
docker-compose stop

# または、起動したままでもOK
```

### Gitでの共同開発フロー

1. **最新のコードを取得**:
```bash
# mainブランチの最新を取得
git checkout main
git pull origin main
```

2. **フィーチャーブランチを作成**:
```bash
# 新機能用のブランチを作成
git checkout -b feature/new-feature
```

3. **開発**:
- コードを編集
- ローカルでテスト

4. **コミット**:
```bash
# 変更をステージング
git add .

# コミット
git commit -m "feat: 新機能の説明"
```

5. **プッシュ**:
```bash
# リモートにプッシュ
git push origin feature/new-feature
```

6. **プルリクエスト**:
- GitHubでプルリクエストを作成
- レビューを依頼

---

## 便利なコマンド集

### Docker関連

```bash
# コンテナの状態を確認
docker-compose ps

# ログを確認（最新100行）
docker-compose logs --tail=100

# 特定のコンテナのログ
docker-compose logs --tail=100 frontend

# コンテナ内でコマンド実行
docker-compose exec frontend sh

# すべてのコンテナを再起動
docker-compose restart

# 特定のコンテナを再起動
docker-compose restart frontend

# コンテナを削除して再作成
docker-compose up -d --force-recreate frontend

# ビルドキャッシュを無視して再ビルド
docker-compose build --no-cache frontend
```

### Git関連

```bash
# 現在のブランチを確認
git branch

# 変更されたファイルを確認
git status

# 変更内容を確認
git diff

# コミット履歴を確認
git log --oneline

# ブランチを切り替え
git checkout <ブランチ名>

# 変更を一時退避
git stash

# 退避した変更を復元
git stash pop
```

---

## サポート

### 問題が解決しない場合

1. **ログを確認**:
```bash
docker-compose logs --tail=100
```

2. **コンテナの状態を確認**:
```bash
docker-compose ps
```

3. **完全にクリーンアップして再起動**:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

4. **チームメンバーに相談**:
- 同じエラーが発生していないか確認
- Slackやチャットで共有

---

## 追加リソース

- **Docker公式ドキュメント**: https://docs.docker.com/
- **Docker Compose公式ドキュメント**: https://docs.docker.com/compose/
- **Next.js公式ドキュメント**: https://nextjs.org/docs
- **FastAPI公式ドキュメント**: https://fastapi.tiangolo.com/

---

## まとめ

このガイドに従えば、チームメンバー全員が同じ環境でスムーズに開発を開始できます。

**基本の流れ**:
1. Docker Desktopをインストール
2. リポジトリをクローン
3. `.env`ファイルを作成
4. `docker-compose up -d`でコンテナ起動
5. http://localhost で動作確認

質問や問題があれば、チームで共有して解決しましょう！

**Happy Coding! 🚀**

