# =============================================================================
# 足接地検出ベースピッチ計算機能のテスト
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
    'left_ankle': 27,
    'right_ankle': 28,
}

def calculate_pitch_from_keypoints(time_series_keypoints: List[List[KeyPoint]], video_fps: float) -> Optional[float]:
    """足の接地検出に基づいてピッチを正確に計算する（テスト版）"""
    try:
        if not time_series_keypoints or video_fps <= 0:
            return None
        
        print(f"🦶 フットストライク検出開始...")
        
        # ステップ1: フットストライク（接地）の検出
        
        # a. データ抽出: 左右の足首のY座標を時系列データとして抽出
        left_ankle_y = []
        right_ankle_y = []
        valid_frame_indices = []
        
        for frame_idx, frame_keypoints in enumerate(time_series_keypoints):
            if len(frame_keypoints) < 33:
                continue
                
            left_ankle = frame_keypoints[LANDMARK_INDICES['left_ankle']]
            right_ankle = frame_keypoints[LANDMARK_INDICES['right_ankle']]
            
            # 足首の可視性チェック
            if left_ankle.visibility > 0.5 and right_ankle.visibility > 0.5:
                left_ankle_y.append(left_ankle.y)
                right_ankle_y.append(right_ankle.y)
                valid_frame_indices.append(frame_idx)
        
        if len(left_ankle_y) < 10:  # 最小フレーム数チェック
            print(f"❌ 有効フレーム数が不足: {len(left_ankle_y)}")
            return None
        
        # b. 平滑化: 移動平均フィルタを適用
        def moving_average(data, window_size=5):
            """移動平均フィルタ"""
            if len(data) < window_size:
                return data
            smoothed = []
            for i in range(len(data)):
                start = max(0, i - window_size // 2)
                end = min(len(data), i + window_size // 2 + 1)
                smoothed.append(np.mean(data[start:end]))
            return smoothed
        
        left_ankle_y_smooth = moving_average(left_ankle_y, window_size=5)
        right_ankle_y_smooth = moving_average(right_ankle_y, window_size=5)
        
        # c. 極小値の検出: 足が地面に最も近づいた瞬間（接地）を検出
        def detect_foot_strikes(ankle_y_data, min_distance=10):
            """足の接地（極小値）を検出"""
            strikes = []
            
            for i in range(1, len(ankle_y_data) - 1):
                # 現在の点が両隣より低い（極小値）かチェック
                if (ankle_y_data[i] < ankle_y_data[i-1] and 
                    ankle_y_data[i] < ankle_y_data[i+1]):
                    
                    # 前回の接地から十分な距離があるかチェック
                    if not strikes or (i - strikes[-1]) >= min_distance:
                        strikes.append(i)
            
            return strikes
        
        # 左右の足の接地フレームを検出
        left_foot_strikes = detect_foot_strikes(left_ankle_y_smooth)
        right_foot_strikes = detect_foot_strikes(right_ankle_y_smooth)
        
        print(f"🦶 接地検出結果:")
        print(f"   - 左足接地: {len(left_foot_strikes)}回 {left_foot_strikes}")
        print(f"   - 右足接地: {len(right_foot_strikes)}回 {right_foot_strikes}")
        
        # ステップ2: ランニングサイクルの定義と期間の計算
        
        # 右足の接地を基準にサイクル期間を計算（左足でも可）
        primary_foot_strikes = right_foot_strikes if len(right_foot_strikes) >= len(left_foot_strikes) else left_foot_strikes
        foot_type = "右足" if len(right_foot_strikes) >= len(left_foot_strikes) else "左足"
        
        if len(primary_foot_strikes) < 2:
            print(f"❌ 検出された接地が不足: {len(primary_foot_strikes)}回")
            return None
        
        # a. サイクル期間のリスト作成: 隣り合う接地間のフレーム数
        cycle_lengths_in_frames = []
        for i in range(1, len(primary_foot_strikes)):
            cycle_length = primary_foot_strikes[i] - primary_foot_strikes[i-1]
            cycle_lengths_in_frames.append(cycle_length)
        
        print(f"📊 サイクル分析結果（{foot_type}基準）:")
        print(f"   - 検出サイクル数: {len(cycle_lengths_in_frames)}")
        print(f"   - サイクル長（フレーム）: {cycle_lengths_in_frames}")
        
        # ステップ3: ピッチ（ケイデンス）の計算
        
        # a. サイクルごとのピッチ計算
        cycle_pitches = []
        for total_frames in cycle_lengths_in_frames:
            # サイクル時間を秒単位で計算
            cycle_time_seconds = total_frames / video_fps
            
            # ピッチ（SPM）を計算: 1サイクル = 2歩
            pitch_spm = (2 / cycle_time_seconds) * 60
            cycle_pitches.append(pitch_spm)
        
        # b. 平均ピッチの算出
        average_pitch = np.mean(cycle_pitches)
        
        print(f"🏃 ピッチ計算詳細:")
        print(f"   - 各サイクルのピッチ: {[f'{p:.1f}' for p in cycle_pitches]} SPM")
        print(f"   - 平均ピッチ: {average_pitch:.1f} SPM")
        print(f"   - 標準偏差: {np.std(cycle_pitches):.1f} SPM")
        
        return average_pitch
        
    except Exception as e:
        print(f"高精度ピッチ計算エラー: {str(e)}")
        return None

def create_realistic_running_data_with_footstrikes():
    """実際の足の接地パターンを含むランナーのテストデータを生成"""
    
    frames = []
    num_frames = 120  # 4秒間、30fps
    video_fps = 30
    
    # ランナーの仕様
    stride_frequency = 3.0  # 1秒に3歩（180 SPM）
    
    for i in range(num_frames):
        frame_keypoints = [None] * 33
        
        # 時間計算
        time_seconds = i / video_fps
        
        # 足の動きをシミュレート
        # 左足: サイン波で足の上下動をシミュレート
        left_foot_cycle = math.sin(2 * math.pi * stride_frequency * time_seconds)
        right_foot_cycle = math.sin(2 * math.pi * stride_frequency * time_seconds + math.pi)  # 位相を180度ずらす
        
        # 足首の基準高さ
        base_ankle_height = 0.85
        foot_lift_amplitude = 0.05  # 足の上下動の幅
        
        # 左足首（27番）
        left_ankle_y = base_ankle_height + foot_lift_amplitude * max(0, left_foot_cycle)
        frame_keypoints[27] = KeyPoint(x=0.45, y=left_ankle_y, z=0.0, visibility=0.95)
        
        # 右足首（28番）
        right_ankle_y = base_ankle_height + foot_lift_amplitude * max(0, right_foot_cycle)
        frame_keypoints[28] = KeyPoint(x=0.55, y=right_ankle_y, z=0.0, visibility=0.95)
        
        frames.append(frame_keypoints)
    
    return frames, video_fps

def main():
    """メイン実行関数"""
    print("=" * 70)
    print("足接地検出ベースピッチ計算機能テスト")
    print("=" * 70)
    
    # テストデータの生成
    print("\n1. ランニングデータ（足接地パターン付き）の生成中...")
    test_frames, fps = create_realistic_running_data_with_footstrikes()
    print(f"   生成されたフレーム数: {len(test_frames)}")
    print(f"   動画FPS: {fps}")
    print(f"   動画時間: {len(test_frames)/fps:.1f}秒")
    print(f"   期待されるピッチ: 180 SPM（設計値）")
    
    # 足接地検出ベースピッチ計算テスト
    print("\n2. 足接地検出ベースピッチ計算テスト:")
    calculated_pitch = calculate_pitch_from_keypoints(test_frames, fps)
    
    if calculated_pitch is not None:
        print(f"\n✅ 計算結果:")
        print(f"   - 計算されたピッチ: {calculated_pitch:.1f} SPM")
        print(f"   - 期待値: 180 SPM")
        print(f"   - 誤差: {abs(calculated_pitch - 180):.1f} SPM")
        
        # 精度評価
        accuracy = (1 - abs(calculated_pitch - 180) / 180) * 100
        print(f"   - 精度: {accuracy:.1f}%")
        
        if accuracy > 95:
            print(f"   ✅ 評価: 非常に高精度")
        elif accuracy > 90:
            print(f"   ✅ 評価: 高精度")
        elif accuracy > 80:
            print(f"   ⚠️  評価: 中程度の精度")
        else:
            print(f"   ❌ 評価: 精度不足")
    else:
        print("   ❌ ピッチ計算に失敗")
    
    # 異なるピッチでのテスト
    print("\n3. 異なるピッチでの検証テスト:")
    test_pitches = [160, 170, 180, 190, 200]  # SPM
    
    for target_pitch in test_pitches:
        print(f"\n   目標ピッチ: {target_pitch} SPM")
        
        # 対応するストライド周波数を計算
        stride_freq = target_pitch / 60.0  # SPMをHzに変換
        
        # テストデータ生成（簡易版）
        test_frames_custom = []
        for i in range(60):  # 2秒間
            frame_keypoints = [None] * 33
            time_s = i / 30.0
            
            left_cycle = math.sin(2 * math.pi * stride_freq * time_s)
            right_cycle = math.sin(2 * math.pi * stride_freq * time_s + math.pi)
            
            left_y = 0.85 + 0.05 * max(0, left_cycle)
            right_y = 0.85 + 0.05 * max(0, right_cycle)
            
            frame_keypoints[27] = KeyPoint(x=0.45, y=left_y, z=0.0, visibility=0.95)
            frame_keypoints[28] = KeyPoint(x=0.55, y=right_y, z=0.0, visibility=0.95)
            
            test_frames_custom.append(frame_keypoints)
        
        result = calculate_pitch_from_keypoints(test_frames_custom, 30.0)
        if result:
            error = abs(result - target_pitch)
            print(f"      結果: {result:.1f} SPM (誤差: {error:.1f} SPM)")
        else:
            print(f"      結果: 計算失敗")
    
    print("\n" + "=" * 70)
    print("✅ 足接地検出ベースピッチ計算機能テスト完了")
    print("=" * 70)

if __name__ == "__main__":
    main() 