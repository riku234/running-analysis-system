# 骨格推定システム概要

## システム構成

### 使用技術
- **MediaPipe Pose**: Google製の骨格推定ライブラリ
- **OpenCV**: 画像前処理
- **FastAPI**: RESTful APIサービス
- **Python 3.9+**

### サービス構成
- サービス名: `pose_estimation`
- ポート: 8002
- エンドポイント: `http://pose_estimation:8002/estimate`

---

## 現在の設定パラメータ

### MediaPipe Pose設定
```python
mp_pose.Pose(
    static_image_mode=False,          # 動画モード
    model_complexity=2,               # 最高精度モデル（0=軽量, 1=標準, 2=高精度）
    enable_segmentation=False,        # セグメンテーション無効
    min_detection_confidence=0.2,     # 検出閾値（低く設定して検出率向上）
    min_tracking_confidence=0.2       # トラッキング閾値（低く設定して安定性向上）
)
```

### 検出対象
- **33個のランドマーク**（MediaPipe Pose標準）
- 主要な関節ポイント：
  - 顔: 0-10
  - 左肩: 11, 左肘: 13, 左手首: 15
  - 右肩: 12, 右肘: 14, 右手首: 16
  - 左腰: 23, 左膝: 25, 左足首: 27
  - 右腰: 24, 右膝: 26, 右足首: 28

---

## 実装されている精度向上機能

### 1. 画像前処理パイプライン

```python
# 1. 解像度向上（小さい動画の場合）
scale_factor = max(1.0, 640.0 / max(width, height))
if scale_factor > 1.0:
    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

# 2. ノイズ除去（ガウシアンブラー）
frame = cv2.GaussianBlur(frame, (3, 3), 0)

# 3. バイラテラルフィルター（エッジを保ちながらノイズ除去）
frame = cv2.bilateralFilter(frame, 5, 50, 50)

# 4. コントラスト調整（CLAHE）
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
l = clahe.apply(l)
frame = cv2.merge([l, a, b])
frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)

# 5. シャープ化（エッジ強調）
kernel = np.array([[-1, -1, -1],
                  [-1,  9, -1],
                  [-1, -1, -1]])
frame = cv2.filter2D(frame, -1, kernel * 0.15 + np.eye(3) * 0.55)
```

### 2. 左右の区別を改善する構造的制約

```python
# 左膝(25)と左足首(27)の関係チェック
if (current_keypoints[25].visibility > 0.3 and current_keypoints[27].visibility > 0.3):
    # 左足首は左膝より下（y座標が大きい）であるべき
    if current_keypoints[27].y < current_keypoints[25].y - 0.1:  # 異常な位置関係
        # 前フレームの値を使用
        if len(keypoint_history) > 0 and len(keypoint_history[-1]) > 27:
            current_keypoints[27] = keypoint_history[-1][27]

# 右膝(26)と右足首(28)の関係チェック
if (current_keypoints[26].visibility > 0.3 and current_keypoints[28].visibility > 0.3):
    # 右足首は右膝より下（y座標が大きい）であるべき
    if current_keypoints[28].y < current_keypoints[26].y - 0.1:  # 異常な位置関係
        # 前フレームの値を使用
        if len(keypoint_history) > 0 and len(keypoint_history[-1]) > 28:
            current_keypoints[28] = keypoint_history[-1][28]
```

### 3. 複数フレームの移動平均スムージング

```python
# 過去5フレームの履歴を保持
keypoint_history = []
history_size = 5

# 過去Nフレームの加重平均を計算
# 新しいフレームほど重みが大きい
for j, hist_kps in enumerate(keypoint_history):
    if i < len(hist_kps):
        weight = (j + 1) / len(keypoint_history)  # 新しいフレームほど重い
        if hist_kps[i].visibility > 0.2:  # 信頼度が低いものは除外
            weights.append(weight * hist_kps[i].visibility)
            values_x.append(hist_kps[i].x)
            values_y.append(hist_kps[i].y)
            values_z.append(hist_kps[i].z)
            visibilities.append(hist_kps[i].visibility)

# 加重平均を計算
total_weight = sum(weights)
if total_weight > 0:
    avg_x = sum(vx * w for vx, w in zip(values_x, weights)) / total_weight
    avg_y = sum(vy * w for vy, w in zip(values_y, weights)) / total_weight
    avg_z = sum(vz * w for vz, w in zip(values_z, weights)) / total_weight
    avg_visibility = max(visibilities)  # 最大信頼度を使用
```

### 4. 検出失敗時の補間

```python
# 検出失敗時は履歴から最新フレームを使用（信頼度を下げる）
if len(keypoint_history) > 0:
    landmarks_detected = True
    last_keypoints = keypoint_history[-1]
    for last_kp in last_keypoints:
        keypoints.append(KeyPoint(
            x=last_kp.x,
            y=last_kp.y,
            z=last_kp.z,
            visibility=last_kp.visibility * 0.6  # 信頼度を40%減衰
        ))
```

---

## フロントエンドでの同期処理

### スローモーション再生時の同期改善

