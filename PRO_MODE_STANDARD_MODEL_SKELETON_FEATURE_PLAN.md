# Proモード: 標準モデル擬似骨格表示機能の実現可能性分析

## 📋 概要

Proモードにおいて、以下の機能を実装する可能性を検討します：

1. **現状の骨格表示を非表示にする**
2. **ランナーの前方または後方に標準モデルの点を元にした擬似骨格を走らせる**

---

## ✅ 実現可能性: **高**

技術的には実現可能ですが、いくつかの課題と解決策が必要です。

---

## 🔍 現状の実装状況

### 1. Proモードの骨格表示

**ファイル**: `frontend/app/components/PoseVisualizer.tsx`

- **描画方法**: HTML5 Canvasを使用
- **描画関数**: `drawKeypoints()` (line 538-608)
- **骨格データ**: `poseData.pose_data[].keypoints` (33個のMediaPipeランドマーク)
- **表示制御**: `updateCanvas()` 関数内で `drawKeypoints()` を呼び出し

### 2. 標準モデルデータ

**ファイル**: `backend/services/analysis/app/main.py`

- **関数**: `get_event_based_standard_model()` (line 27-64)
- **データ形式**: イベント別（`right_strike`, `right_off`, `left_strike`, `left_off`）の角度データ
- **含まれる角度**:
  - 体幹角度
  - 右大腿角度
  - 右下腿角度
  - 左大腿角度
  - 左下腿角度
- **データ形式**: 各角度について `mean`（平均値）と `std`（標準偏差）のみ

---

## 🎯 実装要件

### 要件1: 現状の骨格表示を非表示にする

**難易度**: ⭐ (非常に簡単)

**実装方法**:
1. `PoseVisualizer.tsx` の `updateCanvas()` 関数内で、`drawKeypoints()` の呼び出しを条件分岐で制御
2. プロパティとして `showSkeleton: boolean` を追加し、`false` の場合は描画をスキップ
3. または、`drawKeypoints()` 関数内で早期リターン

**コード例**:
```typescript
// オプション1: プロパティで制御
interface PoseVisualizerProps {
  // ... 既存のプロパティ
  showSkeleton?: boolean  // デフォルト: true
}

// updateCanvas()内
if (showSkeleton && frameData && frameData.landmarks_detected) {
  drawKeypoints(ctx, frameData.keypoints, canvas.width, canvas.height)
}
```

**影響範囲**: 最小限（1ファイルのみ）

---

### 要件2: 標準モデルから擬似骨格を生成

**難易度**: ⭐⭐⭐⭐ (複雑)

#### 課題1: 角度データからキーポイント座標への逆算

**問題点**:
- 標準モデルは**角度データのみ**を持っている
- キーポイント座標（x, y, z）は持っていない
- 角度から座標を逆算する必要がある

**解決策**:

##### アプローチA: 基準点を設定して順次計算（推奨）

1. **基準点の設定**
   - ランナーの骨盤中心（左右の腰の中点）を基準点として使用
   - または、ランナーの現在位置を基準に、前方/後方にオフセット

2. **順次計算の流れ**
   ```
   基準点（骨盤中心）
   ↓
   体幹角度 → 肩の位置
   ↓
   大腿角度 → 膝の位置
   ↓
   下腿角度 → 足首の位置
   ↓
   その他のランドマーク（腕、顔など）
   ```

3. **計算式の例**:
   ```typescript
   // 体幹角度から肩の位置を計算
   const trunkAngleRad = Math.radians(standardModel.trunk_angle.mean)
   const shoulderY = hipY - (torsoLength * Math.cos(trunkAngleRad))
   const shoulderX = hipX + (torsoLength * Math.sin(trunkAngleRad))
   
   // 大腿角度から膝の位置を計算
   const thighAngleRad = Math.radians(standardModel.right_thigh_angle.mean)
   const kneeY = hipY + (thighLength * Math.cos(thighAngleRad))
   const kneeX = hipX + (thighLength * Math.sin(thighAngleRad))
   
   // 下腿角度から足首の位置を計算
   const shankAngleRad = Math.radians(standardModel.right_shank_angle.mean)
   const ankleY = kneeY + (shankLength * Math.cos(shankAngleRad))
   const ankleX = kneeX + (shankLength * Math.sin(shankAngleRad))
   ```

