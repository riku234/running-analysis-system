# =============================================================================
# 骨格身長推定機能のテスト
# =============================================================================

import numpy as np
import math
from typing import List, Optional

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
    'right_ankle': 28,
}

def calculate_skeletal_height(frame_keypoints: List[KeyPoint]) -> Optional[float]:
    """1フレームの骨格データから「骨格上の全長」を計算する"""
    try:
        if len(frame_keypoints) < 33:
            return None
        
        # 必要なキーポイントを取得
        left_ankle = frame_keypoints[LANDMARK_INDICES['left_ankle']]
        right_ankle = frame_keypoints[LANDMARK_INDICES['right_ankle']]
        left_knee = frame_keypoints[LANDMARK_INDICES['left_knee']]
        right_knee = frame_keypoints[LANDMARK_INDICES['right_knee']]
        left_hip = frame_keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = frame_keypoints[LANDMARK_INDICES['right_hip']]
        left_shoulder = frame_keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = frame_keypoints[LANDMARK_INDICES['right_shoulder']]
        
        # 鼻（頭部の代表点）
        nose = frame_keypoints[0]  # MediaPipeの鼻のインデックス
        
        # 可視性チェック（0.5以上で有効とする）
        required_points = [left_ankle, right_ankle, left_knee, right_knee, 
                          left_hip, right_hip, left_shoulder, right_shoulder, nose]
        
        for point in required_points:
            if point.visibility < 0.5:
                return None
        
        # 各セグメントの長さを計算
        
        # 1. 下腿長: 足首から膝までの距離（左右の平均）
        left_lower_leg = math.sqrt((left_knee.x - left_ankle.x)**2 + (left_knee.y - left_ankle.y)**2)
        right_lower_leg = math.sqrt((right_knee.x - right_ankle.x)**2 + (right_knee.y - right_ankle.y)**2)
        avg_lower_leg_length = (left_lower_leg + right_lower_leg) / 2
        
        # 2. 大腿長: 膝から股関節までの距離（左右の平均）
        left_thigh = math.sqrt((left_hip.x - left_knee.x)**2 + (left_hip.y - left_knee.y)**2)
        right_thigh = math.sqrt((right_hip.x - right_knee.x)**2 + (right_hip.y - right_knee.y)**2)
        avg_thigh_length = (left_thigh + right_thigh) / 2
        
        # 3. 体幹長: 股関節の中点から肩の中点までの距離
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        trunk_length = math.sqrt((shoulder_center_x - hip_center_x)**2 + (shoulder_center_y - hip_center_y)**2)
        
        # 4. 頭部長: 肩の中点から鼻までの距離
        head_length = math.sqrt((nose.x - shoulder_center_x)**2 + (nose.y - shoulder_center_y)**2)
        
        # 骨格上の全長を計算
        total_skeletal_height = avg_lower_leg_length + avg_thigh_length + trunk_length + head_length
        
        return total_skeletal_height
        
    except Exception as e:
        print(f"骨格身長計算エラー: {str(e)}")
        return None

def calculate_vertical_oscillation(time_series_keypoints: List[List[KeyPoint]]) -> Optional[float]:
    """重心上下動を計算する（骨格データから自動的に基準身長を算出）"""
    try:
        if not time_series_keypoints:
            return None
        
        center_of_mass_y_positions = []
        skeletal_heights = []
        
        # 各フレームで重心のY座標と骨格身長を計算
        for frame_keypoints in time_series_keypoints:
            if len(frame_keypoints) < 33:
                continue
                
            left_hip = frame_keypoints[LANDMARK_INDICES['left_hip']]
            right_hip = frame_keypoints[LANDMARK_INDICES['right_hip']]
            
            # 股関節の可視性チェック
            if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
                continue
            
            # 左右股関節の中点を重心として定義
            center_of_mass_y = (left_hip.y + right_hip.y) / 2
            center_of_mass_y_positions.append(center_of_mass_y)
            
            # このフレームの骨格身長を計算
            skeletal_height = calculate_skeletal_height(frame_keypoints)
            if skeletal_height is not None:
                skeletal_heights.append(skeletal_height)
        
        # 有効なデータが不足している場合
        if len(center_of_mass_y_positions) < 3 or len(skeletal_heights) < 3:
            return None
        
        # 「計算上の平均身長」を算出
        avg_skeletal_height = np.mean(skeletal_heights)
        
        # 重心のY座標の最大値と最小値の差を計算（分子）
        max_y = max(center_of_mass_y_positions)
        min_y = min(center_of_mass_y_positions)
        vertical_displacement = max_y - min_y
        
        # 重心上下動の比率を計算（分子 / 分母）
        vertical_oscillation_ratio = vertical_displacement / avg_skeletal_height if avg_skeletal_height > 0 else None
        
        return vertical_oscillation_ratio, avg_skeletal_height, vertical_displacement, len(skeletal_heights)
        
    except Exception as e:
        print(f"重心上下動計算エラー: {str(e)}")
        return None

