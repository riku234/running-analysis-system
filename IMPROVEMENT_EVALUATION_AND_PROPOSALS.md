# 改善策の評価と追加提案

## 📋 現状の問題

1. **骨格検出の問題**: ノイズによる異常値、巨大化、滑らかでない動き
2. **サイクル検出の問題**: z_score_analysisによる周期検出が不安定

---

## 🔍 提案された3つの改善策の評価

### 策2: 【フロントエンド】描画スケールの固定（巨大化の完全防止）

#### ✅ 評価: **非常に有効**

**現状の問題点**:
- `drawKeypoints`関数では`point.x * videoWidth`で直接スケール変換
- ノイズで足が外に飛ぶと、その影響で全体のスケールが変わる可能性
- 毎フレームごとにBounding Boxを計算してスケール調整しているわけではないが、座標の正規化が不十分な場合に問題が発生

**改善策の効果**:
- ✅ 初期フレームで「体幹長」または「身長」を固定することで、ノイズの影響を最小化
- ✅ 巨大化問題の根本的な解決
- ✅ 実装が比較的簡単（フロントエンドのみ）

**実装のポイント**:
```typescript
// 初期化時にスケールを決定
const calculateInitialScale = (keypoints: KeyPoint[], width: number, height: number) => {
  // 腰から首までの距離を計算（体幹長）
  const leftHip = keypoints[23]  // 左腰
  const rightHip = keypoints[24]  // 右腰
  const leftShoulder = keypoints[11]  // 左肩
  const rightShoulder = keypoints[12]  // 右肩
  
  const hipCenterY = (leftHip.y + rightHip.y) / 2
  const shoulderCenterY = (leftShoulder.y + rightShoulder.y) / 2
  const torsoLength = Math.abs(hipCenterY - shoulderCenterY)
  
  // キャンバス高さの30-40%を体幹長として使用（固定スケール）
  const targetTorsoLength = height * 0.35
  return targetTorsoLength / torsoLength
}
```

**推奨度**: ⭐⭐⭐⭐⭐ (最優先実装)

---

### 策3: 【バックエンド】信頼度スコアによる「膝の補正」

#### ✅ 評価: **有効だが慎重に実装**

**現状の問題点**:
- MediaPipeは足を後ろに蹴り上げた時（オクルージョン）に膝の位置を見失いやすい
- 以前の物理制約の実装が逆効果だった（異常値を無理やり伸ばした）

**改善策の効果**:
- ✅ 信頼度が低い時だけ補正することで、安全に実装可能
- ✅ 膝の検出精度が向上
- ⚠️ ただし、補正ロジックが複雑になりやすい

**実装のポイント**:
```python
# visibilityが低い場合のみ補正
if landmark.visibility < 0.5:
    # 過去の良好なデータから太ももの長さを推定
    if i in thigh_length_history:
        avg_thigh_length = np.mean(thigh_length_history[i])
        # 腰の位置から膝の位置を予測
        predicted_knee_y = hip_y + avg_thigh_length
        # 予測値と検出値の重み付き平均
        corrected_y = 0.7 * predicted_knee_y + 0.3 * landmark.y
```

**注意点**:
- 補正が強すぎると、実際の動きを歪めてしまう
- 過去のデータが異常値を含む場合、補正が逆効果になる可能性

**推奨度**: ⭐⭐⭐ (慎重に実装、パラメータ調整が必要)

---

### 策4: 【比較機能】「着地」基準の同期（ゼロクロス法）

#### ✅ 評価: **非常に有効**

**現状の問題点**:
- `z_score_analysis`のピーク検出（`scipy.signal.find_peaks`）はノイズに弱い
- 極値検出は、ノイズが多いと誤検出が発生しやすい

**改善策の効果**:
- ✅ ゼロクロス法はノイズに対してより堅牢
- ✅ 「足首が腰に対する相対的な高さの平均値を下回った瞬間」は物理的に明確
- ✅ ランニングの周期検出精度が大幅に向上

**実装のポイント**:
```python
def detect_foot_strike_zero_crossing(ankle_y_coords, hip_y_coords, fps):
    """
    ゼロクロス法による着地検出
    """
    # 腰に対する相対的な高さを計算
    relative_height = ankle_y_coords - np.mean(hip_y_coords)
    mean_height = np.mean(relative_height)
    
    # 平均値を下回る瞬間（ゼロクロス）を検出
    strikes = []
    for i in range(1, len(relative_height)):
        if relative_height[i-1] > mean_height and relative_height[i] <= mean_height:
            strikes.append(i)
    
    return strikes
```