4. **必要な追加データ**:
   - **身体の各部位の長さ**（体幹、大腿、下腿、上腕、前腕など）
   - これらは標準的な人体モデルから取得するか、ランナーの実際のデータから推定

##### アプローチB: 標準モデルのキーポイントデータを事前に生成

1. **バックエンドでキーポイントデータを生成**
   - 標準モデルの角度データから、代表的なキーポイント座標を事前計算
   - イベント別に33個のランドマーク座標を保存

2. **フロントエンドで使用**
   - バックエンドからキーポイントデータを取得
   - そのまま描画に使用

**推奨**: **アプローチB**（事前計算方式）
- 計算が複雑で、リアルタイム計算は負荷が高い
- バックエンドで一度計算してキャッシュする方が効率的

#### 課題2: ランニングサイクルに合わせた動きの生成

**✅ 重要な発見**: 標準モデルには**Frame 0からFrame 100まで、101フレーム分のデータが既に存在**しています！

**ファイル**: `backend/services/feature_extraction/standard_model_complete.py`

- **データ構造**: 各フレーム（Frame_0 〜 Frame_100）に角度データが含まれている
- **含まれる角度**: 体幹角度、右大腿角度、右下腿角度、左大腿角度、左下腿角度
- **データ形式**: 各角度について平均値と標準偏差が含まれている

**解決策**:

1. **補間は不要！**
   - 101フレーム分のデータが既にあるため、補間は不要
   - フレーム単位で直接データを取得できる
   - **カクカクした動きになる心配はありません**

2. **ランニングサイクルの同期**
   - 実際のランナーの動画から、ランニングサイクルを検出
   - 標準モデルの101フレームを、実際のランニングサイクルの長さに合わせてスケーリング
   - または、標準モデルのフレームをループ再生

3. **フレーム単位の動き生成**
   ```typescript
   // 標準モデルのフレーム数を取得（101フレーム）
   const STANDARD_MODEL_FRAMES = 101
   
   // 実際のランニングサイクルの長さを取得
   const runningCycleLength = detectRunningCycleLength(poseData)
   
   // 現在のフレームに対応する標準モデルのフレームを計算
   const standardModelFrame = Math.floor(
     (currentFrame % runningCycleLength) / runningCycleLength * STANDARD_MODEL_FRAMES
   )
   
   // 標準モデルのフレームデータを取得
   const standardModelData = getStandardModelFrame(standardModelFrame)
   
   // 角度データからキーポイントを生成
   const standardKeypoints = generateKeypointsFromAngles(standardModelData)
   ```

4. **スムーズな動きの実現**
   - 101フレーム分のデータがあるため、30fpsで約3.4秒分の滑らかな動きを表現可能
   - ランニングサイクルが標準モデルより長い場合は、ループ再生
   - ランニングサイクルが標準モデルより短い場合は、時間軸を圧縮

#### 課題3: 前方/後方への配置

**問題点**:
- ランナーの前方または後方に擬似骨格を配置する必要がある
- 2D動画では深度（Z軸）情報が限定的

**解決策**:

1. **X軸オフセット**
   - ランナーの現在位置（例: 骨盤中心）を基準に、X軸方向にオフセット
   - 前方: X座標を増加（右方向）
   - 後方: X座標を減少（左方向）

2. **スケーリング**
   - 遠近感を出すために、前方/後方の骨格をスケーリング
   - 前方: 少し大きく表示
   - 後方: 少し小さく表示

3. **透明度**
   - 前方/後方の骨格を半透明にして、区別しやすくする

