# 🐙 GitHub連携セットアップガイド

**対象アカウント**: riku234  
**プロジェクト**: ランニング動画自動解析エキスパートシステム  
**設定日**: 2025年1月26日

## 📋 GitHub設定手順

### ステップ 1: GitHubリポジトリ作成

1. **GitHub.comにアクセス**
   - ブラウザで https://github.com にアクセス
   - riku234アカウントでログイン

2. **新リポジトリ作成**
   - 画面右上の「+」→「New repository」をクリック
   - リポジトリ設定：
     ```
     Repository name: running-analysis-system
     Description: ランニング動画自動解析エキスパートシステム - AI駆動のフォーム分析とアドバイス生成
     Visibility: Public (または Private)
     Initialize: DON'T initialize (重要: 既存コードがあるため)
     ```

3. **リポジトリ作成完了**
   - 「Create repository」をクリック
   - リポジトリURLが表示される：
     `https://github.com/riku234/running-analysis-system.git`

### ステップ 2: ローカルとGitHubの連携

以下のコマンドをターミナルで実行してください：

#### A. リモートリポジトリの追加
```bash
git remote add origin https://github.com/riku234/running-analysis-system.git
```

#### B. デフォルトブランチ名の設定
```bash
git branch -M main
```

#### C. GitHubへのプッシュ
```bash
git push -u origin main
```

### ステップ 3: GitHub認証設定

初回プッシュ時に認証が求められます：

#### 方法1: Personal Access Token（推奨）
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token」→「Generate new token (classic)」
3. 以下の権限を選択：
   ```
   ✅ repo (Full control of private repositories)
   ✅ workflow (Update GitHub Action workflows)
   ✅ write:packages (Upload packages to GitHub Package Registry)
   ```
4. トークンをコピーして保存
5. プッシュ時にパスワード欄にトークンを入力

#### 方法2: SSH Key（上級者向け）
```bash
# SSH キー生成
ssh-keygen -t ed25519 -C "your_email@example.com"

# 公開鍵をGitHubに追加
cat ~/.ssh/id_ed25519.pub
# ↑ の内容をGitHub Settings → SSH Keys に追加

# SSH URLでリモート設定
git remote set-url origin git@github.com:riku234/running-analysis-system.git
```

## 🎯 プッシュ後の確認

### GitHubリポジトリで確認できること

#### 1. **プロジェクト構造**
```
running-analysis-system/
├── .github/workflows/     # CI/CD設定（将来）
├── backend/              # バックエンドサービス群
├── frontend/             # Next.jsフロントエンド
├── docs/                 # ドキュメント・レポート
├── docker-compose.yml    # Docker統合設定
└── README.md             # プロジェクト概要
```

#### 2. **コミット履歴**
- 8つの段階的コミット
- 機能単位での論理的な開発履歴
- 完全な実装トレーサビリティ

#### 3. **実装状況**
- ✅ 動画アップロード機能
- ✅ MediaPipe骨格推定
- ✅ Docker統合環境
- 🚧 特徴量抽出（ダミー）
- 🚧 フォーム分析（ダミー）
- 🚧 改善提案（ダミー）

## 🔄 継続的開発ワークフロー

### 新機能開発の流れ

#### 1. **Feature Branch作成**
```bash
git checkout -b feature/特徴量抽出実装
```

#### 2. **開発・コミット**
```bash
git add .
git commit -m "feat: 関節角度計算機能の実装"
```

#### 3. **プッシュ・Pull Request**
```bash
git push origin feature/特徴量抽出実装
# GitHub上でPull Request作成
```

#### 4. **マージ・デプロイ**
```bash
git checkout main
git pull origin main
```

## 📁 推奨リポジトリ設定

### README.mdの充実
- [x] プロジェクト概要
- [x] アーキテクチャ図
- [x] セットアップ手順
- [x] API仕様
- [ ] デモ動画・スクリーンショット
- [ ] コントリビューションガイド

### Issue・Project管理
- [ ] Issue Template作成
- [ ] Project Board設定
- [ ] Milestone管理

### CI/CD設定
- [ ] GitHub Actions設定
- [ ] 自動テスト実行
- [ ] Docker Hub連携

## 🔐 セキュリティ設定

### 機密情報の管理
```bash
# .gitignore確認（既に設定済み）
cat .gitignore

# 環境変数設定
cp .env.example .env  # 将来の設定
```

### GitHub Secrets
以下の情報をGitHub Secretsに設定（将来）：
- `DOCKER_HUB_TOKEN`
- `API_KEYS`
- `DATABASE_CREDENTIALS`

## 📊 GitHub活用機能

### 1. **GitHub Pages**
- ドキュメントサイトの自動公開
- プロジェクトポートフォリオ

### 2. **GitHub Packages**
- Dockerイメージの配布
- パッケージ管理

### 3. **GitHub Codespaces**
- クラウド開発環境
- 即座の開発開始

## ✨ 完了後の状態

GitHubリポジトリ作成完了後：

### 🌐 **アクセス可能URL**
- **リポジトリ**: https://github.com/riku234/running-analysis-system
- **Issue**: https://github.com/riku234/running-analysis-system/issues
- **Wiki**: https://github.com/riku234/running-analysis-system/wiki

### 👥 **チーム開発準備**
- ✅ コラボレーター招待可能
- ✅ Pull Request ワークフロー
- ✅ Issue・Project管理
- ✅ CI/CD Pipeline構築準備

### 🚀 **デプロイ準備**
- ✅ Docker Hub連携
- ✅ クラウドプラットフォーム連携
- ✅ 本番環境デプロイ

## 🎉 次のステップ

1. **GitHubリポジトリ作成** ← まずはここから！
2. **ローカル→GitHub プッシュ**
3. **README.mdの追加充実**
4. **Issue・Project設定**
5. **CI/CD Pipeline構築**

この手順に従って、riku234アカウントでランニング動画自動解析エキスパートシステムのGitHubリポジトリを作成・公開できます！ 