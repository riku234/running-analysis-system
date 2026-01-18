# Basic認証のトラブルシューティング

## 問題: ブラウザで認証なしでアクセスできてしまう

### 原因

ブラウザが以前の認証情報をキャッシュしている可能性があります。

### 解決策（優先順位順）

#### 1. シークレット/プライベートモードで確認（最も簡単）
   - **Chrome**: `Cmd + Shift + N` (Mac) または `Ctrl + Shift + N` (Windows)
   - **Safari**: `Cmd + Shift + N` (Mac)
   - **Firefox**: `Cmd + Shift + P` (Mac) または `Ctrl + Shift + P` (Windows)
   - 新しいシークレット/プライベートウィンドウで `http://54.206.3.155/` にアクセス
   - **認証ダイアログが表示されることを確認**

#### 2. ブラウザの認証情報キャッシュをクリア
   - **Chrome**:
     1. アドレスバーに `chrome://settings/passwords` と入力
     2. 「保存されているパスワード」から該当サイトを削除
     3. または、`chrome://settings/clearBrowserData` で「保存されているパスワード」を選択して削除
   - **Safari**:
     1. 環境設定 > パスワード
     2. 該当サイトの認証情報を削除
   - **Firefox**:
     1. 設定 > プライバシーとセキュリティ > ログイン情報とパスワード
     2. 保存されているログイン情報から該当サイトを削除

#### 3. ブラウザのキャッシュを完全にクリア
   - Chrome/Safari: `Cmd + Shift + Delete` (Mac) または `Ctrl + Shift + Delete` (Windows)
   - 「キャッシュされた画像とファイル」と「保存されているパスワード」の両方を選択
   - 時間範囲を「全期間」に設定して削除

#### 4. ブラウザを完全に再起動
   - すべてのウィンドウを閉じる
   - ブラウザを完全に終了（タスクマネージャーで確認）
   - 再度起動してアクセス

### 確認方法

#### curlで確認（認証なし）
```bash
curl http://54.206.3.155/
```
**期待される結果**: 401 Unauthorized エラー

#### curlで確認（認証あり）
```bash
curl -u xebio:20251001 http://54.206.3.155/
```
**期待される結果**: HTMLが返ってくる

### 現在の設定

- **Basic認証**: 有効
- **ユーザー名**: `xebio`
- **パスワード**: `20251001`
- **設定ファイル**: `backend/api_gateway/nginx.conf`
- **パスワードファイル**: `backend/api_gateway/.htpasswd`

### 設定の確認

EC2でBasic認証が有効になっているか確認：

```bash
ssh -i "KEY_FILE" ec2-user@54.206.3.155 "cd running-analysis-system && docker-compose exec api_gateway cat /etc/nginx/nginx.conf | grep auth_basic"
```

出力に以下が含まれていることを確認：
```
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```