**コード例**:
```typescript
// ランナーの骨盤中心を取得
const runnerHipCenter = {
  x: (runnerLeftHip.x + runnerRightHip.x) / 2,
  y: (runnerLeftHip.y + runnerRightHip.y) / 2
}

// 前方/後方へのオフセット（動画幅の10%）
const offsetX = videoWidth * 0.1 * (position === 'front' ? 1 : -1)

// 標準モデルのキーポイントをオフセット
const standardKeypoints = standardModelKeypoints.map(kp => ({
  ...kp,
  x: kp.x + offsetX,
  // スケーリング（前方: 1.1倍、後方: 0.9倍）
  scale: position === 'front' ? 1.1 : 0.9
}))
```

---

## 📊 実装ステップ

### Phase 1: 骨格表示の非表示化（簡単）

1. `PoseVisualizer.tsx` に `showSkeleton` プロパティを追加
2. `updateCanvas()` で条件分岐を追加
3. Proモードの呼び出し側で `showSkeleton={false}` を設定

**見積もり**: 30分

### Phase 2: 標準モデルキーポイントデータの生成（バックエンド）

1. **新しいエンドポイントの作成**
   - `GET /api/standard-model/keypoints`
   - 標準モデルの角度データからキーポイント座標を生成

2. **キーポイント生成ロジック**
   - 身体の各部位の長さを定義（標準的な人体モデル）
   - 角度データから順次キーポイント座標を計算
   - イベント別に33個のランドマーク座標を生成

3. **フレーム単位のデータ取得**
   - **補間は不要！** 標準モデルには既に101フレーム分のデータが存在
   - Frame 0〜100の各フレームから角度データを取得
   - 角度データからキーポイント座標を生成

**見積もり**: 4-6時間

### Phase 3: フロントエンドでの擬似骨格描画

1. **標準モデルデータの取得**
   - バックエンドからキーポイントデータを取得
   - キャッシュして使用

2. **ランニングサイクルの検出**
   - 実際のランナーの動画から、ランニングサイクルを検出
   - サイクルに合わせて標準モデルの動きを同期

3. **前方/後方への配置**
   - ランナーの位置を基準に、X軸方向にオフセット
   - スケーリングと透明度を適用

4. **描画関数の追加**
   - `drawStandardModelSkeleton()` 関数を追加
   - 標準モデルのキーポイントを描画

**見積もり**: 6-8時間

### Phase 4: UI制御の追加

1. **表示位置の選択**
   - 前方/後方の切り替えボタン
   - または、両方表示のオプション

2. **表示設定**
   - 透明度の調整
   - 色の変更（例: 標準モデルは青色、ランナーは緑色）

**見積もり**: 2-3時間

---

## 🔧 技術的な詳細

### 必要な追加データ

1. **身体の各部位の長さ**（標準的な人体モデル）
   ```typescript
   const STANDARD_BODY_DIMENSIONS = {
     torsoLength: 0.3,      // 体幹の長さ（正規化座標）
     thighLength: 0.25,     // 大腿の長さ
     shankLength: 0.25,     // 下腿の長さ
     upperArmLength: 0.15,  // 上腕の長さ
     forearmLength: 0.15,   // 前腕の長さ
     // ... その他
   }
   ```

2. **標準モデルのキーポイントデータ構造**
   ```typescript
   interface StandardModelKeypoints {
     event: 'right_strike' | 'right_off' | 'left_strike' | 'left_off'
     frame: number
     keypoints: KeyPoint[]  // 33個のランドマーク
   }
   ```

### フレーム単位のデータ取得（補間不要）

**標準モデルには既に101フレーム分のデータが存在するため、補間は不要です！**

1. **フレームデータの取得**
   ```typescript
   // 標準モデルのフレームデータを取得
   function getStandardModelFrame(frameNumber: number): StandardModelFrame {
     // frameNumberは0-100の範囲
     const frameKey = `Frame_${frameNumber}`
     return standardModelData[frameKey]
   }
   
   // 標準モデルのフレームデータ構造
   interface StandardModelFrame {
     体幹角度_平均: number
     体幹角度_標準偏差: number
     右大腿角度_平均: number
     右大腿角度_標準偏差: number
     右下腿角度_平均: number
     右下腿角度_標準偏差: number
     左大腿角度_平均: number
     左大腿角度_標準偏差: number
     左下腿角度_平均: number
     左下腿角度_標準偏差: number
   }
   ```

