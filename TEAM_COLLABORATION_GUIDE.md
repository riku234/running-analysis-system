# チーム開発での競合回避ガイド

このドキュメントは、複数人で開発する際に変更が競合しないようにするためのベストプラクティスをまとめたものです。

---

## 📋 目次

1. [基本原則](#基本原則)
2. [Gitブランチ戦略](#gitブランチ戦略)
3. [作業前の確認事項](#作業前の確認事項)
4. [作業中の注意点](#作業中の注意点)
5. [コミット・プッシュのルール](#コミットプッシュのルール)
6. [競合が発生した場合の対処](#競合が発生した場合の対処)
7. [コードレビューのプロセス](#コードレビューのプロセス)
8. [よくある競合パターンと回避方法](#よくある競合パターンと回避方法)

---

## 基本原則

### 🎯 3つの黄金ルール

1. **作業前に必ず最新を取得**
   ```bash
   git pull origin main
   ```

2. **機能ごとにブランチを分ける**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **こまめにコミット、定期的にプッシュ**
   ```bash
   git add .
   git commit -m "feat: 機能の説明"
   git push origin feature/your-feature-name
   ```

---

## Gitブランチ戦略

### ブランチの種類

```
main (本番環境)
  │
  ├── feature/user-selection (機能A)
  ├── feature/zscore-highlight (機能B)
  ├── fix/database-connection (バグ修正)
  └── docs/setup-guide (ドキュメント)
```

### ブランチ命名規則

| 種類 | プレフィックス | 例 |
|------|--------------|-----|
| 新機能 | `feature/` | `feature/video-grayscale` |
| バグ修正 | `fix/` | `fix/api-timeout` |
| ドキュメント | `docs/` | `docs/setup-guide` |
| リファクタリング | `refactor/` | `refactor/database-utils` |
| パフォーマンス改善 | `perf/` | `perf/video-processing` |
| テスト | `test/` | `test/api-endpoints` |

### ブランチの作成手順

```bash
# 1. mainブランチに移動
git checkout main

# 2. 最新を取得
git pull origin main

# 3. 新しいブランチを作成
git checkout -b feature/your-feature-name

# 4. 作業開始
```

---

## 作業前の確認事項

### ✅ 作業開始前のチェックリスト

```bash
# 1. 現在のブランチを確認
git branch

# 2. 変更されていないファイルがないか確認
git status

# 3. 最新のmainを取得
git checkout main
git pull origin main

# 4. 新しいブランチを作成
git checkout -b feature/your-feature-name

# 5. 他のメンバーが作業中の内容を確認
git branch -r  # リモートブランチ一覧
```

### 📢 チームとのコミュニケーション

**作業開始時に共有すること**:
- どのファイルを編集する予定か
- どの機能を実装する予定か
- 作業の予定期間

**例（Slackやチャット）**:
```
🚀 作業開始
機能: 動画グレースケール表示
ファイル: frontend/app/components/PoseVisualizer.tsx
期間: 今日中に完了予定
ブランチ: feature/video-grayscale
```

---

## 作業中の注意点

### 🔴 同時に編集してはいけないファイル

以下のファイルは競合しやすいため、**同時に複数人が編集しないよう調整**してください：

#### 1. 設定ファイル
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env`（各自ローカルのみ）
- `package.json`
- `requirements.txt`

#### 2. 共通コンポーネント
- `frontend/app/components/PoseVisualizer.tsx`
- `frontend/app/page.tsx`（アップロード画面）
- `frontend/app/result/[id]/page.tsx`（結果画面）

#### 3. データベース関連
- `database_schema.sql`
- `backend/services/*/db_utils.py`

#### 4. API Gateway設定
- `backend/api_gateway/nginx.conf`

### ✅ 同時に編集しても問題ないファイル

以下は独立しているため、同時編集可能：

- 各サービスの独立した機能（例: `analysis/app/main.py` と `advice_generation/app/main.py`）
- 新しいコンポーネントファイル（既存を変更しない場合）
- ドキュメントファイル（別々のファイルなら）

### 📝 作業中のコミット頻度

**推奨: 30分〜1時間ごとにコミット**

```bash
# 小さな単位でコミット
git add frontend/app/components/NewComponent.tsx
git commit -m "feat: NewComponentの基本構造を追加"

# 30分後
git add frontend/app/components/NewComponent.tsx
git commit -m "feat: NewComponentにスタイルを追加"

# さらに30分後
git add frontend/app/components/NewComponent.tsx
git commit -m "feat: NewComponentにロジックを追加"
```

**メリット**:
- 競合が発生しても影響範囲が小さい
- 問題があった場合に戻しやすい
- 他のメンバーが進捗を把握しやすい

---

## コミット・プッシュのルール

### コミットメッセージの規則

```bash
# 形式: <type>: <説明>

# 新機能
git commit -m "feat: 動画グレースケール表示機能を追加"

# バグ修正
git commit -m "fix: データベース接続エラーを修正"

# ドキュメント
git commit -m "docs: セットアップガイドを追加"

# リファクタリング
git commit -m "refactor: データベースユーティリティを整理"

# パフォーマンス改善
git commit -m "perf: 動画処理速度を改善"

# テスト
git commit -m "test: APIエンドポイントのテストを追加"
```

### プッシュのタイミング

**推奨: 1日の終わりに必ずプッシュ**

```bash
# 作業終了時
git push origin feature/your-feature-name
```

**理由**:
- 他のメンバーが進捗を確認できる
- PCが壊れてもコードが失われない
- 翌日、別のPCから作業を続けられる

---

## 競合が発生した場合の対処

### シナリオ1: プッシュ時に競合

```bash
# プッシュしようとしたらエラー
$ git push origin main
To https://github.com/...
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs
```

**対処法**:

```bash
# 1. 最新を取得（マージ）
git pull origin main

# 2. 競合が発生した場合、ファイルを確認
git status

# 3. 競合ファイルを開いて編集
# <<<<<<< HEAD
# あなたの変更
# =======
# 他の人の変更
# >>>>>>> branch-name

# 4. 競合を解決したらコミット
git add <競合したファイル>
git commit -m "fix: 競合を解決"

# 5. プッシュ
git push origin main
```

### シナリオ2: プルリクエストで競合

```bash
# 1. mainブランチの最新を取得
git checkout main
git pull origin main

# 2. 作業ブランチに戻る
git checkout feature/your-feature-name

# 3. mainをマージ
git merge main

# 4. 競合を解決（上記と同じ）
git add <競合したファイル>
git commit -m "fix: mainとの競合を解決"

# 5. プッシュ
git push origin feature/your-feature-name
```

### 競合を避けるテクニック: Rebase

```bash
# マージの代わりにrebaseを使う（履歴が綺麗になる）
git checkout feature/your-feature-name
git rebase main

# 競合があれば解決
git add <競合したファイル>
git rebase --continue

# プッシュ（force pushが必要）
git push origin feature/your-feature-name --force-with-lease
```

⚠️ **注意**: `--force-with-lease`は他の人がプッシュしていないことを確認してから使用

---

## コードレビューのプロセス

### プルリクエストの作成

1. **GitHub上でプルリクエストを作成**
   - ブランチをプッシュ後、GitHubにアクセス
   - "Compare & pull request"ボタンをクリック

2. **プルリクエストの説明を記入**
   ```markdown
   ## 変更内容
   - 動画グレースケール表示機能を追加
   - トグルボタンでカラー/グレースケールを切り替え可能
   
   ## 変更したファイル
   - frontend/app/components/PoseVisualizer.tsx
   
   ## テスト方法
   1. http://localhost にアクセス
   2. 動画をアップロード
   3. 結果ページで「カラー」ボタンをクリック
   4. 動画がグレースケールになることを確認
   
   ## スクリーンショット
   （あれば添付）
   ```

3. **レビュアーを指定**
   - チームメンバーをレビュアーに追加

4. **レビュー待ち**
   - レビューが完了するまで待つ
   - フィードバックがあれば修正

5. **マージ**
   - レビュー承認後、mainにマージ

### レビューのポイント

**レビュアーが確認すること**:
- ✅ コードが正しく動作するか
- ✅ コーディング規約に従っているか
- ✅ 不要なコメントやデバッグコードがないか
- ✅ パフォーマンスに問題がないか
- ✅ セキュリティの問題がないか

---

## よくある競合パターンと回避方法

### パターン1: 同じファイルの同じ行を編集

**シナリオ**:
- メンバーA: `PoseVisualizer.tsx`の50行目を編集
- メンバーB: `PoseVisualizer.tsx`の50行目を編集

**回避方法**:
1. 作業前にSlackで「PoseVisualizer.tsxを編集します」と宣言
2. 機能ごとにファイルを分割（コンポーネントを小さく）
3. 同じファイルを編集する場合は、時間をずらす

### パターン2: docker-compose.ymlの変更

**シナリオ**:
- メンバーA: 新しいサービスを追加
- メンバーB: 既存サービスのポート番号を変更

**回避方法**:
1. `docker-compose.yml`の変更は事前にチームで相談
2. 変更が必要な場合は、他のメンバーの作業が終わってから
3. 変更後、すぐにプッシュして他のメンバーに通知

### パターン3: データベーススキーマの変更

**シナリオ**:
- メンバーA: 新しいテーブルを追加
- メンバーB: 既存テーブルにカラムを追加

**回避方法**:
1. データベース変更は必ずチームで相談
2. マイグレーションスクリプトを作成
3. 変更後、すぐに他のメンバーに通知

### パターン4: package.jsonやrequirements.txtの変更

**シナリオ**:
- メンバーA: 新しいライブラリを追加
- メンバーB: 別のライブラリを追加

**回避方法**:
1. ライブラリ追加は事前に相談
2. 追加後、すぐにプッシュ
3. 他のメンバーに`npm install`または`pip install`を実行するよう通知

---

## 実践的なワークフロー例

### 例1: 新機能の追加（1人で完結）

```bash
# 1. 最新を取得
git checkout main
git pull origin main

# 2. ブランチ作成
git checkout -b feature/new-feature

# 3. 作業（30分）
# ... コードを編集 ...

# 4. コミット
git add .
git commit -m "feat: 新機能の基本構造を追加"

# 5. 作業（30分）
# ... さらに編集 ...

# 6. コミット
git add .
git commit -m "feat: 新機能のロジックを実装"

# 7. プッシュ
git push origin feature/new-feature

# 8. プルリクエスト作成
# GitHubでプルリクエストを作成

# 9. レビュー待ち・修正

# 10. マージ
```

### 例2: 複数人で大きな機能を分担

**機能**: Z-score問題部位の視覚的ハイライト

**分担**:
- メンバーA: データ取得ロジック（`result/[id]/page.tsx`）
- メンバーB: 描画ロジック（`PoseVisualizer.tsx`）

**ワークフロー**:

```bash
# メンバーA
git checkout -b feature/zscore-data-logic
# ... result/[id]/page.tsx を編集 ...
git commit -m "feat: Z-scoreデータ取得ロジックを追加"
git push origin feature/zscore-data-logic

# メンバーB
git checkout -b feature/zscore-drawing
# ... PoseVisualizer.tsx を編集 ...
git commit -m "feat: Z-score描画ロジックを追加"
git push origin feature/zscore-drawing

# 両方がマージされたら、統合テスト
```

---

## チーム内のコミュニケーションツール

### 推奨ツール

1. **Slack / Discord**
   - 作業開始・終了の報告
   - 質問・相談
   - プルリクエストの通知

2. **GitHub Issues**
   - タスク管理
   - バグ報告
   - 機能リクエスト

3. **GitHub Projects**
   - プロジェクト全体の進捗管理
   - カンバンボード

### コミュニケーションのテンプレート

**作業開始時**:
```
🚀 作業開始
機能: [機能名]
ファイル: [編集するファイル]
ブランチ: [ブランチ名]
予定: [完了予定時刻]
```

**作業終了時**:
```
✅ 作業完了
機能: [機能名]
ブランチ: [ブランチ名]
プルリクエスト: [URL]
レビュー依頼: @メンバー名
```

**質問時**:
```
❓ 質問
内容: [質問内容]
関連ファイル: [ファイル名]
試したこと: [試したこと]
```

---

## まとめ

### ✅ 競合を避けるための10のルール

1. ✅ 作業前に必ず`git pull origin main`
2. ✅ 機能ごとにブランチを分ける
3. ✅ 同じファイルを同時に編集しない（事前に相談）
4. ✅ こまめにコミット（30分〜1時間ごと）
5. ✅ 1日の終わりに必ずプッシュ
6. ✅ プルリクエストを活用
7. ✅ コードレビューを必ず行う
8. ✅ 設定ファイルの変更は慎重に
9. ✅ チームとのコミュニケーションを密に
10. ✅ 困ったらすぐに相談

### 🎯 最も重要なこと

**コミュニケーション > 技術**

技術的な競合は解決できますが、コミュニケーション不足による問題は避けられません。
常にチームメンバーと情報を共有し、協力して開発を進めましょう！

---

## 参考リソース

- **Git公式ドキュメント**: https://git-scm.com/doc
- **GitHub Flow**: https://guides.github.com/introduction/flow/
- **Conventional Commits**: https://www.conventionalcommits.org/

---

**Happy Collaboration! 🤝**

