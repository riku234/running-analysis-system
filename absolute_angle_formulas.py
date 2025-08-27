# =============================================================================
# ランニングフォーム解析：絶対角度計算式（新仕様）
# 鉛直軸を基準とした体幹・大腿・下腿の角度計算
# =============================================================================

import numpy as np
import math
from typing import Optional, List, Dict

class KeyPoint:
    def __init__(self, x: float, y: float, z: float, visibility: float):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

# MediaPipeランドマークのインデックス定義
LANDMARK_INDICES = {
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28
}

# =============================================================================
# 基本計算関数：ベクトルと鉛直軸の角度
# =============================================================================

def calculate_absolute_angle_with_vertical(vector: np.ndarray, forward_positive: bool = True) -> Optional[float]:
    """
    ベクトルと鉛直軸がなす角度を計算する
    
    Args:
        vector: 対象ベクトル [x, y]
        forward_positive: Trueの場合、前方への傾きを正とする
                          Falseの場合、後方への傾きを正とする
    
    Returns:
        角度（度数法、-180～+180）または None
    
    数学的根拠:
        1. ベクトルの正規化: v_norm = v / |v|
        2. 鉛直軸との内積: cos(θ) = v_norm · [0, 1] = v_norm_y
        3. 角度計算: θ = arccos(cos(θ))
        4. 符号判定: x < 0 なら θ = -θ
        5. 度数変換: θ_deg = θ × (180/π)
    """
    try:
        # ベクトルの長さをチェック
        length = np.linalg.norm(vector)
        if length == 0:
            return None
        
        # 鉛直軸（下向き）: [0, 1] （画像座標系では下がy正方向）
        vertical_vector = np.array([0, 1])
        
        # ベクトルを正規化
        normalized_vector = vector / length
        
        # 内積を使って角度を計算
        cos_angle = np.dot(normalized_vector, vertical_vector)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # ラジアンで角度を計算
        angle_rad = np.arccos(cos_angle)
        
        # x成分の符号で左右を判定
        if vector[0] < 0:  # 左方向（後方）
            angle_rad = -angle_rad
        
        # 度数法に変換
        angle_deg = np.degrees(angle_rad)
        
        # forward_positiveがFalseの場合は符号を反転
        if not forward_positive:
            angle_deg = -angle_deg
        
        return angle_deg
        
    except Exception:
        return None