2. **ランニングサイクルとの同期**
   ```typescript
   // 実際のランニングサイクルの長さを取得
   const runningCycleLength = detectRunningCycleLength(poseData) // 例: 60フレーム
   
   // 現在のフレームに対応する標準モデルのフレームを計算
   const currentFrame = video.currentFrame
   const cyclePosition = (currentFrame % runningCycleLength) / runningCycleLength
   const standardModelFrame = Math.floor(cyclePosition * 101) // 0-100の範囲
   
   // 標準モデルのフレームデータを取得
   const standardModelData = getStandardModelFrame(standardModelFrame)
   ```

### ランニングサイクルの検出

1. **既存のイベント検出機能を活用**
   - `backend/services/analysis/app/main.py` の `detect_foot_strikes_advanced()` を使用
   - 右足接地・離地、左足接地・離地を検出

2. **サイクルの定義**
   ```typescript
   interface RunningCycle {
     startFrame: number
     endFrame: number
     events: {
       rightStrike: number
       rightOff: number
       leftStrike: number
       leftOff: number
     }
   }
   ```

---

## ⚠️ 潜在的な課題と解決策

### 課題1: 標準モデルのキーポイントデータが不完全

**問題**: 標準モデルは主要な角度のみを持っており、すべてのランドマーク（33個）の座標を生成するには追加の情報が必要

**解決策**:
- 主要なランドマーク（体幹、脚、腕）のみを生成
- その他のランドマーク（顔、手など）は、主要なランドマークから推定
- または、標準的な人体モデルから補完

### 課題2: ランニングサイクルの同期

**問題**: 実際のランナーの動きと標準モデルの動きを同期させる必要がある

**解決策**:
- ランニングサイクルの検出精度を向上
- サイクルの開始タイミングを自動検出
- 標準モデルの101フレームを、実際のサイクル長に合わせてスケーリング
- 手動でサイクルを調整するUIを提供

**注意**: 標準モデルは101フレーム（約3.4秒@30fps）のデータなので、実際のサイクルが異なる長さの場合は時間軸を調整する必要がある

### 課題3: パフォーマンス

**問題**: リアルタイムでキーポイントを計算・描画すると、パフォーマンスが低下する可能性

**解決策**:
- バックエンドで事前計算してキャッシュ
- フロントエンドでは補間のみを実行
- Web Workersを使用して計算を並列化

---

## 📈 実現可能性の総合評価

### 技術的実現可能性: **高** ✅

- 既存の技術スタックで実現可能
- 追加のライブラリは不要
- 既存のコードベースを拡張する形で実装可能

### 実装の複雑さ: **中程度**

- Phase 1（骨格非表示）: 非常に簡単
- Phase 2-3（擬似骨格生成・描画）: 中程度の複雑さ
- Phase 4（UI制御）: 簡単

### 見積もり時間

- **最小実装**（Phase 1 + Phase 2の簡易版）: 4-6時間（補間が不要なため短縮）
- **完全実装**（全Phase）: 10-14時間（補間が不要なため短縮）

**補間が不要なため、実装時間が短縮されます！**

### 推奨アプローチ

1. **Phase 1を最初に実装**（骨格非表示）
2. **Phase 2を簡易版で実装**（主要なランドマークのみ）
3. **Phase 3を実装**（描画）
4. **Phase 4を実装**（UI制御）
5. **必要に応じて改善**（全ランドマーク対応、パフォーマンス最適化など）

---

## 🎯 次のステップ

実装を開始する場合は、以下の順序で進めることを推奨します：

1. **要件の詳細化**
   - 前方/後方のどちらに表示するか
   - 両方表示のオプションは必要か
   - 表示の色や透明度の設定

2. **プロトタイプの作成**
   - Phase 1（骨格非表示）を実装
   - 簡単な擬似骨格（主要なランドマークのみ）を表示

3. **フィードバックの収集**
   - プロトタイプを確認して、改善点を特定

4. **完全実装**
   - フィードバックを反映して、完全な実装を進める
