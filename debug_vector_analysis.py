#!/usr/bin/env python3
"""
ベクトルと角度計算の詳細分析
"""

import sys
import numpy as np

# プロジェクトのパスを追加
sys.path.append('backend/services/feature_extraction/app')

try:
    from main import calculate_absolute_angle_with_vertical
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def analyze_vector_angles():
    """ベクトルと角度の関係を詳しく分析"""
    print("🔍 ベクトルと角度の関係分析")
    print("=" * 50)
    
    # 座標系の確認
    print("MediaPipe座標系:")
    print("- X軸: 左(0) → 右(1)")
    print("- Y軸: 上(0) → 下(1)")
    print("- 進行方向: 左→右 (X軸正方向)")
    print()
    
    # 大腿角度の理想的な動作
    print("🦵 大腿角度の理想的な動作 (股関節X=0.5基準):")
    print("- 離地時: 膝が後方 → 膝のX < 0.5 (膝が左側) → 正値期待")
    print("- 接地時: 膝が前方 → 膝のX > 0.5 (膝が右側) → 負値期待")
    print()
    
    test_cases = [
        {
            "name": "離地時: 膝が後方(左側)",
            "hip": (0.5, 0.5),
            "knee": (0.3, 0.6),  # 膝がX軸負方向(後方)
            "expected": "正値"
        },
        {
            "name": "接地時: 膝が前方(右側)",
            "hip": (0.5, 0.5),
            "knee": (0.7, 0.6),  # 膝がX軸正方向(前方)
            "expected": "負値"
        }
    ]
    
    for case in test_cases:
        print(f"{case['name']} (期待値: {case['expected']}):")
        
        # 大腿ベクトル（膝→股関節）
        thigh_vector = np.array([
            case["hip"][0] - case["knee"][0],  # X成分
            case["hip"][1] - case["knee"][1]   # Y成分
        ])
        
        print(f"  股関節: {case['hip']}, 膝: {case['knee']}")
        print(f"  大腿ベクトル: [{thigh_vector[0]:.3f}, {thigh_vector[1]:.3f}]")
        
        # forward_positive=True と False の結果を比較
        angle_true = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=True)
        angle_false = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        
        print(f"  forward_positive=True:  {angle_true:.1f}°")
        print(f"  forward_positive=False: {angle_false:.1f}°")
        print(f"  -angle_true: {-angle_true:.1f}°")
        print(f"  -angle_false: {-angle_false:.1f}°")
        
        # どれが期待値に合うか判定
        if case["expected"] == "正値":
            correct_options = []
            if angle_true > 0: correct_options.append("forward_positive=True")
            if angle_false > 0: correct_options.append("forward_positive=False") 
            if -angle_true > 0: correct_options.append("-angle_true")
            if -angle_false > 0: correct_options.append("-angle_false")
            print(f"  ✅ 正値になるオプション: {', '.join(correct_options)}")
        else:
            correct_options = []
            if angle_true < 0: correct_options.append("forward_positive=True")
            if angle_false < 0: correct_options.append("forward_positive=False")
            if -angle_true < 0: correct_options.append("-angle_true")
            if -angle_false < 0: correct_options.append("-angle_false")
            print(f"  ✅ 負値になるオプション: {', '.join(correct_options)}")
        
        print()

if __name__ == "__main__":
    analyze_vector_angles()