```typescript
// requestAnimationFrameを使って高頻度更新（約60fps）
useEffect(() => {
  const updateTime = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
    animationFrameRef.current = requestAnimationFrame(updateTime)
  }
  
  if (videoUrl && videoRef.current) {
    animationFrameRef.current = requestAnimationFrame(updateTime)
  }
  
  return () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
  }
}, [videoUrl])

// フレーム番号ベースのマッチング（より正確）
const getCurrentLandmarks = () => {
  if (!poseData || poseData.length === 0) return null
  
  // フレーム番号で直接マッチング
  if (videoRef.current && poseData.length > 0) {
    const video = videoRef.current
    const fps = poseData[0].timestamp > 0 ? 1 / (poseData[1]?.timestamp - poseData[0].timestamp) : 30
    const frameNumber = Math.round(currentTime * fps)
    
    const frameMatch = poseData.find(frame => frame.frame_number === frameNumber)
    if (frameMatch) {
      return frameMatch.keypoints
    }
  }
  
  // タイムスタンプベースのマッチング（フォールバック）
  const closestFrame = poseData.reduce((prev, curr) => {
    const prevDiff = Math.abs(prev.timestamp - currentTime)
    const currDiff = Math.abs(curr.timestamp - currentTime)
    return currDiff < prevDiff ? curr : prev
  })
  
  // より厳密な閾値（0.05秒以内）
  if (Math.abs(closestFrame.timestamp - currentTime) < 0.05) {
    return closestFrame.keypoints
  }
  return null
}
```

---

## 現在の課題

### 1. 左右の区別が不十分
- 左足と右足が混同される場合がある
- 構造的制約を追加したが、まだ改善の余地がある

### 2. 骨格の動きが不自然
- 一部のフレームで骨格が大きくずれる
- スムージングを強化したが、さらなる改善が必要

### 3. 精度の限界
- MediaPipe Poseの精度限界に近づいている可能性
- より高度なモデルや手法の検討が必要かもしれない

---

## データ形式

### 入力
```json
{
  "video_path": "uploads/video.mp4",
  "confidence_threshold": 0.3
}
```

### 出力
```json
{
  "status": "success",
  "message": "骨格検出が完了しました。",
  "video_info": {
    "fps": 30.0,
    "total_frames": 900,
    "duration_seconds": 30.0,
    "width": 1920,
    "height": 1080
  },
  "pose_data": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "keypoints": [
        {
          "x": 0.5,
          "y": 0.3,
          "z": 0.0,
          "visibility": 0.95
        },
        // ... 33個のキーポイント
      ],
      "landmarks_detected": true,
      "confidence_score": 0.92
    }
  ],
  "summary": {
    "total_processed_frames": 900,
    "detected_pose_frames": 850,
    "detection_rate": 0.944,
    "average_confidence": 0.89,
    "mediapipe_landmarks_count": 33
  }
}
```

---

## 改善の履歴

### 最新の改善（2024年）
1. **モデル精度向上**: `model_complexity=1` → `2`
2. **検出閾値最適化**: `0.5` → `0.2`
3. **画像前処理強化**: 解像度向上、バイラテラルフィルター追加
4. **構造的制約追加**: 左右の区別改善
5. **複数フレームスムージング**: 過去5フレームの移動平均
6. **フロントエンド同期改善**: requestAnimationFrameによる高頻度更新

---

## 相談したいポイント

1. **左右の区別をさらに改善する方法**
   - 現在は構造的制約（膝と足首の位置関係）のみ
   - より高度な手法があるか？

2. **骨格の動きをより自然にする方法**
   - 現在は過去5フレームの移動平均を使用
   - カルマンフィルターや他の手法が有効か？

3. **MediaPipe Poseの精度限界を超える方法**
   - より高精度なモデル（例: OpenPose, AlphaPose）への移行
   - 複数モデルのアンサンブル
   - カスタムモデルの訓練

4. **リアルタイム処理の最適化**
   - 現在の処理速度と精度のバランス
   - さらなる最適化の余地

5. **特定の動き（ランニング）に特化した改善**
   - ランニング動作に特化した補正ロジック
   - ドメイン知識の活用方法

---

## ファイル構成

```
backend/services/pose_estimation/
├── app/
│   └── main.py          # メイン実装（約300行）
├── Dockerfile
└── requirements.txt     # mediapipe==0.10.7, opencv-python-headless==4.8.1.78
```

---

## 使用環境

- **Python**: 3.9+
- **MediaPipe**: 0.10.7
- **OpenCV**: 4.8.1.78
- **Docker**: コンテナ化済み
- **OS**: Linux (Dockerコンテナ内)

---

## パフォーマンス

- **処理速度**: 約30fpsの動画をリアルタイム処理可能
- **メモリ使用量**: 動画サイズに依存（通常500MB-2GB）
- **CPU使用率**: 高（model_complexity=2のため）
- **検出率**: 約94%（動画の品質に依存）

---

## 今後の検討事項

1. GPU加速の検討（CUDA対応）
2. より軽量なモデルとの精度比較
3. カスタムモデルの訓練
4. 複数モデルのアンサンブル
5. リアルタイム処理の最適化