def create_realistic_runner_data():
    """現実的なランナーのテストデータを生成"""
    
    frames = []
    num_frames = 30
    
    # ランナーの基本体型（正規化座標）
    base_proportions = {
        'lower_leg': 0.23,  # 下腿長（身長の23%）
        'thigh': 0.25,      # 大腿長（身長の25%）
        'trunk': 0.30,      # 体幹長（身長の30%）
        'head': 0.12        # 頭部長（身長の12%）
    }
    
    for i in range(num_frames):
        frame_keypoints = [None] * 33
        
        # 時間による姿勢変化をシミュレート
        time_factor = i / num_frames  # 0から1へ
        
        # ランニング中の膝の曲がりをシミュレート
        knee_bend_factor = 0.02 * math.sin(2 * math.pi * time_factor)
        
        # 重心の上下動をシミュレート
        vertical_oscillation = 0.03 * math.sin(2 * math.pi * time_factor)
        
        # 基準位置を設定
        base_ankle_y = 0.9
        base_knee_y = base_ankle_y - base_proportions['lower_leg']
        base_hip_y = base_knee_y - base_proportions['thigh'] + knee_bend_factor
        base_shoulder_y = base_hip_y - base_proportions['trunk']
        base_nose_y = base_shoulder_y - base_proportions['head']
        
        # 重心の上下動を全体に適用
        base_ankle_y += vertical_oscillation
        base_knee_y += vertical_oscillation
        base_hip_y += vertical_oscillation
        base_shoulder_y += vertical_oscillation
        base_nose_y += vertical_oscillation
        
        # 鼻（0番）
        frame_keypoints[0] = KeyPoint(x=0.5, y=base_nose_y, z=0.0, visibility=0.95)
        
        # 左肩（11番）
        frame_keypoints[11] = KeyPoint(x=0.45, y=base_shoulder_y, z=0.0, visibility=0.95)
        
        # 右肩（12番）
        frame_keypoints[12] = KeyPoint(x=0.55, y=base_shoulder_y, z=0.0, visibility=0.95)
        
        # 左股関節（23番）
        frame_keypoints[23] = KeyPoint(x=0.45, y=base_hip_y, z=0.0, visibility=0.95)
        
        # 右股関節（24番）
        frame_keypoints[24] = KeyPoint(x=0.55, y=base_hip_y, z=0.0, visibility=0.95)
        
        # 左膝（25番）
        frame_keypoints[25] = KeyPoint(x=0.45, y=base_knee_y, z=0.0, visibility=0.95)
        
        # 右膝（26番）
        frame_keypoints[26] = KeyPoint(x=0.55, y=base_knee_y, z=0.0, visibility=0.95)
        
        # 左足首（27番）
        frame_keypoints[27] = KeyPoint(x=0.45, y=base_ankle_y, z=0.0, visibility=0.95)
        
        # 右足首（28番）
        frame_keypoints[28] = KeyPoint(x=0.55, y=base_ankle_y, z=0.0, visibility=0.95)
        
        frames.append(frame_keypoints)
    
    return frames

