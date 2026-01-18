# EC2デプロイ前チェックリスト

## デプロイ前の必須確認事項

### 1. Basic認証の確認
- [ ] `backend/api_gateway/nginx.conf`でBasic認証がコメントアウトされているか確認
- [ ] ローカルで`curl http://localhost/`が401を返さないか確認

### 2. フロントエンドの確認
- [ ] フロントエンドのビルドが成功するか確認
- [ ] `docker-compose build frontend`がエラーなく完了するか確認

### 3. バックエンドサービスの確認
- [ ] 変更したサービスのビルドが成功するか確認
- [ ] ヘルスチェックが通るか確認

### 4. Gitの状態確認
- [ ] 変更がコミットされているか確認
- [ ] GitHubにプッシュされているか確認

## デプロイ後の確認事項

### 1. サービス状態確認
```bash
ssh -i "KEY_FILE" ec2-user@54.206.3.155 "cd running-analysis-system && docker-compose ps"
```

### 2. 外部アクセステスト
```bash
curl http://54.206.3.155/
```
- ✅ HTMLが返ってくる → 正常
- ❌ 401エラー → Basic認証が有効になっている可能性

### 3. フロントエンドアクセステスト
```bash
curl http://54.206.3.155/ | grep -i "Running Analysis System"
```

### 4. APIエンドポイントテスト
```bash
curl http://54.206.3.155/api/video_processing/status/test
```

## よくある問題と解決策

### 問題1: 401 Authorization Required
**原因**: Basic認証が有効になっている  
**解決策**: `backend/api_gateway/nginx.conf`でBasic認証をコメントアウト

### 問題2: フロントエンドが起動しない
**原因**: ビルドエラー、メモリ不足、ポート競合  
**解決策**: 
- ログを確認: `docker-compose logs frontend`
- 再ビルド: `docker-compose build frontend`
- メモリ確認: `free -h`

### 問題3: サービスが起動しない
**原因**: 依存関係の問題、ヘルスチェック失敗  
**解決策**:
- 依存サービスの状態を確認
- ヘルスチェックのタイムアウトを延長

## 再発防止策

1. **Basic認証はデフォルトで無効化**
   - `nginx.conf`では常にコメントアウト
   - 必要に応じて手動で有効化

2. **デプロイスクリプトにチェックを追加**
   - Basic認証の有効/無効を確認
   - 外部アクセステストを自動実行

3. **ドキュメントの整備**
   - デプロイ手順を明確化
   - トラブルシューティングガイドを整備
