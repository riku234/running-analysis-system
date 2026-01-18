# フロントエンドサーバー再起動手順

## 方法1: Docker Composeを使用する場合

```bash
# プロジェクトルートで実行
docker compose restart frontend
```

または、完全に再ビルドする場合：

```bash
# フロントエンドを停止して再ビルド
docker compose stop frontend
docker compose build frontend
docker compose up -d frontend
```

## 方法2: 直接Next.js開発サーバーを起動している場合

### 現在のサーバーを停止
1. 開発サーバーが起動しているターミナルで `Ctrl+C` を押して停止

### サーバーを再起動
```bash
# フロントエンドディレクトリに移動
cd frontend

# .nextフォルダを削除（キャッシュクリア）
rm -rf .next

# 開発サーバーを起動
npm run dev
```

または、yarnを使用している場合：

```bash
cd frontend
rm -rf .next
yarn dev
```

## 方法3: ブラウザのキャッシュをクリア

サーバーを再起動しても変更が反映されない場合：

1. **ハードリロード**: 
   - Mac: `Cmd + Shift + R`
   - Windows/Linux: `Ctrl + Shift + R`

2. **開発者ツールを使用**:
   - `F12` または `Cmd + Option + I` (Mac) で開発者ツールを開く
   - ネットワークタブで「Disable cache」にチェックを入れる
   - ページをリロード

## 確認事項

再起動後、以下の変更が反映されているか確認してください：

- ✅ 1枚目（Step 0）にスコアと指標の説明が統合されている
- ✅ 角度基準ページが削除されている（Step 3がドリルページになっている）
- ✅ ページ数が5ページになっている（プログレスバーで確認）
- ✅ 動画が再生される（コンソールに詳細なログが表示される）
