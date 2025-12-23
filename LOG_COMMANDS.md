# ログ確認コマンド集

Cursor内のターミナルで使用できるコマンド集です。

## リアルタイムログ監視（推奨）

新しい動画をアップロードしながら、リアルタイムでログを確認できます：

```bash
docker compose logs -f back_view_analysis
```

## 最近のログを確認

直近のログを確認したい場合：

```bash
docker compose logs --tail=100 back_view_analysis
```

## 詳細ログのみを表示

身長比や角度の詳細ログのみを表示：

```bash
docker compose logs --tail=200 back_view_analysis | grep -E "上下動計算詳細|クロスオーバー計算詳細|背後解析完了" -A 10
```

## すべてのログを確認

全ログを確認したい場合：

```bash
docker compose logs back_view_analysis
```

## ログをクリアしてから監視

古いログをクリアして、新しいログのみを監視：

```bash
docker compose logs -f --tail=0 back_view_analysis
```

## 期待されるログ出力

新しい動画をアップロードすると、以下のような詳細ログが表示されます：

```
📏 上下動計算詳細:
   - 有効フレーム数: X
   - 平均骨格身長: X.XXXXXX (正規化座標)
   - 上下動範囲: X.XXXXXX (正規化座標)
   - 上下動比率（身長比）: X.XXXXXX

📐 クロスオーバー計算詳細:
   - 検出着地数: X
   - 左足平均角度: X.XX°
   - 右足平均角度: X.XX°
   - 最大角度: X.XX°

✅ 背後解析完了:
   📊 Hip Drop: 最大角度=X.XX°, 平均角度=X.XX°
   📊 Vertical Oscillation: 範囲=X.XXXX, 身長比=X.XXXX (X.XX%)
   📊 Crossover: 最大距離=X.XXXX, 最大角度=X.XX°, 平均角度=X.XX°, 着地数=X
```

## 使い方

1. Cursor内のターミナルを開く（Ctrl+` または Cmd+`）
2. 上記のコマンドをコピー＆ペーストして実行
3. 新しい動画をアップロードすると、リアルタイムでログが表示されます