# =============================================================================
# 1. 体幹角度計算
# =============================================================================

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算する
    
    定義: 体幹ベクトル（股関節中点→肩中点）と鉛直軸がなす角度
    正: 前傾、負: 後傾
    
    計算手順:
        1. 左右の肩の中点を計算
        2. 左右の股関節の中点を計算  
        3. 体幹ベクトル = 肩中点 - 股関節中点
        4. 鉛直軸との角度を計算（前傾を正とする）
    """
    try:
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        
        # すべてのキーポイントが有効か確認
        if any(kp.visibility < 0.5 for kp in [left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        # 肩の中心点と股関節の中心点を計算
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        
        # 体幹ベクトル（股関節中点→肩中点）
        trunk_vector = np.array([shoulder_center_x - hip_center_x, shoulder_center_y - hip_center_y])
        
        # 絶対角度を計算（前傾を正とする）
        return calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=True)
        
    except Exception:
        return None

# =============================================================================
# 2. 大腿角度計算
# =============================================================================

def calculate_thigh_angle(hip: KeyPoint, knee: KeyPoint, side: str) -> Optional[float]:
    """
    大腿角度を計算する
    
    定義: 大腿ベクトル（股関節→膝）と鉛直軸がなす角度
    正: 膝が股関節より後方、負: 膝が股関節より前方
    
    計算手順:
        1. 大腿ベクトル = 膝座標 - 股関節座標
        2. 鉛直軸との角度を計算（後方を正とする）
    """
    try:
        # キーポイントの有効性を確認
        if hip.visibility < 0.5 or knee.visibility < 0.5:
            return None
        
        # 大腿ベクトル（股関節→膝）
        thigh_vector = np.array([knee.x - hip.x, knee.y - hip.y])
        
        # 絶対角度を計算（後方を正とする）
        return calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        
    except Exception:
        return None

# =============================================================================
# 3. 下腿角度計算
# =============================================================================

def calculate_lower_leg_angle(knee: KeyPoint, ankle: KeyPoint, side: str) -> Optional[float]:
    """
    下腿角度を計算する
    
    定義: 下腿ベクトル（膝→足首）と鉛直軸がなす角度
    正: 足首が膝より後方、負: 足首が膝より前方
    
    計算手順:
        1. 下腿ベクトル = 足首座標 - 膝座標
        2. 鉛直軸との角度を計算（後方を正とする）
    """
    try:
        # キーポイントの有効性を確認
        if knee.visibility < 0.5 or ankle.visibility < 0.5:
            return None
        
        # 下腿ベクトル（膝→足首）
        lower_leg_vector = np.array([ankle.x - knee.x, ankle.y - knee.y])
        
        # 絶対角度を計算（後方を正とする）
        return calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=False)
        
    except Exception:
        return None

# =============================================================================
# 統合関数：1フレームから全絶対角度を抽出
# =============================================================================

def extract_absolute_angles_from_frame(keypoints: List[KeyPoint]) -> Dict[str, Optional[float]]:
    """
    1フレームから新仕様の絶対角度を抽出する
    
    Returns:
        Dict[str, Optional[float]]: 5つの絶対角度
        - trunk_angle: 体幹角度
        - left_thigh_angle: 左大腿角度
        - right_thigh_angle: 右大腿角度
        - left_lower_leg_angle: 左下腿角度
        - right_lower_leg_angle: 右下腿角度
    """
    angles = {
        'trunk_angle': None,
        'left_thigh_angle': None,
        'right_thigh_angle': None,
        'left_lower_leg_angle': None,
        'right_lower_leg_angle': None
    }
    
    try:
        # ① 体幹角度
        angles['trunk_angle'] = calculate_trunk_angle(keypoints)
        
        # ② 大腿角度（左右）
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        angles['left_thigh_angle'] = calculate_thigh_angle(left_hip, left_knee, 'left')
        
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        angles['right_thigh_angle'] = calculate_thigh_angle(right_hip, right_knee, 'right')
        
        # ③ 下腿角度（左右）
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        angles['left_lower_leg_angle'] = calculate_lower_leg_angle(left_knee, left_ankle, 'left')
        
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        angles['right_lower_leg_angle'] = calculate_lower_leg_angle(right_knee, right_ankle, 'right')
        
    except (IndexError, KeyError):
        # キーポイントが不足している場合はすべてNoneを返す
        for key in angles.keys():
            angles[key] = None
    
    return angles

# =============================================================================
# 実際の計算例（3.00秒時点のデータ）
# =============================================================================

def demonstrate_calculation():
    """実際のキーポイントデータを使った計算例"""
    
    print("=" * 80)
    print("絶対角度計算の実例（3.00秒時点のデータ）")
    print("=" * 80)
    
    # サンプルキーポイントデータ（実際の解析結果）
    sample_keypoints = [None] * 33
    
    # 必要なキーポイントのみ定義
    sample_keypoints[11] = KeyPoint(0.452, 0.248, -0.035, 0.92)  # left_shoulder
    sample_keypoints[12] = KeyPoint(0.548, 0.251, -0.028, 0.89)  # right_shoulder
    sample_keypoints[23] = KeyPoint(0.468, 0.485, -0.015, 0.94)  # left_hip
    sample_keypoints[24] = KeyPoint(0.532, 0.488, -0.012, 0.91)  # right_hip
    sample_keypoints[25] = KeyPoint(0.478, 0.652, 0.045, 0.96)   # left_knee
    sample_keypoints[26] = KeyPoint(0.522, 0.655, 0.048, 0.93)   # right_knee
    sample_keypoints[27] = KeyPoint(0.485, 0.815, 0.125, 0.88)   # left_ankle
    sample_keypoints[28] = KeyPoint(0.515, 0.818, 0.128, 0.85)   # right_ankle
    
    print("\n【入力データ】")
    print("左肩:   (0.452, 0.248)")
    print("右肩:   (0.548, 0.251)")
    print("左股関節: (0.468, 0.485)")
    print("右股関節: (0.532, 0.488)")
    print("左膝:   (0.478, 0.652)")
    print("右膝:   (0.522, 0.655)")
    print("左足首: (0.485, 0.815)")
    print("右足首: (0.515, 0.818)")
    
    # 詳細計算手順を表示
    print("\n【計算手順詳細】")
    
    # 1. 体幹角度の計算
    print("\n1. 体幹角度の計算:")
    shoulder_x = (0.452 + 0.548) / 2
    shoulder_y = (0.248 + 0.251) / 2
    hip_x = (0.468 + 0.532) / 2
    hip_y = (0.485 + 0.488) / 2
    
    print(f"   肩中点:     ({shoulder_x:.3f}, {shoulder_y:.3f})")
    print(f"   股関節中点: ({hip_x:.3f}, {hip_y:.3f})")
    
    trunk_vector_x = shoulder_x - hip_x
    trunk_vector_y = shoulder_y - hip_y
    print(f"   体幹ベクトル: ({trunk_vector_x:.3f}, {trunk_vector_y:.3f})")
    
    # 2. 右大腿角度の計算
    print("\n2. 右大腿角度の計算:")
    thigh_vector_x = 0.522 - 0.532
    thigh_vector_y = 0.655 - 0.488
    print(f"   大腿ベクトル: ({thigh_vector_x:.3f}, {thigh_vector_y:.3f})")
    
    # 3. 右下腿角度の計算
    print("\n3. 右下腿角度の計算:")
    lower_leg_vector_x = 0.515 - 0.522
    lower_leg_vector_y = 0.818 - 0.655
    print(f"   下腿ベクトル: ({lower_leg_vector_x:.3f}, {lower_leg_vector_y:.3f})")
    
    # 絶対角度を計算
    angles = extract_absolute_angles_from_frame(sample_keypoints)
    
    print("\n【絶対角度計算結果】")
    print("-" * 50)
    angle_names = {
        'trunk_angle': '体幹角度',
        'left_thigh_angle': '左大腿角度',
        'right_thigh_angle': '右大腿角度',
        'left_lower_leg_angle': '左下腿角度',
        'right_lower_leg_angle': '右下腿角度'
    }
    
    for angle_key, angle_name in angle_names.items():
        if angles[angle_key] is not None:
            print(f"{angle_name:12}: {angles[angle_key]:7.1f}°")
        else:
            print(f"{angle_name:12}: 計算不可")
    
    print("\n【角度の意味】")
    print("• 体幹角度:  正=前傾, 負=後傾")
    print("• 大腿角度:  正=後方, 負=前方")
    print("• 下腿角度:  正=後方, 負=前方")
    
    return angles

# =============================================================================
# 簡潔版の計算関数
# =============================================================================

def simple_angle_calculation(vector_x: float, vector_y: float, forward_positive: bool = True) -> Optional[float]:
    """
    簡潔版：ベクトルと鉛直軸の角度計算
    
    Args:
        vector_x: ベクトルのx成分
        vector_y: ベクトルのy成分
        forward_positive: 前方を正とするかどうか
    
    Returns:
        角度（度数法）
    """
    # ベクトル長さ
    length = math.sqrt(vector_x**2 + vector_y**2)
    if length == 0:
        return None
    
    # 正規化
    norm_y = vector_y / length
    
    # 鉛直軸 [0, 1] との内積 = norm_y
    cos_angle = max(-1.0, min(1.0, norm_y))
    
    # 角度計算
    angle_rad = math.acos(cos_angle)
    if vector_x < 0:  # 左方向は負
        angle_rad = -angle_rad
    
    angle_deg = math.degrees(angle_rad)
    
    # 符号反転（後方を正とする場合）
    if not forward_positive:
        angle_deg = -angle_deg
    
    return angle_deg

# =============================================================================
# メイン実行部
# =============================================================================

if __name__ == '__main__':
    # 計算例の実行
    demonstrate_calculation()
    
    print("\n" + "=" * 80)
    print("簡潔版関数のテスト")
    print("=" * 80)
    
    # 簡潔版のテスト
    test_cases = [
        ("体幹前傾10度", 0.1, -0.9, True),
        ("体幹後傾10度", -0.1, -0.9, True),
        ("大腿前方20度", 0.3, 0.9, False),
        ("大腿後方15度", -0.25, 0.9, False),
        ("下腿垂直", 0.0, 1.0, False)
    ]
    
    for name, vx, vy, forward_pos in test_cases:
        angle = simple_angle_calculation(vx, vy, forward_pos)
        print(f"{name:12}: {angle:7.1f}°") 