**推奨度**: ⭐⭐⭐⭐⭐ (最優先実装、サイクル検出の根本的改善)

---

## 💡 追加提案

### 策5: 【バックエンド】多フレーム平均による安定化

**問題**: 単一フレームのノイズがそのまま出力される

**解決策**: 過去Nフレーム（例: 3-5フレーム）の移動平均を計算し、異常値の影響を軽減

```python
# 過去3フレームの移動平均
if len(keypoint_history) >= 3:
    recent_x = [kp.x for kp in keypoint_history[-3:]]
    recent_y = [kp.y for kp in keypoint_history[-3:]]
    
    # 外れ値を除外して平均を計算
    filtered_x = remove_outliers(recent_x)
    filtered_y = remove_outliers(recent_y)
    
    smoothed_x = np.mean(filtered_x)
    smoothed_y = np.mean(filtered_y)
```

**推奨度**: ⭐⭐⭐⭐ (OneEuroFilterと組み合わせて効果的)

---

### 策6: 【フロントエンド】座標のクリッピング強化

**問題**: 0-1の範囲外の値が描画されることで巨大化が発生

**解決策**: 描画前に座標を0-1の範囲に強制的にクリップ

```typescript
const clampCoordinate = (value: number): number => {
  return Math.max(0, Math.min(1, value))
}

// 描画前にクリップ
const x = clampCoordinate(point.x) * videoWidth
const y = clampCoordinate(point.y) * videoHeight
```

**推奨度**: ⭐⭐⭐ (既に一部実装されている可能性があるが、強化が必要)

---

### 策7: 【バックエンド】キーポイント間の距離制約

**問題**: 物理的に不可能な距離（例: 足首が頭より上）が検出される

**解決策**: キーポイント間の距離に物理的制約を設ける

```python
# 太ももの長さは一定範囲内に収まる
MIN_THIGH_LENGTH = 0.15  # 画面の15%
MAX_THIGH_LENGTH = 0.25  # 画面の25%

hip_to_knee_dist = calculate_distance(hip, knee)
if hip_to_knee_dist < MIN_THIGH_LENGTH or hip_to_knee_dist > MAX_THIGH_LENGTH:
    # 過去の良好な値を使用
    knee = get_last_valid_knee_position()
```

**推奨度**: ⭐⭐⭐ (策3と組み合わせて効果的)

---

### 策8: 【バックエンド】検出失敗時の補間強化

**問題**: 検出失敗時に前フレームの値をそのまま使うと、動きが止まって見える

**解決策**: 過去数フレームのトレンドから補間

```python
if not landmarks_detected:
    if len(keypoint_history) >= 3:
        # 過去3フレームの速度を計算
        velocity = calculate_velocity(keypoint_history[-3:])
        # 速度に基づいて予測位置を計算
        predicted_position = keypoint_history[-1] + velocity
        keypoints = predicted_position
```

**推奨度**: ⭐⭐⭐ (検出率が低い動画で有効)

---

## 🎯 実装優先順位

### フェーズ1: 即効性のある改善（最優先）
1. **策2: 描画スケールの固定** ⭐⭐⭐⭐⭐
   - 巨大化問題の根本的解決
   - 実装が簡単
   - 即座に効果が現れる

2. **策4: ゼロクロス法による着地検出** ⭐⭐⭐⭐⭐
   - サイクル検出の根本的改善
   - 比較機能の精度向上

### フェーズ2: 精度向上（中優先）
3. **策6: 座標のクリッピング強化** ⭐⭐⭐
   - 既存のOutlier Rejectionと組み合わせて効果的

4. **策5: 多フレーム平均による安定化** ⭐⭐⭐⭐
   - OneEuroFilterと組み合わせて効果的

### フェーズ3: 高度な改善（低優先）
5. **策3: 信頼度スコアによる膝の補正** ⭐⭐⭐
   - 慎重に実装、パラメータ調整が必要

6. **策7: キーポイント間の距離制約** ⭐⭐⭐
   - 策3と組み合わせて効果的

7. **策8: 検出失敗時の補間強化** ⭐⭐⭐
   - 検出率が低い動画で有効

---

## 📝 まとめ

**最も効果的な組み合わせ**:
1. **策2（描画スケール固定）** + **策4（ゼロクロス法）** = 巨大化とサイクル検出の両方を解決
2. 既存の**Outlier Rejection** + **OneEuroFilter** + **策6（クリッピング強化）** = ノイズ対策の強化

**推奨実装順序**:
1. 策2を実装（巨大化問題の解決）
2. 策4を実装（サイクル検出の改善）
3. 策6を実装（安全性の向上）
4. その他の改善策は、効果を確認しながら段階的に実装
