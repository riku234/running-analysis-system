# Basic認証の無効化について

## 問題の概要

EC2デプロイ時に、Basic認証が有効になっていると外部からアクセスできなくなり、401 Authorization Requiredエラーが発生します。

## 原因

`backend/api_gateway/nginx.conf`でBasic認証が有効になっている場合、すべてのリクエストに対して認証が要求されます。

## 解決策

`backend/api_gateway/nginx.conf`の以下の行をコメントアウトして、Basic認証を無効化します：

```nginx
# auth_basic "Restricted Access";
# auth_basic_user_file /etc/nginx/.htpasswd;
```

## 再発防止策

1. **デフォルトではBasic認証を無効化**
   - `nginx.conf`ではデフォルトでBasic認証をコメントアウト
   - 必要に応じて手動で有効化可能

2. **デプロイ前の確認チェックリスト**
   - [ ] `nginx.conf`でBasic認証がコメントアウトされているか確認
   - [ ] ローカルで`curl http://localhost/`が401を返さないか確認
   - [ ] EC2デプロイ後に`curl http://EC2_IP/`でアクセス可能か確認

3. **Basic認証が必要な場合**
   - 開発環境やステージング環境でのみ有効化
   - 本番環境（EC2）では無効化を推奨

## 確認方法

```bash
# ローカル確認
curl http://localhost/

# EC2確認
curl http://54.206.3.155/
```

正常な場合はHTMLが返り、401エラーは返りません。
