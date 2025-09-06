#!/usr/bin/env python3
"""
座標系とベクトルの向きを詳しく分析するスクリプト
"""

import sys
import os
import numpy as np

# プロジェクトのパスを追加
sys.path.append('backend/services/feature_extraction/app')

try:
    from main import calculate_absolute_angle_with_vertical, KeyPoint
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def analyze_coordinate_system():
    """MediaPipeの座標系を分析"""
    print("📐 MediaPipe座標系の分析")
    print("=" * 50)
    print("MediaPipeでは:")
    print("- X軸: 左→右 (0.0 ～ 1.0)")
    print("- Y軸: 上→下 (0.0 ～ 1.0)")
    print("- 進行方向: 左→右 (X軸正方向)")
    print()
    
    print("ユーザー要求:")
    print("- 左から右にランナーが進行（X軸正方向）")
    print("- 膝が後方（X軸負方向）で正値")
    print("- 膝が前方（X軸正方向）で負値")
    print()

def test_thigh_scenarios():
    """大腿角度の具体的なシナリオをテスト"""
    print("🦵 大腿角度の詳細分析")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "離地時: 膝が股関節より後方（左側）",
            "hip_x": 0.5, "knee_x": 0.3,  # 膝が左（後方）
            "expected": "正値"
        },
        {
            "name": "接地時: 膝が股関節より前方（右側）", 
            "hip_x": 0.5, "knee_x": 0.7,  # 膝が右（前方）
            "expected": "負値"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']} (期待値: {scenario['expected']}):")
        
        # 大腿ベクトル（膝→股関節）を計算
        thigh_vector_x = scenario["hip_x"] - scenario["knee_x"]
        thigh_vector = np.array([thigh_vector_x, -0.1])  # Y成分は上向き
        
        print(f"  股関節X: {scenario['hip_x']}, 膝X: {scenario['knee_x']}")
        print(f"  大腿ベクトル: [{thigh_vector[0]:.3f}, {thigh_vector[1]:.3f}]")
        
        # forward_positive=True と False の両方をテスト
        angle_true = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=True)
        angle_false = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        
        print(f"  forward_positive=True:  {angle_true:.1f}°")
        print(f"  forward_positive=False: {angle_false:.1f}°")
        print(f"  反転後 (-angle_true): {-angle_true:.1f}°")
        
        # どれが期待値に合うかチェック
        if scenario["expected"] == "正値":
            if angle_true > 0:
                print("  ✅ forward_positive=True が期待に合致")
            elif angle_false > 0:
                print("  ✅ forward_positive=False が期待に合致")
            elif -angle_true > 0:
                print("  ✅ -angle_true が期待に合致")
        else:  # 負値期待
            if angle_true < 0:
                print("  ✅ forward_positive=True が期待に合致")
            elif angle_false < 0:
                print("  ✅ forward_positive=False が期待に合致")
            elif -angle_true < 0:
                print("  ✅ -angle_true が期待に合致")

if __name__ == "__main__":
    analyze_coordinate_system()
    test_thigh_scenarios()
