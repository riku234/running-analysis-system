#!/usr/bin/env python3
"""
角度計算の最終検証スクリプト
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
        KeyPoint,
        calculate_absolute_angle_with_vertical
    )
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def test_angle_calculation_logic():
    """角度計算の論理検証"""
    print("\n🧪 角度計算論理の検証")
    print("=" * 60)
    
    # ログから実際の値を使用
    print("📊 実際のログデータを使用:")
    
    # 左大腿: [0.028, -0.090] → 膝が前方 → 負値であるべき
    left_thigh_vector = np.array([0.028, -0.090])
    print(f"左大腿ベクトル: {left_thigh_vector} (X > 0 = 膝が前方)")
    
    # forward_positive=False の場合
    angle_false = calculate_absolute_angle_with_vertical(left_thigh_vector, forward_positive=False)
    print(f"forward_positive=False: {angle_false:.1f}°")
    print(f"期待値: 負値（膝が前方） {'✅' if angle_false < 0 else '❌'}")
    
    # 右大腿: [-0.040, -0.083] → 膝が後方 → 正値であるべき  
    right_thigh_vector = np.array([-0.040, -0.083])
    print(f"\n右大腿ベクトル: {right_thigh_vector} (X < 0 = 膝が後方)")
    
    angle_false2 = calculate_absolute_angle_with_vertical(right_thigh_vector, forward_positive=False)
    print(f"forward_positive=False: {angle_false2:.1f}°")
    print(f"期待値: 正値（膝が後方） {'✅' if angle_false2 > 0 else '❌'}")
    
    print(f"\n📋 結論:")
    if angle_false < 0 and angle_false2 > 0:
        print("✅ forward_positive=False が正しい符号を生成")
    else:
        print("❌ まだ符号が逆転している")
        print("🔧 考えられる解決案:")
        print("   1. forward_positive=True に変更")
        print("   2. 明示的に符号反転")
        
        # forward_positive=True をテスト
        angle_true = calculate_absolute_angle_with_vertical(left_thigh_vector, forward_positive=True)
        angle_true2 = calculate_absolute_angle_with_vertical(right_thigh_vector, forward_positive=True)
        
        print(f"\n🧪 forward_positive=True テスト:")
        print(f"左大腿 (膝前方): {angle_true:.1f}° {'✅' if angle_true < 0 else '❌'}")
        print(f"右大腿 (膝後方): {angle_true2:.1f}° {'✅' if angle_true2 > 0 else '❌'}")
        
        if angle_true < 0 and angle_true2 > 0:
            print("🎯 forward_positive=True が正解！")

if __name__ == "__main__":
    test_angle_calculation_logic()
