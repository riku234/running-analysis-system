"""
標準モデルからキーポイント座標を生成するモジュール
角度データから33個のMediaPipeランドマーク座標を計算
"""

import numpy as np
import math
from typing import Dict, List, Any, Optional

# MediaPipe Pose Landmark インデックス
LANDMARK_INDICES = {
    "nose": 0,
    "left_eye_inner": 1,
    "left_eye": 2,
    "left_eye_outer": 3,
    "right_eye_inner": 4,
    "right_eye": 5,
    "right_eye_outer": 6,
    "left_ear": 7,
    "right_ear": 8,
    "mouth_left": 9,
    "mouth_right": 10,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32
}

# 標準的な人体の各部位の長さ（正規化座標、身長1.0を基準）
STANDARD_BODY_DIMENSIONS = {
    "torso_length": 0.3,      # 体幹の長さ（腰から肩まで）
    "thigh_length": 0.25,     # 大腿の長さ
    "shank_length": 0.25,     # 下腿の長さ
    "upper_arm_length": 0.15, # 上腕の長さ
    "forearm_length": 0.15,   # 前腕の長さ
    "head_radius": 0.05,      # 頭の半径
    "shoulder_width": 0.2,    # 肩幅
    "hip_width": 0.15,        # 骨盤幅
    "foot_length": 0.1        # 足の長さ
}

