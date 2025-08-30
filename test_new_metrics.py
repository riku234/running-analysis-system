# =============================================================================
# 新機能テスト: 重心上下動とピッチ計算のテスト
# =============================================================================

import numpy as np
from typing import List, Optional

class KeyPoint:
    def __init__(self, x: float, y: float, z: float, visibility: float):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

def calculate_vertical_oscillation(time_series_keypoints: List[List[KeyPoint]], runner_height: float) -> Optional[float]:
    """重心上下動を計算する（テスト版）"""
    try:
        if not time_series_keypoints or runner_height <= 0:
            return None
        
        center_of_mass_y_positions = []
        
        # 各フレームで重心のY座標を計算
        for frame_keypoints in time_series_keypoints:
            if len(frame_keypoints) < 33:
                continue
                
            left_hip = frame_keypoints[23]  # left_hip index
            right_hip = frame_keypoints[24]  # right_hip index
            
            # 股関節の可視性チェック
            if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
                continue
            
            # 左右股関節の中点を重心として定義
            center_of_mass_y = (left_hip.y + right_hip.y) / 2
            center_of_mass_y_positions.append(center_of_mass_y)
        
        # 有効なデータが不足している場合
        if len(center_of_mass_y_positions) < 3:
            return None
        
        # 最大値と最小値の差を計算（上下動の絶対距離）
        max_y = max(center_of_mass_y_positions)
        min_y = min(center_of_mass_y_positions)
        vertical_displacement = max_y - min_y
        
        # 身長に対する比率を計算
        vertical_oscillation_ratio = vertical_displacement / runner_height if runner_height > 0 else None
        
        return vertical_oscillation_ratio
        
    except Exception as e:
        print(f"重心上下動計算エラー: {str(e)}")
        return None

def calculate_pitch(num_frames_in_cycle: int, video_fps: float) -> Optional[float]:
    """ピッチ（ケイデンス）を計算する（テスト版）"""
    try:
        if num_frames_in_cycle <= 0 or video_fps <= 0:
            return None
        
        # 1サイクルの所要時間を秒単位で計算
        cycle_duration_seconds = num_frames_in_cycle / video_fps
        
        # ランニングの1サイクル = 2歩（右足接地 + 左足接地）
        steps_per_cycle = 2
        
        # 1分間あたりの歩数（SPM: Steps Per Minute）を計算
        steps_per_minute = (steps_per_cycle / cycle_duration_seconds) * 60
        
        return steps_per_minute
        
    except Exception as e:
        print(f"ピッチ計算エラー: {str(e)}")
        return None

def create_test_data():
    """テスト用のサンプルデータを生成"""
    
    # 30フレームのサンプルデータ（1秒間、30fps）
    # ランニング中の重心の上下動をシミュレート
    frames = []
    for i in range(30):
        frame_keypoints = [None] * 33
        
        # 時間による上下動をシミュレート（サイン波で近似）
        time_factor = i / 30.0  # 0から1へ
        y_oscillation = 0.02 * np.sin(2 * np.pi * time_factor)  # 上下動 ±2%
        
        # 左股関節（index 23）
        frame_keypoints[23] = KeyPoint(
            x=0.45, 
            y=0.50 + y_oscillation,  # 基準位置 + 上下動
            z=0.0, 
            visibility=0.95
        )
        
        # 右股関節（index 24）
        frame_keypoints[24] = KeyPoint(
            x=0.55, 
            y=0.50 + y_oscillation,  # 基準位置 + 上下動
            z=0.0, 
            visibility=0.95
        )
        
        frames.append(frame_keypoints)
    
    return frames

def main():
    """メイン実行関数"""
    print("=" * 70)
    print("新機能テスト: 重心上下動とピッチ計算")
    print("=" * 70)
    
    # テストデータの生成
    print("\n1. テストデータの生成中...")
    test_frames = create_test_data()
    print(f"   生成されたフレーム数: {len(test_frames)}")
    
    # 重心上下動のテスト
    print("\n2. 重心上下動の計算テスト:")
    runner_height = 1.7  # 身長1.7m
    vertical_oscillation = calculate_vertical_oscillation(test_frames, runner_height)
    
    if vertical_oscillation is not None:
        print(f"   ✅ 重心上下動: {vertical_oscillation:.6f}")
        print(f"   ✅ 身長比: {(vertical_oscillation * 100):.2f}%")
        
        # 理想値との比較
        ideal_range = (0.05, 0.08)  # 5-8%
        percentage = vertical_oscillation * 100
        if ideal_range[0] * 100 <= percentage <= ideal_range[1] * 100:
            print(f"   ✅ 評価: 理想的な範囲内（5-8%）")
        elif percentage < ideal_range[0] * 100:
            print(f"   ⚠️  評価: やや少ない（理想: 5-8%）")
        else:
            print(f"   ⚠️  評価: やや多い（理想: 5-8%）")
    else:
        print("   ❌ 重心上下動の計算に失敗")
    
    # ピッチのテスト
    print("\n3. ピッチ（ケイデンス）の計算テスト:")
    video_fps = 30.0
    num_frames = len(test_frames)
    pitch = calculate_pitch(num_frames, video_fps)
    
    if pitch is not None:
        print(f"   ✅ ピッチ: {pitch:.1f} SPM")
        print(f"   ✅ 計算詳細:")
        print(f"      - フレーム数: {num_frames}")
        print(f"      - 動画FPS: {video_fps}")
        print(f"      - サイクル時間: {num_frames/video_fps:.2f}秒")
        print(f"      - 1サイクル = 2歩")
        
        # 理想値との比較
        ideal_range = (170, 190)  # 170-190 SPM
        if ideal_range[0] <= pitch <= ideal_range[1]:
            print(f"   ✅ 評価: 理想的な範囲内（170-190 SPM）")
        elif pitch < ideal_range[0]:
            print(f"   ⚠️  評価: やや遅い（理想: 170-190 SPM）")
        else:
            print(f"   ⚠️  評価: やや速い（理想: 170-190 SPM）")
    else:
        print("   ❌ ピッチの計算に失敗")
    
    # 異なるFPSでのテスト
    print("\n4. 異なるFPSでのピッチ計算テスト:")
    fps_tests = [24, 30, 60]
    for fps in fps_tests:
        pitch_test = calculate_pitch(30, fps)  # 30フレーム
        if pitch_test is not None:
            print(f"   {fps}fps: {pitch_test:.1f} SPM (サイクル時間: {30/fps:.2f}秒)")
    
    # エラーハンドリングのテスト
    print("\n5. エラーハンドリングのテスト:")
    
    # 無効な入力でのテスト
    error_tests = [
        ([], 1.7, "空のフレームデータ"),
        (test_frames, 0, "無効な身長"),
        (test_frames, -1.5, "負の身長")
    ]
    
    for frames, height, description in error_tests:
        result = calculate_vertical_oscillation(frames, height)
        status = "✅ 正しくNoneを返却" if result is None else f"❌ 予期しない結果: {result}"
        print(f"   {description}: {status}")
    
    pitch_error_tests = [
        (0, 30.0, "ゼロフレーム"),
        (-10, 30.0, "負のフレーム数"),
        (30, 0, "ゼロFPS"),
        (30, -30.0, "負のFPS")
    ]
    
    for frames, fps, description in pitch_error_tests:
        result = calculate_pitch(frames, fps)
        status = "✅ 正しくNoneを返却" if result is None else f"❌ 予期しない結果: {result}"
        print(f"   {description}: {status}")
    
    print("\n" + "=" * 70)
    print("✅ 新機能テスト完了")
    print("=" * 70)

if __name__ == "__main__":
    main() 