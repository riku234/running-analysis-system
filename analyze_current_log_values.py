#!/usr/bin/env python3
"""
現在のログから実際の角度計算を分析するスクリプト
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

def analyze_log_values():
    """ログからの実際の値を分析"""
    print("\n🔍 ログからの実際の値を分析")
    print("=" * 80)
    
    # ログから抽出した実際の値
    log_data = [
        {
            "frame": "例1",
            "left_thigh": ([0.028, -0.090], -17.1),
            "right_thigh": ([-0.040, -0.083], 25.9),
            "left_lower": ([0.051, -0.094], -28.3),
            "right_lower": ([0.022, -0.123], -10.2)
        },
        {
            "frame": "例2", 
            "left_thigh": ([0.029, -0.089], -18.3),
            "right_thigh": ([-0.042, -0.083], 26.9),
            "left_lower": ([0.052, -0.093], -29.4),
            "right_lower": ([0.019, -0.126], -8.7)
        }
    ]
    
    print("📊 ユーザーの期待する符号規則:")
    print("・大腿角度: 膝が後方で正値、膝が前方で負値")
    print("・下腿角度: 足首が後方で正値、足首が前方で負値")
    print()
    
    for data in log_data:
        print(f"🔍 {data['frame']}:")
        
        # 大腿角度の分析
        left_thigh_vec, left_thigh_angle = data["left_thigh"]
        right_thigh_vec, right_thigh_angle = data["right_thigh"]
        
        print(f"  左大腿: ベクトル{left_thigh_vec} → 角度{left_thigh_angle}°")
        print(f"    X={left_thigh_vec[0]:.3f} {'> 0 (膝が前方)' if left_thigh_vec[0] > 0 else '< 0 (膝が後方)'}")
        print(f"    期待値: {'負値' if left_thigh_vec[0] > 0 else '正値'}")
        print(f"    実際値: {left_thigh_angle}° ({'正値' if left_thigh_angle > 0 else '負値'})")
        print(f"    結果: {'✅ 正しい' if (left_thigh_vec[0] > 0 and left_thigh_angle < 0) or (left_thigh_vec[0] < 0 and left_thigh_angle > 0) else '❌ 逆転'}")
        
        print(f"  右大腿: ベクトル{right_thigh_vec} → 角度{right_thigh_angle}°")
        print(f"    X={right_thigh_vec[0]:.3f} {'> 0 (膝が前方)' if right_thigh_vec[0] > 0 else '< 0 (膝が後方)'}")
        print(f"    期待値: {'負値' if right_thigh_vec[0] > 0 else '正値'}")
        print(f"    実際値: {right_thigh_angle}° ({'正値' if right_thigh_angle > 0 else '負値'})")
        print(f"    結果: {'✅ 正しい' if (right_thigh_vec[0] > 0 and right_thigh_angle < 0) or (right_thigh_vec[0] < 0 and right_thigh_angle > 0) else '❌ 逆転'}")
        
        # 下腿角度の分析
        left_lower_vec, left_lower_angle = data["left_lower"]
        right_lower_vec, right_lower_angle = data["right_lower"]
        
        print(f"  左下腿: ベクトル{left_lower_vec} → 角度{left_lower_angle}°")
        print(f"    X={left_lower_vec[0]:.3f} {'> 0 (足首が前方)' if left_lower_vec[0] > 0 else '< 0 (足首が後方)'}")
        print(f"    期待値: {'負値' if left_lower_vec[0] > 0 else '正値'}")
        print(f"    実際値: {left_lower_angle}° ({'正値' if left_lower_angle > 0 else '負値'})")
        print(f"    結果: {'✅ 正しい' if (left_lower_vec[0] > 0 and left_lower_angle < 0) or (left_lower_vec[0] < 0 and left_lower_angle > 0) else '❌ 逆転'}")
        
        print(f"  右下腿: ベクトル{right_lower_vec} → 角度{right_lower_angle}°")
        print(f"    X={right_lower_vec[0]:.3f} {'> 0 (足首が前方)' if right_lower_vec[0] > 0 else '< 0 (足首が後方)'}")
        print(f"    期待値: {'負値' if right_lower_vec[0] > 0 else '正値'}")
        print(f"    実際値: {right_lower_angle}° ({'正値' if right_lower_angle > 0 else '負値'})")
        print(f"    結果: {'✅ 正しい' if (right_lower_vec[0] > 0 and right_lower_angle < 0) or (right_lower_vec[0] < 0 and right_lower_angle > 0) else '❌ 逆転'}")
        print()
    
    print("🔧 解決策の検討:")
    
    # テストデータで各オプションを試す
    test_vector_forward = np.array([0.028, -0.090])  # 膝/足首が前方
    test_vector_backward = np.array([-0.040, -0.083])  # 膝/足首が後方
    
    print(f"テストベクトル（前方）: {test_vector_forward}")
    print(f"テストベクトル（後方）: {test_vector_backward}")
    
    options = [
        ("forward_positive=True", True, 1),
        ("forward_positive=False", False, 1),
        ("forward_positive=True + 符号反転", True, -1),
        ("forward_positive=False + 符号反転", False, -1)
    ]
    
    for option_name, forward_positive, sign_multiplier in options:
        angle_forward = calculate_absolute_angle_with_vertical(test_vector_forward, forward_positive) * sign_multiplier
        angle_backward = calculate_absolute_angle_with_vertical(test_vector_backward, forward_positive) * sign_multiplier
        
        forward_correct = angle_forward < 0  # 前方は負値であるべき
        backward_correct = angle_backward > 0  # 後方は正値であるべき
        
        print(f"  {option_name}:")
        print(f"    前方ベクトル: {angle_forward:.1f}° {'✅' if forward_correct else '❌'}")
        print(f"    後方ベクトル: {angle_backward:.1f}° {'✅' if backward_correct else '❌'}")
        
        if forward_correct and backward_correct:
            print(f"    🎯 この設定が正解！")
        print()

if __name__ == "__main__":
    analyze_log_values()