def generate_keypoints_from_angles(
    frame_data: Dict[str, float],
    base_x: float = 0.5,
    base_y: float = 0.5
) -> List[Dict[str, float]]:
    """
    角度データから33個のMediaPipeランドマーク座標を生成
    
    Args:
        frame_data: フレームの角度データ
            - 体幹角度_平均 (trunk_angle)
            - 右大腿角度_平均 (right_thigh_angle)
            - 右下腿角度_平均 (right_shank_angle)
            - 左大腿角度_平均 (left_thigh_angle)
            - 左下腿角度_平均 (left_shank_angle)
        base_x: 基準点のX座標（骨盤中心、デフォルト: 0.5）
        base_y: 基準点のY座標（骨盤中心、デフォルト: 0.5）
    
    Returns:
        List[Dict]: 33個のキーポイント（x, y, z, visibility）
    """
    # 角度データを取得（キー名のバリエーションに対応）
    trunk_angle = frame_data.get("体幹角度_平均") or frame_data.get("trunk_angle") or 0.0
    right_thigh_angle = frame_data.get("右大腿角度_平均") or frame_data.get("right_thigh_angle") or 0.0
    right_shank_angle = frame_data.get("右下腿角度_平均") or frame_data.get("right_shank_angle") or 0.0
    left_thigh_angle = frame_data.get("左大腿角度_平均") or frame_data.get("left_thigh_angle") or 0.0
    left_shank_angle = frame_data.get("左下腿角度_平均") or frame_data.get("left_shank_angle") or 0.0
    
    # 角度をラジアンに変換
    trunk_rad = math.radians(trunk_angle)
    right_thigh_rad = math.radians(right_thigh_angle)
    right_shank_rad = math.radians(right_shank_angle)
    left_thigh_rad = math.radians(left_thigh_angle)
    left_shank_rad = math.radians(left_shank_angle)
    
    # 33個のキーポイントを初期化
    keypoints = [None] * 33
    
    # 基準点: 骨盤中心（腰の中点）
    hip_center_x = base_x
    hip_center_y = base_y
    
    # 体幹角度から肩の中心を計算
    torso_length = STANDARD_BODY_DIMENSIONS["torso_length"]
    shoulder_center_x = hip_center_x + torso_length * math.sin(trunk_rad)
    shoulder_center_y = hip_center_y - torso_length * math.cos(trunk_rad)
    
    # 肩幅から左右の肩を計算
    shoulder_width = STANDARD_BODY_DIMENSIONS["shoulder_width"]
    left_shoulder_x = shoulder_center_x - shoulder_width / 2
    left_shoulder_y = shoulder_center_y
    right_shoulder_x = shoulder_center_x + shoulder_width / 2
    right_shoulder_y = shoulder_center_y
    
    # 骨盤幅から左右の腰を計算
    hip_width = STANDARD_BODY_DIMENSIONS["hip_width"]
    left_hip_x = hip_center_x - hip_width / 2
    left_hip_y = hip_center_y
    right_hip_x = hip_center_x + hip_width / 2
    right_hip_y = hip_center_y
    
    # 頭部（肩の中心から上に配置）
    head_radius = STANDARD_BODY_DIMENSIONS["head_radius"]
    nose_x = shoulder_center_x
    nose_y = shoulder_center_y - head_radius
    
    # 右脚の計算
    thigh_length = STANDARD_BODY_DIMENSIONS["thigh_length"]
    right_knee_x = right_hip_x + thigh_length * math.sin(right_thigh_rad)
    right_knee_y = right_hip_y + thigh_length * math.cos(right_thigh_rad)
    
    shank_length = STANDARD_BODY_DIMENSIONS["shank_length"]
    right_ankle_x = right_knee_x + shank_length * math.sin(right_shank_rad)
    right_ankle_y = right_knee_y + shank_length * math.cos(right_shank_rad)
    
    # 左脚の計算
    left_knee_x = left_hip_x + thigh_length * math.sin(left_thigh_rad)
    left_knee_y = left_hip_y + thigh_length * math.cos(left_thigh_rad)
    
    left_ankle_x = left_knee_x + shank_length * math.sin(left_shank_rad)
    left_ankle_y = left_knee_y + shank_length * math.cos(left_shank_rad)
    
    # 腕の計算（簡易版：自然な位置に配置）
    upper_arm_length = STANDARD_BODY_DIMENSIONS["upper_arm_length"]
    forearm_length = STANDARD_BODY_DIMENSIONS["forearm_length"]
    
    # 右腕（簡易版：体側に沿って配置）
    right_elbow_x = right_shoulder_x + upper_arm_length * 0.3
    right_elbow_y = right_shoulder_y + upper_arm_length * 0.5
    right_wrist_x = right_elbow_x + forearm_length * 0.3
    right_wrist_y = right_elbow_y + forearm_length * 0.5
    
    # 左腕（簡易版：体側に沿って配置）
    left_elbow_x = left_shoulder_x - upper_arm_length * 0.3
    left_elbow_y = left_shoulder_y + upper_arm_length * 0.5
    left_wrist_x = left_elbow_x - forearm_length * 0.3
    left_wrist_y = left_elbow_y + forearm_length * 0.5
    
    # 足の計算
    foot_length = STANDARD_BODY_DIMENSIONS["foot_length"]
    right_heel_x = right_ankle_x
    right_heel_y = right_ankle_y + foot_length * 0.2
    right_foot_index_x = right_ankle_x + foot_length
    right_foot_index_y = right_ankle_y
    
    left_heel_x = left_ankle_x
    left_heel_y = left_ankle_y + foot_length * 0.2
    left_foot_index_x = left_ankle_x + foot_length
    left_foot_index_y = left_ankle_y
    
    # キーポイントを設定
    def set_keypoint(idx: int, x: float, y: float, z: float = 0.0, visibility: float = 0.9):
        if 0 <= idx < 33:
            keypoints[idx] = {
                "x": max(0.0, min(1.0, x)),  # 0-1の範囲にクランプ
                "y": max(0.0, min(1.0, y)),  # 0-1の範囲にクランプ
                "z": z,
                "visibility": visibility
            }
    
    # 頭部
    set_keypoint(LANDMARK_INDICES["nose"], nose_x, nose_y)
    set_keypoint(LANDMARK_INDICES["left_eye"], nose_x - 0.02, nose_y - 0.01)
    set_keypoint(LANDMARK_INDICES["right_eye"], nose_x + 0.02, nose_y - 0.01)
    set_keypoint(LANDMARK_INDICES["left_ear"], nose_x - 0.03, nose_y)
    set_keypoint(LANDMARK_INDICES["right_ear"], nose_x + 0.03, nose_y)
    set_keypoint(LANDMARK_INDICES["mouth_left"], nose_x - 0.01, nose_y + 0.02)
    set_keypoint(LANDMARK_INDICES["mouth_right"], nose_x + 0.01, nose_y + 0.02)
    
    # 肩
    set_keypoint(LANDMARK_INDICES["left_shoulder"], left_shoulder_x, left_shoulder_y)
    set_keypoint(LANDMARK_INDICES["right_shoulder"], right_shoulder_x, right_shoulder_y)
    
    # 腕
    set_keypoint(LANDMARK_INDICES["left_elbow"], left_elbow_x, left_elbow_y)
    set_keypoint(LANDMARK_INDICES["right_elbow"], right_elbow_x, right_elbow_y)
    set_keypoint(LANDMARK_INDICES["left_wrist"], left_wrist_x, left_wrist_y)
    set_keypoint(LANDMARK_INDICES["right_wrist"], right_wrist_x, right_wrist_y)
    
    # 手（簡易版：手首の近くに配置）
    set_keypoint(LANDMARK_INDICES["left_pinky"], left_wrist_x - 0.01, left_wrist_y)
    set_keypoint(LANDMARK_INDICES["right_pinky"], right_wrist_x + 0.01, right_wrist_y)
    set_keypoint(LANDMARK_INDICES["left_index"], left_wrist_x - 0.01, left_wrist_y - 0.01)
    set_keypoint(LANDMARK_INDICES["right_index"], right_wrist_x + 0.01, right_wrist_y - 0.01)
    set_keypoint(LANDMARK_INDICES["left_thumb"], left_wrist_x, left_wrist_y + 0.01)
    set_keypoint(LANDMARK_INDICES["right_thumb"], right_wrist_x, right_wrist_y + 0.01)
    
    # 腰
    set_keypoint(LANDMARK_INDICES["left_hip"], left_hip_x, left_hip_y)
    set_keypoint(LANDMARK_INDICES["right_hip"], right_hip_x, right_hip_y)
    
    # 脚
    set_keypoint(LANDMARK_INDICES["left_knee"], left_knee_x, left_knee_y)
    set_keypoint(LANDMARK_INDICES["right_knee"], right_knee_x, right_knee_y)
    set_keypoint(LANDMARK_INDICES["left_ankle"], left_ankle_x, left_ankle_y)
    set_keypoint(LANDMARK_INDICES["right_ankle"], right_ankle_x, right_ankle_y)
    set_keypoint(LANDMARK_INDICES["left_heel"], left_heel_x, left_heel_y)
    set_keypoint(LANDMARK_INDICES["right_heel"], right_heel_x, right_heel_y)
    set_keypoint(LANDMARK_INDICES["left_foot_index"], left_foot_index_x, left_foot_index_y)
    set_keypoint(LANDMARK_INDICES["right_foot_index"], right_foot_index_x, right_foot_index_y)
    
    # その他のランドマーク（簡易版：近くのポイントから推定）
    set_keypoint(LANDMARK_INDICES["left_eye_inner"], nose_x - 0.015, nose_y - 0.01)
    set_keypoint(LANDMARK_INDICES["left_eye_outer"], nose_x - 0.025, nose_y - 0.01)
    set_keypoint(LANDMARK_INDICES["right_eye_inner"], nose_x + 0.015, nose_y - 0.01)
    set_keypoint(LANDMARK_INDICES["right_eye_outer"], nose_x + 0.025, nose_y - 0.01)
    
    # Noneのキーポイントをデフォルト値で埋める
    for i in range(33):
        if keypoints[i] is None:
            keypoints[i] = {
                "x": 0.5,
                "y": 0.5,
                "z": 0.0,
                "visibility": 0.0
            }
    
    return keypoints
