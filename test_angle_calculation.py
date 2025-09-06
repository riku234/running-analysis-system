#!/usr/bin/env python3
"""
角度計算の符号規則をテストするスクリプト
"""

import sys
import os
import numpy as np

# プロジェクトのパスを追加
sys.path.append('backend/services/feature_extraction/app')

try:
    from main import (
        calculate_absolute_angle_with_vertical, 
        calculate_trunk_angle,
        calculate_thigh_angle,
        calculate_lower_leg_angle,
        KeyPoint
    )
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("仮想環境を有効化してください: source venv/bin/activate")
    sys.exit(1)

def test_absolute_angle_calculation():
    """基本的な角度計算のテスト"""
    print("\n🔍 基本的な角度計算のテスト")
    print("=" * 50)
    
    # テストケース
    test_vectors = [
        ([1, 0], "右向き（前方）"),
        ([-1, 0], "左向き（後方）"),
        ([0, -1], "上向き（鉛直）"),
        ([0, 1], "下向き"),
        ([1, -1], "右上向き"),
        ([-1, -1], "左上向き")
    ]
    
    for vector, description in test_vectors:
        angle_forward_true = calculate_absolute_angle_with_vertical(np.array(vector), forward_positive=True)
        angle_forward_false = calculate_absolute_angle_with_vertical(np.array(vector), forward_positive=False)
        
        print(f"ベクトル {vector} ({description}):")
        print(f"  forward_positive=True:  {angle_forward_true:.1f}°")
        print(f"  forward_positive=False: {angle_forward_false:.1f}°")

def test_trunk_angle():
    """体幹角度計算のテスト"""
    print("\n🏃 体幹角度計算のテスト（新しい符号規則）")
    print("=" * 50)
    
    # テストケース：左傾き=後傾で正値、右傾き=前傾で正値
    test_cases = [
        {
            "name": "直立（理想的な姿勢）",
            "shoulder": (0.5, 0.3),
            "hip": (0.5, 0.7),
            "expected": "約0°"
        },
        {
            "name": "左傾き（後傾） - 正値",
            "shoulder": (0.4, 0.3),  # 肩が左（後方）
            "hip": (0.5, 0.7),
            "expected": "正値"
        },
        {
            "name": "右傾き（前傾） - 正値", 
            "shoulder": (0.6, 0.3),  # 肩が右（前方）
            "hip": (0.5, 0.7),
            "expected": "正値"
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['name']} (期待値: {case['expected']}):")
        
        # KeyPointオブジェクトを作成
        keypoints = [None] * 33  # MediaPipeの33個のランドマーク
        
        # 肩のキーポイント（インデックス11, 12）
        keypoints[11] = KeyPoint(x=case["shoulder"][0], y=case["shoulder"][1], z=0, visibility=1.0)  # left_shoulder
        keypoints[12] = KeyPoint(x=case["shoulder"][0], y=case["shoulder"][1], z=0, visibility=1.0)  # right_shoulder
        
        # 股関節のキーポイント（インデックス23, 24）
        keypoints[23] = KeyPoint(x=case["hip"][0], y=case["hip"][1], z=0, visibility=1.0)  # left_hip
        keypoints[24] = KeyPoint(x=case["hip"][0], y=case["hip"][1], z=0, visibility=1.0)  # right_hip
        
        angle = calculate_trunk_angle(keypoints)
        print(f"  計算結果: {angle:.1f}°")

def test_limb_angles():
    """大腿・下腿角度計算のテスト"""
    print("\n🦵 大腿・下腿角度計算のテスト")
    print("=" * 50)
    
    # テストケース
    test_cases = [
        {
            "name": "離地時（膝・足首が後方）",
            "hip": (0.5, 0.5),
            "knee": (0.4, 0.6),  # 膝が後方（左側）
            "ankle": (0.3, 0.8), # 足首がさらに後方
            "expected_thigh": "正値",
            "expected_lower": "正値"
        },
        {
            "name": "接地時（膝・足首が前方）",
            "hip": (0.5, 0.5),
            "knee": (0.6, 0.6),  # 膝が前方（右側）
            "ankle": (0.7, 0.8), # 足首がさらに前方
            "expected_thigh": "負値",
            "expected_lower": "負値"
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  期待値 - 大腿角度: {case['expected_thigh']}, 下腿角度: {case['expected_lower']}")
        
        # KeyPointオブジェクトを作成
        hip = KeyPoint(x=case["hip"][0], y=case["hip"][1], z=0, visibility=1.0)
        knee = KeyPoint(x=case["knee"][0], y=case["knee"][1], z=0, visibility=1.0)
        ankle = KeyPoint(x=case["ankle"][0], y=case["ankle"][1], z=0, visibility=1.0)
        
        thigh_angle = calculate_thigh_angle(hip, knee, "test")
        lower_leg_angle = calculate_lower_leg_angle(knee, ankle, "test")
        
        print(f"  計算結果 - 大腿角度: {thigh_angle:.1f}°, 下腿角度: {lower_leg_angle:.1f}°")

if __name__ == "__main__":
    print("🧪 角度計算テストスクリプト")
    print("新しい符号規則のテスト:")
    print("・体幹角度: 左傾き=後傾で正値、右傾き=前傾で正値")
    print("・大腿角度: 膝が後方で正値、前方で負値")
    print("・下腿角度: 足首が後方で正値、前方で負値")
    
    test_absolute_angle_calculation()
    test_trunk_angle()
    test_limb_angles()
    
    print("\n✅ テスト完了")
