#!/usr/bin/env python3
"""
最終修正の検証スクリプト
"""

import sys
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

def verify_final_angles():
    """最終修正された角度計算の検証"""
    print("\n🧪 最終修正された角度計算の検証")
    print("=" * 60)
    
    print("📐 立式と期待値:")
    print("・体幹角度: 前傾で正値、後傾で負値")
    print("・大腿角度: 膝が後方で正値、前方で負値")
    print("・下腿角度: 足首が後方で正値、前方で負値")
    print()
    
    # 体幹角度の検証
    print("🏃 体幹角度の検証:")
    keypoints = [None] * 33
    
    # 前傾姿勢
    keypoints[11] = KeyPoint(x=0.6, y=0.3, z=0, visibility=1.0)  # left_shoulder
    keypoints[12] = KeyPoint(x=0.6, y=0.3, z=0, visibility=1.0)  # right_shoulder
    keypoints[23] = KeyPoint(x=0.5, y=0.7, z=0, visibility=1.0)  # left_hip
    keypoints[24] = KeyPoint(x=0.5, y=0.7, z=0, visibility=1.0)  # right_hip
    trunk_angle = calculate_trunk_angle(keypoints)
    print(f"前傾姿勢: {trunk_angle:.1f}° (期待値: 正値) {'✅' if trunk_angle > 0 else '❌'}")
    
    # 後傾姿勢
    keypoints[11] = KeyPoint(x=0.4, y=0.3, z=0, visibility=1.0)  # left_shoulder
    keypoints[12] = KeyPoint(x=0.4, y=0.3, z=0, visibility=1.0)  # right_shoulder
    trunk_angle = calculate_trunk_angle(keypoints)
    print(f"後傾姿勢: {trunk_angle:.1f}° (期待値: 負値) {'✅' if trunk_angle < 0 else '❌'}")
    
    # 大腿角度の検証
    print("\n🦵 大腿角度の検証:")
    
    # 離地時（膝が後方）
    hip = KeyPoint(x=0.5, y=0.5, z=0, visibility=1.0)
    knee = KeyPoint(x=0.3, y=0.6, z=0, visibility=1.0)  # 膝が後方
    thigh_angle = calculate_thigh_angle(hip, knee, "test")
    print(f"離地時（膝が後方）: {thigh_angle:.1f}° (期待値: 正値) {'✅' if thigh_angle > 0 else '❌'}")
    
    # 接地時（膝が前方）
    knee = KeyPoint(x=0.7, y=0.6, z=0, visibility=1.0)  # 膝が前方
    thigh_angle = calculate_thigh_angle(hip, knee, "test")
    print(f"接地時（膝が前方）: {thigh_angle:.1f}° (期待値: 負値) {'✅' if thigh_angle < 0 else '❌'}")
    
    # 下腿角度の検証
    print("\n🦵 下腿角度の検証:")
    
    # 離地時（足首が後方）
    knee = KeyPoint(x=0.5, y=0.6, z=0, visibility=1.0)
    ankle = KeyPoint(x=0.3, y=0.8, z=0, visibility=1.0)  # 足首が後方
    lower_leg_angle = calculate_lower_leg_angle(knee, ankle, "test")
    print(f"離地時（足首が後方）: {lower_leg_angle:.1f}° (期待値: 正値) {'✅' if lower_leg_angle > 0 else '❌'}")
    
    # 接地時（足首が前方）
    ankle = KeyPoint(x=0.7, y=0.8, z=0, visibility=1.0)  # 足首が前方
    lower_leg_angle = calculate_lower_leg_angle(knee, ankle, "test")
    print(f"接地時（足首が前方）: {lower_leg_angle:.1f}° (期待値: 負値) {'✅' if lower_leg_angle < 0 else '❌'}")

if __name__ == "__main__":
    print("🧪 最終修正の検証")
    verify_final_angles()
    print("\n✅ 検証完了")
