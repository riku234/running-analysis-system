# Basic認証の認証情報

## 認証情報

**ユーザー名**: `xebio`  
**パスワード**: （.htpasswdファイルに保存されているハッシュ化されたパスワード）

## アクセス方法

### ブラウザでのアクセス
1. `http://54.206.3.155/` にアクセス
2. 認証ダイアログが表示されたら、以下の情報を入力：
   - **ユーザー名**: `xebio`
   - **パスワード**: （設定されているパスワードを入力）

### curlでのアクセス
```bash
curl -u xebio:PASSWORD http://54.206.3.155/
```

### 認証情報の確認
`.htpasswd`ファイルには以下のエントリが保存されています：
```
xebio:$apr1$vfOaLHgJ$UoiWk2S8P4.1gxcMGk9AE1
```

パスワードの平文はハッシュ化されているため、直接確認できません。  
パスワードを忘れた場合は、新しいパスワードを設定する必要があります。

## パスワードの変更方法

新しいパスワードを設定する場合：

```bash
# htpasswdコマンドで新しいパスワードを設定
htpasswd -c backend/api_gateway/.htpasswd xebio

# または、既存のファイルに追加/更新する場合（-cオプションなし）
htpasswd backend/api_gateway/.htpasswd xebio
```

その後、API Gatewayを再ビルド・再起動：
```bash
docker-compose build api_gateway
docker-compose up -d api_gateway
```
