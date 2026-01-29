# Phase 2 動作確認チェックリスト

## 確認項目

### 1. バックエンドエンドポイントの動作確認

#### 1.1 全フレーム取得
- **エンドポイント**: `GET /standard_model/keypoints`
- **期待される動作**: 101フレーム分のキーポイントデータを返す
- **確認内容**:
  - HTTPステータスコード: 200
  - `status: "success"`
  - `total_frames: 101`
  - `frames`に0-100のフレームデータが含まれている
  - 各フレームに`keypoints`（33個）と`angles`が含まれている

#### 1.2 特定フレーム取得
- **エンドポイント**: `GET /standard_model/keypoints?frame=0`
- **期待される動作**: フレーム0のキーポイントデータを返す
- **確認内容**:
  - HTTPステータスコード: 200
  - `status: "success"`
  - `frame: 0`
  - `keypoints`配列に33個の要素がある
  - 各キーポイントに`x`, `y`, `z`, `visibility`が含まれている
  - `angles`に角度データが含まれている

#### 1.3 エラーハンドリング
- **エンドポイント**: `GET /standard_model/keypoints?frame=101`
- **期待される動作**: 400エラー（フレーム番号が範囲外）
- **確認内容**:
  - HTTPステータスコード: 400
  - エラーメッセージが適切

### 2. キーポイントデータの妥当性確認

#### 2.1 キーポイント数の確認
- **確認内容**: 各フレームで33個のキーポイントが生成されているか

#### 2.2 座標値の範囲確認
- **確認内容**:
  - `x`, `y`が0.0-1.0の範囲内にあるか
  - `z`が適切な値（通常は0.0付近）か
  - `visibility`が0.0-1.0の範囲内にあるか

#### 2.3 主要キーポイントの存在確認
- **確認内容**: 以下のキーポイントが正しく生成されているか
  - 肩（left_shoulder: 11, right_shoulder: 12）
  - 腰（left_hip: 23, right_hip: 24）
  - 膝（left_knee: 25, right_knee: 26）
  - 足首（left_ankle: 27, right_ankle: 28）

#### 2.4 角度データとの整合性確認
- **確認内容**: 
  - 角度データ（体幹角度、大腿角度、下腿角度）から計算されたキーポイントが、角度と一致しているか
  - 例: 体幹角度が前傾している場合、肩の位置が適切に前傾しているか

### 3. データ構造の確認

#### 3.1 レスポンス形式の確認
- **全フレーム取得時の形式**:
```json
{
  "status": "success",
  "total_frames": 101,
  "frames": {
    "0": {
      "keypoints": [...],
      "angles": {...}
    },
    ...
  }
}
```

- **特定フレーム取得時の形式**:
```json
{
  "status": "success",
  "frame": 0,
  "keypoints": [...],
  "angles": {...}
}
```

#### 3.2 キーポイントの形式確認
- **各キーポイントの形式**:
```json
{
  "x": 0.5,
  "y": 0.5,
  "z": 0.0,
  "visibility": 0.9
}
```

## 確認方法

### 方法1: curlコマンドで確認

```bash
# 全フレーム取得
curl http://localhost:8002/standard_model/keypoints

# 特定フレーム取得（フレーム0）
curl http://localhost:8002/standard_model/keypoints?frame=0

# 特定フレーム取得（フレーム50）
curl http://localhost:8002/standard_model/keypoints?frame=50

# エラーテスト（範囲外）
curl http://localhost:8002/standard_model/keypoints?frame=101
```

### 方法2: ブラウザで確認

- `http://localhost:8002/standard_model/keypoints?frame=0`
- ブラウザの開発者ツールでレスポンスを確認

### 方法3: Pythonスクリプトで確認

```python
import requests
import json

# 全フレーム取得
response = requests.get("http://localhost:8002/standard_model/keypoints")
data = response.json()
print(f"Total frames: {data['total_frames']}")
print(f"Frame 0 keypoints count: {len(data['frames']['0']['keypoints'])}")

# 特定フレーム取得
response = requests.get("http://localhost:8002/standard_model/keypoints?frame=0")
data = response.json()
print(f"Keypoints count: {len(data['keypoints'])}")
print(f"First keypoint: {data['keypoints'][0]}")
```

## OK判定基準

✅ **Phase 2がOKと判定される条件**:

1. ✅ エンドポイントが正常にレスポンスを返す（200ステータス）
2. ✅ 全フレーム取得で101フレーム分のデータが返る
3. ✅ 特定フレーム取得で正しいフレームのデータが返る
4. ✅ 各フレームで33個のキーポイントが生成されている
5. ✅ キーポイントの座標値が0.0-1.0の範囲内にある
6. ✅ 主要キーポイント（肩、腰、膝、足首）が正しく生成されている
7. ✅ エラーハンドリングが適切に動作する（範囲外のフレーム番号で400エラー）

## 次のステップ

Phase 2がOKと判定されたら、Phase 3（フロントエンドでの描画）に進みます。
