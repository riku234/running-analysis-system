# Git チートシート - 競合回避のための基本コマンド

チーム開発で頻繁に使うGitコマンドのクイックリファレンスです。

---

## 🚀 作業開始時（毎回必須）

```bash
# 1. mainブランチに移動
git checkout main

# 2. 最新を取得
git pull origin main

# 3. 新しいブランチを作成
git checkout -b feature/your-feature-name
```

---

## 💾 作業中（こまめに実行）

```bash
# 変更状況を確認
git status

# 変更をステージング
git add .

# コミット
git commit -m "feat: 機能の説明"

# リモートにプッシュ
git push origin feature/your-feature-name
```

---

## 🔄 他の人の変更を取り込む

```bash
# mainブランチの最新を取得
git checkout main
git pull origin main

# 作業ブランチに戻る
git checkout feature/your-feature-name

# mainの変更を取り込む
git merge main

# または（履歴が綺麗になる）
git rebase main
```

---

## ⚠️ 競合が発生した場合

```bash
# 1. 競合ファイルを確認
git status

# 2. ファイルを開いて編集
# <<<<<<< HEAD
# あなたの変更
# =======
# 他の人の変更
# >>>>>>> branch-name

# 3. 競合を解決したらコミット
git add <競合したファイル>
git commit -m "fix: 競合を解決"

# 4. プッシュ
git push origin feature/your-feature-name
```

---

## 🔍 確認コマンド

```bash
# 現在のブランチを確認
git branch

# リモートブランチを確認
git branch -r

# コミット履歴を確認
git log --oneline

# 変更内容を確認
git diff

# 特定のファイルの変更履歴
git log --oneline <ファイル名>
```

---

## 🔙 やり直し・取り消し

```bash
# 直前のコミットを取り消し（変更は残る）
git reset --soft HEAD~1

# 直前のコミットを取り消し（変更も削除）
git reset --hard HEAD~1

# ステージングを取り消し
git reset HEAD <ファイル名>

# ファイルの変更を取り消し
git checkout -- <ファイル名>

# 変更を一時退避
git stash

# 退避した変更を復元
git stash pop
```

---

## 🌿 ブランチ操作

```bash
# ブランチを作成
git branch feature/new-feature

# ブランチを切り替え
git checkout feature/new-feature

# ブランチを作成して切り替え（上記2つを同時に）
git checkout -b feature/new-feature

# ブランチを削除（ローカル）
git branch -d feature/old-feature

# ブランチを削除（リモート）
git push origin --delete feature/old-feature

# ブランチ名を変更
git branch -m old-name new-name
```

---

## 📝 コミットメッセージの規則

```bash
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

---

## 🚨 緊急時のコマンド

```bash
# 間違えてmainに直接コミットしてしまった場合
git reset --soft HEAD~1  # コミットを取り消し
git stash                # 変更を退避
git checkout -b feature/emergency  # 新しいブランチを作成
git stash pop            # 変更を復元
git add .
git commit -m "feat: 機能の説明"
git push origin feature/emergency

# 間違えてプッシュしてしまった場合（他の人がプルする前に）
git reset --hard HEAD~1
git push origin main --force-with-lease

# ⚠️ 注意: force pushは慎重に！
```

---

## 🔧 便利なエイリアス設定

```bash
# ~/.gitconfig に追加

[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    pl = pull
    ps = push
    lg = log --oneline --graph --decorate --all
```

使用例:
```bash
git st  # git status と同じ
git co main  # git checkout main と同じ
git lg  # 綺麗なログ表示
```

---

## 📊 よく使うコマンドの組み合わせ

### 作業開始
```bash
git checkout main && git pull origin main && git checkout -b feature/new-feature
```

### 変更をコミット＆プッシュ
```bash
git add . && git commit -m "feat: 機能の説明" && git push origin feature/new-feature
```

### mainの最新を取り込む
```bash
git checkout main && git pull origin main && git checkout - && git merge main
```

---

## 🎯 毎日のワークフロー

### 朝（作業開始時）
```bash
git checkout main
git pull origin main
git checkout -b feature/todays-work
```

### 昼（進捗を保存）
```bash
git add .
git commit -m "feat: 午前中の作業を保存"
git push origin feature/todays-work
```

### 夕方（作業終了時）
```bash
git add .
git commit -m "feat: 本日の作業完了"
git push origin feature/todays-work
# GitHubでプルリクエストを作成
```

---

## 💡 ヒント

1. **コミット前に必ず`git status`で確認**
2. **プッシュ前に必ず`git log`で確認**
3. **困ったら`git status`を見る**
4. **わからなくなったらチームに相談**

---

詳細は [TEAM_COLLABORATION_GUIDE.md](./TEAM_COLLABORATION_GUIDE.md) を参照してください。

