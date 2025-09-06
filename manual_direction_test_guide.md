# 進行方向手動設定ガイド

## 🎯 **問題の検証と修正方法**

右から左の動画で符号が反転している場合、以下の手順で問題を特定・修正できます。

## 📋 **手順1: 問題の確認**

### 通常のテスト（自動検出）
```bash
# 右→左動画をアップロードして結果を確認
# もし前傾なのに負の値が出力される場合、進行方向検出に問題がある可能性
```

### 詳細ログの確認
```bash
# EC2サーバーでログを確認
ssh -i "キー.pem" ec2-user@54.206.3.155 "cd running-analysis-system && docker-compose logs feature_extraction --tail 50"

# 以下を確認:
# - 🏃 最終決定された進行方向: [結果]
# - 🔄 右→左移動のため符号反転: [角度変化]
# - 💡 理由: [補正ロジックの説明]
```

## 🔧 **手順2: 手動での進行方向設定**

問題の動画で進行方向が誤検出されている場合、環境変数で強制設定できます：

### 右→左動画の場合
```bash
# EC2サーバーに接続
ssh -i "キー.pem" ec2-user@54.206.3.155

# 環境変数を設定してサービス再起動
cd running-analysis-system
export FORCE_RUNNING_DIRECTION=right_to_left
docker-compose up -d feature_extraction

# 動画を再テスト
# → 正しい符号（前傾=正、後傾=負）が出力されるはず
```

### 左→右動画の場合
```bash
# 左→右に強制設定
export FORCE_RUNNING_DIRECTION=left_to_right
docker-compose up -d feature_extraction
```

### 自動検出に戻す場合
```bash
# 環境変数をクリア
unset FORCE_RUNNING_DIRECTION
docker-compose up -d feature_extraction
```

## 🔍 **手順3: 根本原因の特定**

### 進行方向検出が失敗する原因：
1. **フレーム数不足**: 10フレーム未満の短い動画
2. **移動量が小さい**: 閾値0.001未満の微小な移動
3. **カメラの揺れ**: 手ブレによる座標の不安定性
4. **ランナーの左右移動**: 進行方向以外の動きが大きい

### 確認方法：
```bash
# ログで以下を確認
# - フレーム数: [値]
# - 開始X座標: [値]  
# - 終了X座標: [値]
# - 移動量: [値]
# - 結果: [判定理由]
```

## ⚡ **即座の解決方法**

**今すぐ問題を解決したい場合：**

```bash
# EC2サーバーで右→左動画用の設定を適用
ssh -i "キー.pem" ec2-user@54.206.3.155 \
"cd running-analysis-system && \
export FORCE_RUNNING_DIRECTION=right_to_left && \
docker-compose up -d feature_extraction"

# この設定で右→左動画をテスト
# → 正しい角度値が出力されるはず
```

## 📊 **期待される結果**

| 動画タイプ | 設定 | 前傾 | 後傾 |
|------------|------|------|------|
| 左→右 | `left_to_right` | 正 | 負 |
| 右→左 | `right_to_left` | 正 | 負 |

## 🎉 **最終確認**

手動設定で正しい結果が得られた場合、進行方向検出ロジックの改良が必要です。
自動検出が正しく動作した場合、元の問題は解決済みです。

---

**注意**: 環境変数設定は一時的な解決策です。本格運用では自動検出の改良が推奨されます。

