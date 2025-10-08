# 🐛 バグ修正サマリー（2025-10-08）

## 発生していた問題

1. **アドバイスカードが表示されない**
2. **Z値分析がAPI経由に戻ってしまった（即座に表示されない）**

---

## 根本原因

### 問題1: アドバイス生成エラー

**原因**: `backend/services/advice_generation/app/main.py` の932行目で、Gemini APIのレスポンスに対して**安全性チェックなしで直接 `response.text` にアクセス**していた。

```python
# ❌ 問題のコード（932行目）
response = current_model.generate_content(prompt)
ai_response = response.text.strip()  # finish_reason=2の場合エラー
```

Gemini APIが安全性フィルター（`finish_reason=2`）を発動した場合、`response.text`にアクセスすると以下のエラーが発生：

```
ValueError: The `response.text` quick accessor requires the response to contain a valid `Part`, 
but none were returned. The candidate's finish_reason is 2.
```

### 問題2: Z値分析が即座に表示されない

**原因**: EC2デプロイ時に**frontendとvideo_processingサービスが古いまま**だった。

- `advice_generation`のみを再ビルド・再起動
- `frontend`と`video_processing`は23分前の古いバージョンのまま稼働
- 結果として、Z値データの`localStorage`保存機能が反映されていなかった

---

## 実施した修正

### 修正1: Gemini APIレスポンスの安全な処理

**ファイル**: `backend/services/advice_generation/app/main.py`

**変更内容**:
1. `response.text`への直接アクセスを削除
2. リトライロジックに500エラーハンドリングを追加
3. レスポンス検証で`finish_reason`を先にチェック

```python
# ✅ 修正後のコード
for attempt in range(max_retries):
    try:
        response = current_model.generate_content(prompt)
        print(f"   📨 Gemini応答受信: {type(response)}")
        break
    except Exception as api_error:
        error_str = str(api_error)
        if "429" in error_str or "quota" in error_str.lower():
            # レート制限処理
            ...
        elif "500" in error_str or "InternalServerError" in error_str:
            # 内部エラー処理（新規追加）
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"   ⏳ Gemini API内部エラー、{wait_time}秒待機後にリトライ ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                response = None
                break
        else:
            response = None
            break

# レスポンスの検証（finish_reasonを先にチェック）
if not response:
    ai_response = ""
elif response.candidates:
    candidate = response.candidates[0]
    if candidate.finish_reason == 2:  # SAFETY
        ai_response = "今回の分析結果を参考に、基本的なフォーム改善を心がけましょう。"
    elif hasattr(response, 'text') and response.text:
        ai_response = response.text.strip()
    else:
        ai_response = ""
```

### 修正2: 全サービスの完全デプロイ

**実施内容**:
1. `frontend`、`video_processing`、`advice_generation`を全て再ビルド
2. `--force-recreate`オプションで強制的にコンテナを再作成
3. `api_gateway`を再起動して接続をリフレッシュ

```bash
# EC2で実行
git pull origin main
docker-compose build frontend video_processing advice_generation
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate frontend video_processing advice_generation
docker-compose restart api_gateway
```

---

## 修正後の動作

### ✅ 正常に動作する機能

1. **アドバイスカードの表示**
   - Gemini APIが安全性フィルターを発動しても、フォールバックメッセージを表示
   - 500エラー時も適切にリトライ

2. **Z値分析の即座表示**
   - アップロード時に`z_score_analysis`が`localStorage`に保存される
   - 結果画面で即座に表示される（API呼び出しなし）

3. **統合アドバイスの生成**
   - 個別課題の詳細解説が正しく生成される
   - プロコーチ視点のアドバイスと統合される

---

## 再発防止策

### 1. デプロイ手順の標準化

今後のデプロイでは、**常に全サービスを再ビルド・再作成**する：

```bash
# 推奨デプロイコマンド
cd ~/running-analysis-system
git pull origin main
docker-compose build  # 全サービスをビルド
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
docker-compose restart api_gateway
```

### 2. Gemini APIエラーハンドリングの強化

- ✅ `finish_reason`の事前チェック
- ✅ 500エラーのリトライロジック
- ✅ `response.text`への安全なアクセス

### 3. デプロイ後の確認項目

1. 全コンテナが最新のタイムスタンプで起動しているか確認
   ```bash
   docker-compose ps
   ```

2. 各サービスのログでエラーがないか確認
   ```bash
   docker-compose logs frontend --tail 20
   docker-compose logs video_processing --tail 20
   docker-compose logs advice_generation --tail 20
   ```

3. 実際に動画をアップロードして動作確認

---

## Git コミット履歴

```
af8e459 - Fix response.text access in integrated advice generation - add proper error handling for finish_reason=2
21413aa - Fix Gemini API model name and improve error handling
```

---

## 確認済み環境

- ✅ ローカル環境（macOS）
- ✅ EC2本番環境（Amazon Linux 2023）

---

## 連絡先

問題が再発した場合は、このドキュメントを参照して以下を確認してください：

1. 全サービスが最新版か？（`docker-compose ps`でCREATED時刻を確認）
2. Gemini APIのログにエラーがないか？
3. `localStorage`にデータが保存されているか？（ブラウザの開発者ツールで確認）
