"""
提供された座標データから標準モデルキーポイントを生成
s-motion_girl_Velocity2.sdファイルから24個の関節点を読み込み、MediaPipe形式（33個のランドマーク）に変換
"""

import numpy as np
from typing import List, Dict, Any
import os

# ファイルパス（複数のパスを試す）
def find_sd_file():
    """s-motion_girl_Velocity2.sdファイルを探す"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '../../../../s-motion_girl_Velocity2.sd'),
        '/app/s-motion_girl_Velocity2.sd',
        's-motion_girl_Velocity2.sd',
        os.path.join(os.path.dirname(__file__), '../../../s-motion_girl_Velocity2.sd'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

SD_FILE_PATH = find_sd_file()

# 提供された24個の関節点のインデックス（s-motion形式）
# 順序: 右手、右手首、右肘、右肩、左手、左手首、左肘、左肩、
#       右爪先、右母指球、右踵、右足首、右膝、右股関節、
#       左爪先、左母指球、左踵、左足首、左膝、左股関節、
#       頭頂、耳、左右肩中点＋身体重心、[24個目: 未確認、おそらく首/Neck]
KEYPOINT_INDICES_24 = {
    "Right Hand": 0,        # 右手
    "Right Wrist": 1,      # 右手首
    "Right Elbow": 2,      # 右肘
    "Right Shoulder": 3,   # 右肩
    "Left Hand": 4,        # 左手
    "Left Wrist": 5,       # 左手首
    "Left Elbow": 6,       # 左肘
    "Left Shoulder": 7,    # 左肩
    "Right Toe": 8,        # 右爪先
    "Right Ball": 9,       # 右母指球
    "Right Heel": 10,      # 右踵
    "Right Ankle": 11,     # 右足首
    "Right Knee": 12,      # 右膝
    "Right Hip": 13,       # 右股関節
    "Left Toe": 14,        # 左爪先
    "Left Ball": 15,       # 左母指球
    "Left Heel": 16,       # 左踵
    "Left Ankle": 17,      # 左足首
    "Left Knee": 18,       # 左膝
    "Left Hip": 19,        # 左股関節
    "Head Top": 20,        # 頭頂
    "Ear": 21,             # 耳
    "Body Center": 22,     # 左右肩中点＋身体重心
    "Neck": 23             # 24個目（推測: 首/Neck、または追加の関節点）
}

def load_pose_data_from_file() -> List[List[float]]:
    """
    s-motion_girl_Velocity2.sdファイルから座標データを読み込む
    
    Returns:
        101フレーム分の座標データ（各フレームは72個の値：24点 × 3座標）
    """
    try:
        with open(SD_FILE_PATH, 'r') as f:
            lines = f.readlines()
        
        # 最初の行はメタデータ（101,24,0.007300）
        # 2行目以降が座標データ
        pose_data = []
        for line in lines[1:]:  # 最初の行をスキップ
            line = line.strip()
            if not line:
                continue
            values = [float(x) for x in line.split(',')]
            if len(values) == 72:  # 24点 × 3座標 = 72
                pose_data.append(values)
        
        print(f"✅ ファイルから{len(pose_data)}フレームのデータを読み込みました")
        return pose_data
    except FileNotFoundError:
        print(f"⚠️ ファイルが見つかりません: {SD_FILE_PATH}")
        print("⚠️ フォールバック: ハードコードされたデータを使用します")
        # フォールバック: 空のリストを返す（後でエラー処理）
        return []
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {str(e)}")
        return []

def get_all_frames_bounds(pose_data: List[List[float]]) -> Dict[str, float]:
    """
    全フレームを通した座標の範囲を計算
    人体のアスペクト比を保持するため、各軸を独立に正規化する
    
    Args:
        pose_data: 全フレームの座標データ
    
    Returns:
        最小値・最大値の辞書
    """
    all_x, all_y, all_z = [], [], []
    
    for frame_data in pose_data:
        for i in range(24):  # 24個の関節点
            idx = i * 3
            if idx + 2 < len(frame_data):
                all_x.append(frame_data[idx])
                all_y.append(frame_data[idx + 1])
                all_z.append(frame_data[idx + 2])
    
    if not all_x:
        # デフォルト値
        return {
            'min_x': 0.0, 'max_x': 1.0,
            'min_y': 0.0, 'max_y': 1.0,
            'min_z': 0.0, 'max_z': 1.0
        }
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    min_z, max_z = min(all_z), max(all_z)
    
    # 各軸の範囲を計算
    range_x = max_x - min_x
    range_y = max_y - min_y
    range_z = max_z - min_z
    
    # 最大の範囲を基準にスケーリング（アスペクト比を保持）
    max_range = max(range_x, range_y, range_z)
    
    # 中央値を計算
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    return {
        'min_x': min_x,
        'max_x': max_x,
        'min_y': min_y,
        'max_y': max_y,
        'min_z': min_z,
        'max_z': max_z,
        'range_x': range_x,
        'range_y': range_y,
        'range_z': range_z,
        'max_range': max_range,
        'center_x': center_x,
        'center_y': center_y,
        'center_z': center_z
    }

def convert_to_mediapipe_format(frame_data: List[float], bounds: Dict[str, float], frame_index: int = 0, total_frames: int = 101) -> List[Dict[str, float]]:
    """
    提供された24個の関節点をMediaPipe形式（33個のランドマーク）に変換
    
    Args:
        frame_data: 72個の値（24点 × 3座標）
        bounds: 全フレームを通した座標の範囲
    
    Returns:
        33個のMediaPipeランドマーク（x, y, z, visibility）
    """
    # データを24個の点に分割
    points = []
    for i in range(24):
        idx = i * 3
        if idx + 2 < len(frame_data):
            points.append({
                'x': frame_data[idx],
                'y': frame_data[idx + 1],
                'z': frame_data[idx + 2]
            })
        else:
            # データが不足している場合はデフォルト値
            points.append({'x': 0.0, 'y': 0.0, 'z': 0.0})
    
    min_x, max_x = bounds['min_x'], bounds['max_x']
    min_y, max_y = bounds['min_y'], bounds['max_y']
    min_z, max_z = bounds['min_z'], bounds['max_z']
    max_range = bounds.get('max_range', max(max_x - min_x, max_y - min_y, max_z - min_z))
    center_x = bounds.get('center_x', (min_x + max_x) / 2)
    center_y = bounds.get('center_y', (min_y + max_y) / 2)
    center_z = bounds.get('center_z', (min_z + max_z) / 2)
    
    # 正規化関数（アスペクト比を保持）
    # 各軸を独立に正規化し、中央を0.5に配置
    # Y軸は反転（元データではYが大きいほど下、CanvasではYが小さいほど上）
    def normalize(value, min_val, max_val, center_val, max_range_val, flip_y=False):
        if max_range_val == 0:
            return 0.5
        # 中央を基準に正規化
        normalized = 0.5 + (value - center_val) / max_range_val
        # Y軸を反転（Canvas座標系に合わせる）
        if flip_y:
            normalized = 1.0 - normalized
        # 0.0-1.0の範囲にクランプ
        return max(0.0, min(1.0, normalized))
    
    # MediaPipe形式の33個のランドマークを生成
    # 座標系のマッピング（横から見た視点）:
    # - 元データのY軸（時間経過/ランニング方向）→ CanvasのX軸（左から右）
    # - 元データのZ軸（左右方向）→ CanvasのY軸（上から下、反転）
    # - 元データのX軸（前後方向/奥行き）→ 深度として扱う（2D表示では使用しない）
    # 
    # 注意: データ分析により、Y軸が時間経過（単調増加）を表していることが判明
    # Y軸の範囲: 0.542-3.565 (範囲: 3.023) → これを横方向の動きとして使用
    
    # Y軸の範囲を計算
    y_range = max_y - min_y
    
    mediapipe_keypoints = []
    
    # 0-10: 顔のランドマーク
    # 鼻（Body CenterとHead Topの中点、またはNeckを使用）
    if len(points) > KEYPOINT_INDICES_24["Neck"]:
        nose_point = points[KEYPOINT_INDICES_24["Neck"]]
    else:
        nose_x = (points[KEYPOINT_INDICES_24["Body Center"]]['x'] + points[KEYPOINT_INDICES_24["Head Top"]]['x']) / 2
        nose_y = (points[KEYPOINT_INDICES_24["Body Center"]]['y'] + points[KEYPOINT_INDICES_24["Head Top"]]['y']) / 2
        nose_z = (points[KEYPOINT_INDICES_24["Body Center"]]['z'] + points[KEYPOINT_INDICES_24["Head Top"]]['z']) / 2
        nose_point = {'x': nose_x, 'y': nose_y, 'z': nose_z}
    
    # 横から見た視点: Y軸（時間経過）→ Canvas X、Z軸（左右）→ Canvas Y（反転）
    # Y軸をX軸にマッピング（時間経過が横方向の動き）
    # Y軸の範囲を0.0-1.0に正規化
    nose_y_normalized = (nose_point['y'] - min_y) / y_range if y_range > 0 else 0.5
    nose_x = nose_y_normalized  # Y軸（時間経過）→ Canvas X（左から右）
    # Z軸をY軸にマッピング（左右方向が上下方向）
    nose_y = normalize(nose_point['z'], min_z, max_z, center_z, max_range, flip_y=True)
    # X軸は深度として保持
    nose_z = normalize(nose_point['x'], min_x, max_x, center_x, max_range, flip_y=False)
    
    # 左目（Earの左側）- Y軸をX軸にマッピング、Z軸をY軸にマッピング
    ear_y_normalized = (points[KEYPOINT_INDICES_24["Ear"]]['y'] - min_y) / y_range if y_range > 0 else 0.5
    left_eye_x = ear_y_normalized
    left_eye_y = normalize(points[KEYPOINT_INDICES_24["Ear"]]['z'] - 0.02, min_z, max_z, center_z, max_range, flip_y=True)
    left_eye_z = normalize(points[KEYPOINT_INDICES_24["Ear"]]['x'], min_x, max_x, center_x, max_range, flip_y=False)
    
    # 右目（Earの右側）- Y軸をX軸にマッピング、Z軸をY軸にマッピング
    right_eye_x = ear_y_normalized
    right_eye_y = normalize(points[KEYPOINT_INDICES_24["Ear"]]['z'] + 0.02, min_z, max_z, center_z, max_range, flip_y=True)
    right_eye_z = normalize(points[KEYPOINT_INDICES_24["Ear"]]['x'], min_x, max_x, center_x, max_range, flip_y=False)
    
    # 顔のランドマーク（簡易版）
    for i in range(11):
        if i == 0:  # 鼻
            mediapipe_keypoints.append({'x': nose_x, 'y': nose_y, 'z': nose_z, 'visibility': 0.9})
        elif i == 2:  # 左目
            mediapipe_keypoints.append({'x': left_eye_x, 'y': left_eye_y, 'z': left_eye_z, 'visibility': 0.9})
        elif i == 5:  # 右目
            mediapipe_keypoints.append({'x': right_eye_x, 'y': right_eye_y, 'z': right_eye_z, 'visibility': 0.9})
        else:
            # その他の顔のランドマークは鼻の周辺に配置
            mediapipe_keypoints.append({'x': nose_x, 'y': nose_y, 'z': nose_z, 'visibility': 0.5})
    
    # 11-12: 肩（Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    left_shoulder_y_normalized = (points[KEYPOINT_INDICES_24["Left Shoulder"]]['y'] - min_y) / y_range if y_range > 0 else 0.5
    mediapipe_keypoints.append({
        'x': left_shoulder_y_normalized,
        'y': normalize(points[KEYPOINT_INDICES_24["Left Shoulder"]]['z'], min_z, max_z, center_z, max_range, flip_y=True),
        'z': normalize(points[KEYPOINT_INDICES_24["Left Shoulder"]]['x'], min_x, max_x, center_x, max_range, flip_y=False),
        'visibility': 0.9
    })
    right_shoulder_y_normalized = (points[KEYPOINT_INDICES_24["Right Shoulder"]]['y'] - min_y) / y_range if y_range > 0 else 0.5
    mediapipe_keypoints.append({
        'x': right_shoulder_y_normalized,
        'y': normalize(points[KEYPOINT_INDICES_24["Right Shoulder"]]['z'], min_z, max_z, center_z, max_range, flip_y=True),
        'z': normalize(points[KEYPOINT_INDICES_24["Right Shoulder"]]['x'], min_x, max_x, center_x, max_range, flip_y=False),
        'visibility': 0.9
    })
    
    # ヘルパー関数: Y座標をX座標にマッピング（時間経過が横方向の動き）
    def get_x_from_y(point_y):
        y_normalized = (point_y - min_y) / y_range if y_range > 0 else 0.5
        return y_normalized
    
    # ヘルパー関数: Z座標をY座標にマッピング（左右方向が上下方向）
    def get_y_from_z(point_z):
        return normalize(point_z, min_z, max_z, center_z, max_range, flip_y=True)
    
    # ヘルパー関数: X座標を深度として保持
    def get_z_from_x(point_x):
        return normalize(point_x, min_x, max_x, center_x, max_range, flip_y=False)
    
    # 13-22: 腕（提供データから）
    # 左肘、右肘、左腕首、右腕首（Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Elbow"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Elbow"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Elbow"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Elbow"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Elbow"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Elbow"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Wrist"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Wrist"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Wrist"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Wrist"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Wrist"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Wrist"]]['x']),
        'visibility': 0.9
    })
    
    # 手の詳細ランドマーク（17-22）は簡易版
    for i in range(6):
        if i % 2 == 0:  # 左手
            mediapipe_keypoints.append({
                'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Hand"]]['y']),
                'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Hand"]]['z']),
                'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Hand"]]['x']),
                'visibility': 0.7
            })
        else:  # 右手
            mediapipe_keypoints.append({
                'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Hand"]]['y']),
                'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Hand"]]['z']),
                'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Hand"]]['x']),
                'visibility': 0.7
            })
    
    # 23-24: 腰（Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Hip"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Hip"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Hip"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Hip"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Hip"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Hip"]]['x']),
        'visibility': 0.9
    })
    
    # 25-26: 膝（Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Knee"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Knee"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Knee"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Knee"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Knee"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Knee"]]['x']),
        'visibility': 0.9
    })
    
    # 27-28: 足首（Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Ankle"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Ankle"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Ankle"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Ankle"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Ankle"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Ankle"]]['x']),
        'visibility': 0.9
    })
    
    # 29-30: かかと（提供データから、Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Heel"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Heel"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Heel"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Heel"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Heel"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Heel"]]['x']),
        'visibility': 0.9
    })
    
    # 31-32: つま先（提供データから、Y軸をX軸にマッピング、Z軸をY軸にマッピング）
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Left Toe"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Left Toe"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Left Toe"]]['x']),
        'visibility': 0.9
    })
    mediapipe_keypoints.append({
        'x': get_x_from_y(points[KEYPOINT_INDICES_24["Right Toe"]]['y']),
        'y': get_y_from_z(points[KEYPOINT_INDICES_24["Right Toe"]]['z']),
        'z': get_z_from_x(points[KEYPOINT_INDICES_24["Right Toe"]]['x']),
        'visibility': 0.9
    })
    
    return mediapipe_keypoints

def get_standard_model_keypoints_from_coordinates() -> Dict[str, Any]:
    """
    提供された座標データから標準モデルキーポイントを生成
    
    Returns:
        フレームごとのキーポイントデータ
    """
    # ファイルからデータを読み込む
    pose_data = load_pose_data_from_file()
    
    if not pose_data:
        print("❌ 座標データが読み込めませんでした")
        return {
            'status': 'error',
            'message': '座標データの読み込みに失敗しました'
        }
    
    # 全フレームを通した座標の範囲を計算
    bounds = get_all_frames_bounds(pose_data)
    print(f"📊 座標範囲: X[{bounds['min_x']:.3f}, {bounds['max_x']:.3f}], Y[{bounds['min_y']:.3f}, {bounds['max_y']:.3f}], Z[{bounds['min_z']:.3f}, {bounds['max_z']:.3f}]")
    
    frames = {}
    
    for frame_idx, frame_data in enumerate(pose_data):
        mediapipe_keypoints = convert_to_mediapipe_format(frame_data, bounds, frame_idx, len(pose_data))
        frames[str(frame_idx)] = {
            'keypoints': mediapipe_keypoints,
            'frame_number': frame_idx
        }
    
    print(f"✅ {len(frames)}フレームのキーポイントを生成しました")
    
    return {
        'status': 'success',
        'total_frames': len(frames),
        'frames': frames,
        'is_cycle': True,
        'note': 'このデータは提供された座標データから生成された1周期分です。リピートして使用してください。'
    }