def main():
    """メイン実行関数"""
    print("=" * 70)
    print("骨格身長推定機能テスト")
    print("=" * 70)
    
    # テストデータの生成
    print("\n1. 現実的なランナーデータの生成中...")
    test_frames = create_realistic_runner_data()
    print(f"   生成されたフレーム数: {len(test_frames)}")
    
    # 1フレームの骨格身長計算テスト
    print("\n2. 1フレームの骨格身長計算テスト:")
    skeletal_height = calculate_skeletal_height(test_frames[0])
    if skeletal_height is not None:
        print(f"   ✅ 骨格身長: {skeletal_height:.6f} (正規化座標)")
        print(f"   ✅ 各セグメント分析:")
        
        # 詳細分析
        frame = test_frames[0]
        left_ankle = frame[LANDMARK_INDICES['left_ankle']]
        left_knee = frame[LANDMARK_INDICES['left_knee']]
        left_hip = frame[LANDMARK_INDICES['left_hip']]
        left_shoulder = frame[LANDMARK_INDICES['left_shoulder']]
        nose = frame[0]
        
        lower_leg = math.sqrt((left_knee.x - left_ankle.x)**2 + (left_knee.y - left_ankle.y)**2)
        thigh = math.sqrt((left_hip.x - left_knee.x)**2 + (left_hip.y - left_knee.y)**2)
        
        hip_center_y = (frame[23].y + frame[24].y) / 2
        shoulder_center_y = (frame[11].y + frame[12].y) / 2
        trunk = abs(shoulder_center_y - hip_center_y)
        head = abs(nose.y - shoulder_center_y)
        
        print(f"      - 下腿長: {lower_leg:.6f} ({lower_leg/skeletal_height*100:.1f}%)")
        print(f"      - 大腿長: {thigh:.6f} ({thigh/skeletal_height*100:.1f}%)")
        print(f"      - 体幹長: {trunk:.6f} ({trunk/skeletal_height*100:.1f}%)")
        print(f"      - 頭部長: {head:.6f} ({head/skeletal_height*100:.1f}%)")
    else:
        print("   ❌ 骨格身長の計算に失敗")
    
    # 全フレームでの平均身長計算
    print("\n3. 全フレームでの平均身長計算:")
    skeletal_heights = []
    for i, frame in enumerate(test_frames):
        height = calculate_skeletal_height(frame)
        if height is not None:
            skeletal_heights.append(height)
    
    if skeletal_heights:
        avg_height = np.mean(skeletal_heights)
        height_std = np.std(skeletal_heights)
        print(f"   ✅ 有効フレーム数: {len(skeletal_heights)}/{len(test_frames)}")
        print(f"   ✅ 平均骨格身長: {avg_height:.6f}")
        print(f"   ✅ 標準偏差: {height_std:.6f}")
        print(f"   ✅ 変動係数: {(height_std/avg_height*100):.2f}%")
    else:
        print("   ❌ 平均身長の計算に失敗")
    
    # 重心上下動計算テスト
    print("\n4. 重心上下動計算テスト:")
    result = calculate_vertical_oscillation(test_frames)
    if result is not None:
        ratio, avg_height, displacement, valid_frames = result
        print(f"   ✅ 重心上下動比率: {ratio:.6f}")
        print(f"   ✅ 基準身長: {avg_height:.6f}")
        print(f"   ✅ 上下動量: {displacement:.6f}")
        print(f"   ✅ 有効フレーム数: {valid_frames}")
        print(f"   ✅ パーセンテージ: {(ratio * 100):.2f}%")
        
        # 理想値との比較
        ideal_range = (0.05, 0.08)  # 5-8%
        percentage = ratio * 100
        if ideal_range[0] * 100 <= percentage <= ideal_range[1] * 100:
            print(f"   ✅ 評価: 理想的な範囲内（5-8%）")
        elif percentage < ideal_range[0] * 100:
            print(f"   ⚠️  評価: やや少ない（理想: 5-8%）")
        else:
            print(f"   ⚠️  評価: やや多い（理想: 5-8%）")
    else:
        print("   ❌ 重心上下動の計算に失敗")
    
    print("\n" + "=" * 70)
    print("✅ 骨格身長推定機能テスト完了")
    print("=" * 70)

if __name__ == "__main__":
    main() 