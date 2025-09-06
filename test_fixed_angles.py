#!/usr/bin/env python3
"""
修正された角度計算をテストするスクリプト
"""

import sys
import os
import numpy as np

# プロジェクトのパスを追加
sys.path.append('backend/services/feature_extraction/app')

try:
    from main import (
        calculate_trunk_angle,
        calculate_thigh_angle,
        calculate_lower_leg_angle,
        KeyPoint
    )
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def test_fixed_angles():
    """修正された角度計算のテスト"""
    print("\n🧪 修正された角度計算のテスト")
    print("=" * 50)
    
    # 体幹角度のテスト
    print("\n🏃 体幹角度テスト (前傾で正値、後傾で負値)")
    
    # テストケース1: 前傾（肩が股関節より前方/右側）
    keypoints = [None] * 33
    keypoints[11] = KeyPoint(x=0.6, y=0.3, z=0, visibility=1.0)  # left_shoulder
    keypoints[12] = KeyPoint(x=0.6, y=0.3, z=0, visibility=1.0)  # right_shoulder
    keypoints[23] = KeyPoint(x=0.5, y=0.7, z=0, visibility=1.0)  # left_hip
    keypoints[24] = KeyPoint(x=0.5, y=0.7, z=0, visibility=1.0)  # right_hip
    
    trunk_angle = calculate_trunk_angle(keypoints)
    print(f"前傾姿勢: {trunk_angle:.1f}° (期待値: 正値)")
    
    # テストケース2: 後傾（肩が股関節より後方/左側）
    keypoints[11] = KeyPoint(x=0.4, y=0.3, z=0, visibility=1.0)  # left_shoulder
    keypoints[12] = KeyPoint(x=0.4, y=0.3, z=0, visibility=1.0)  # right_shoulder
    
    trunk_angle = calculate_trunk_angle(keypoints)
    print(f"後傾姿勢: {trunk_angle:.1f}° (期待値: 負値)")
    
    # 大腿・下腿角度のテスト
    print("\n🦵 大腿・下腿角度テスト")
    
    # テストケース1: 離地時（膝・足首が後方）
    print("離地時（膝・足首が後方）:")
    hip = KeyPoint(x=0.5, y=0.5, z=0, visibility=1.0)
    knee = KeyPoint(x=0.3, y=0.6, z=0, visibility=1.0)  # 膝が後方
    ankle = KeyPoint(x=0.2, y=0.8, z=0, visibility=1.0)  # 足首がさらに後方
    
    thigh_angle = calculate_thigh_angle(hip, knee, "left")
    lower_leg_angle = calculate_lower_leg_angle(knee, ankle, "left")
    print(f"  大腿角度: {thigh_angle:.1f}° (期待値: 正値)")
    print(f"  下腿角度: {lower_leg_angle:.1f}° (期待値: 正値)")
    
    # テストケース2: 接地時（膝・足首が前方）
    print("接地時（膝・足首が前方）:")
    knee = KeyPoint(x=0.7, y=0.6, z=0, visibility=1.0)  # 膝が前方
    ankle = KeyPoint(x=0.8, y=0.8, z=0, visibility=1.0)  # 足首がさらに前方
    
    thigh_angle = calculate_thigh_angle(hip, knee, "left")
    lower_leg_angle = calculate_lower_leg_angle(knee, ankle, "left")
    print(f"  大腿角度: {thigh_angle:.1f}° (期待値: 負値)")
    print(f"  下腿角度: {lower_leg_angle:.1f}° (期待値: 負値)")

if __name__ == "__main__":
    print("🧪 修正された角度計算のテスト")
    print("・体幹角度: 前傾で正値、後傾で負値")
    print("・大腿角度: 膝が後方で正値、前方で負値")
    print("・下腿角度: 足首が後方で正値、前方で負値")
    
    test_fixed_angles()
    
    print("\n✅ テスト完了")
