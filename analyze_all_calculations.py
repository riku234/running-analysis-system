#!/usr/bin/env python3
"""
全ての角度計算の立式とベクトルの向きを詳細に分析するスクリプト
"""

import sys
import numpy as np

# プロジェクトのパスを追加
sys.path.append('backend/services/feature_extraction/app')

try:
    from main import calculate_absolute_angle_with_vertical, KeyPoint
    print("✅ モジュールのインポートが成功しました")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

def analyze_all_angle_calculations():
    """全ての角度計算の立式とベクトルの向きを詳細分析"""
    print("🔍 全ての角度計算の立式とベクトルの向き分析")
    print("=" * 80)
    
    print("📐 MediaPipe座標系:")
    print("- X軸: 左(0.0) → 右(1.0)")
    print("- Y軸: 上(0.0) → 下(1.0)")
    print("- 進行方向: 左→右 (X軸正方向)")
    print("- 座標原点: 左上角")
    print()
    
    # ===================================================================
    # 1. 体幹角度の分析
    # ===================================================================
    print("🏃 1. 体幹角度の立式分析")
    print("-" * 50)
    print("定義: 腰から肩への直線ベクトルと鉛直軸がなす角度")
    print("立式:")
    print("  1. 肩中心点: (left_shoulder + right_shoulder) / 2")
    print("  2. 股関節中心点: (left_hip + right_hip) / 2") 
    print("  3. 体幹ベクトル = 肩中心点 - 股関節中心点")
    print("  4. 角度 = atan2(体幹ベクトル.x, -体幹ベクトル.y)")
    print("  5. forward_positive=True: 前方（右）向きを正値とする")
    print()
    
    # テストケース
    trunk_cases = [
        {
            "name": "直立姿勢",
            "shoulder": (0.5, 0.3),
            "hip": (0.5, 0.7),
            "expected": "約0°"
        },
        {
            "name": "前傾姿勢（肩が前方/右側）",
            "shoulder": (0.6, 0.3),
            "hip": (0.5, 0.7),
            "expected": "正値"
        },
        {
            "name": "後傾姿勢（肩が後方/左側）",
            "shoulder": (0.4, 0.3),
            "hip": (0.5, 0.7),
            "expected": "負値"
        }
    ]
    
    for case in trunk_cases:
        print(f"テストケース: {case['name']} (期待値: {case['expected']})")
        
        # ベクトル計算
        trunk_vector = np.array([
            case["shoulder"][0] - case["hip"][0],  # X成分
            case["shoulder"][1] - case["hip"][1]   # Y成分
        ])
        
        print(f"  肩中心点: {case['shoulder']}")
        print(f"  股関節中心点: {case['hip']}")
        print(f"  体幹ベクトル: [{trunk_vector[0]:.3f}, {trunk_vector[1]:.3f}]")
        print(f"  ベクトルの向き: X成分={trunk_vector[0]:.3f} ({'右' if trunk_vector[0] > 0 else '左'}), Y成分={trunk_vector[1]:.3f} ({'下' if trunk_vector[1] > 0 else '上'})")
        
        angle = calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=True)
        print(f"  計算結果: {angle:.1f}°")
        print()
    
    # ===================================================================
    # 2. 大腿角度の分析
    # ===================================================================
    print("🦵 2. 大腿角度の立式分析")
    print("-" * 50)
    print("定義: 膝関節点から股関節点に向かうベクトルと鉛直軸がなす角度")
    print("立式:")
    print("  1. 大腿ベクトル = 股関節点 - 膝関節点")
    print("  2. 角度 = atan2(大腿ベクトル.x, -大腿ベクトル.y)")
    print("  3. forward_positive=True: 前方（右）向きを正値とする")
    print("期待値: 膝が後方で正値、膝が前方で負値")
    print()
    
    thigh_cases = [
        {
            "name": "離地時（膝が後方/左側）",
            "hip": (0.5, 0.5),
            "knee": (0.3, 0.6),  # 膝がX軸負方向（後方）
            "expected": "正値"
        },
        {
            "name": "接地時（膝が前方/右側）",
            "hip": (0.5, 0.5),
            "knee": (0.7, 0.6),  # 膝がX軸正方向（前方）
            "expected": "負値"
        }
    ]
    
    for case in thigh_cases:
        print(f"テストケース: {case['name']} (期待値: {case['expected']})")
        
        # ベクトル計算
        thigh_vector = np.array([
            case["hip"][0] - case["knee"][0],  # X成分
            case["hip"][1] - case["knee"][1]   # Y成分
        ])
        
        print(f"  股関節点: {case['hip']}")
        print(f"  膝関節点: {case['knee']}")
        print(f"  大腿ベクトル: [{thigh_vector[0]:.3f}, {thigh_vector[1]:.3f}]")
        print(f"  ベクトルの向き: X成分={thigh_vector[0]:.3f} ({'右' if thigh_vector[0] > 0 else '左'}), Y成分={thigh_vector[1]:.3f} ({'下' if thigh_vector[1] > 0 else '上'})")
        
        angle_true = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=True)
        angle_false = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        
        print(f"  forward_positive=True: {angle_true:.1f}°")
        print(f"  forward_positive=False: {angle_false:.1f}°")
        print(f"  -angle_true: {-angle_true:.1f}°")
        print(f"  -angle_false: {-angle_false:.1f}°")
        
        # 期待値に合うオプションを特定
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
    
    # ===================================================================
    # 3. 下腿角度の分析
    # ===================================================================
    print("🦵 3. 下腿角度の立式分析")
    print("-" * 50)
    print("定義: 足関節点から膝関節点に向かうベクトルと鉛直軸がなす角度")
    print("立式:")
    print("  1. 下腿ベクトル = 膝関節点 - 足関節点")
    print("  2. 角度 = atan2(下腿ベクトル.x, -下腿ベクトル.y)")
    print("  3. forward_positive=True: 前方（右）向きを正値とする")
    print("期待値: 足首が後方で正値、足首が前方で負値")
    print()
    
    lower_leg_cases = [
        {
            "name": "離地時（足首が後方/左側）",
            "knee": (0.5, 0.6),
            "ankle": (0.3, 0.8),  # 足首がX軸負方向（後方）
            "expected": "正値"
        },
        {
            "name": "接地時（足首が前方/右側）",
            "knee": (0.5, 0.6),
            "ankle": (0.7, 0.8),  # 足首がX軸正方向（前方）
            "expected": "負値"
        }
    ]
    
    for case in lower_leg_cases:
        print(f"テストケース: {case['name']} (期待値: {case['expected']})")
        
        # ベクトル計算
        lower_leg_vector = np.array([
            case["knee"][0] - case["ankle"][0],  # X成分
            case["knee"][1] - case["ankle"][1]   # Y成分
        ])
        
        print(f"  膝関節点: {case['knee']}")
        print(f"  足関節点: {case['ankle']}")
        print(f"  下腿ベクトル: [{lower_leg_vector[0]:.3f}, {lower_leg_vector[1]:.3f}]")
        print(f"  ベクトルの向き: X成分={lower_leg_vector[0]:.3f} ({'右' if lower_leg_vector[0] > 0 else '左'}), Y成分={lower_leg_vector[1]:.3f} ({'下' if lower_leg_vector[1] > 0 else '上'})")
        
        angle_true = calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=True)
        angle_false = calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=False)
        
        print(f"  forward_positive=True: {angle_true:.1f}°")
        print(f"  forward_positive=False: {angle_false:.1f}°")
        print(f"  -angle_true: {-angle_true:.1f}°")
        print(f"  -angle_false: {-angle_false:.1f}°")
        
        # 期待値に合うオプションを特定
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
    
    # ===================================================================
    # 4. 重心上下動の分析
    # ===================================================================
    print("📏 4. 重心上下動の立式分析")
    print("-" * 50)
    print("定義: 重心位置の上下動変動を身長で正規化した比率")
    print("立式:")
    print("  1. 重心位置 = (left_hip + right_hip) / 2 のY座標")
    print("  2. 身長推定 = 下腿長 + 大腿長 + 体幹長 + 頭部長")
    print("  3. 上下動 = max(重心Y) - min(重心Y)")
    print("  4. 上下動比率 = 上下動 / 推定身長")
    print("座標系: Y軸は上(0) → 下(1) なので、Y値が大きいほど下位置")
    print()

def analyze_atan2_function():
    """atan2関数の動作を詳細分析"""
    print("🔢 5. atan2関数の詳細分析")
    print("-" * 50)
    print("atan2(y, x)の動作:")
    print("- ベクトル(x, y)の角度を-π～+πの範囲で返す")
    print("- 基準軸は正のX軸（右向き）")
    print("- 反時計回りが正の角度")
    print()
    
    print("calculate_absolute_angle_with_vertical(vector, forward_positive)の動作:")
    print("- atan2(vector[0], -vector[1]) を計算")
    print("- 基準軸は負のY軸（上向き）に変換")
    print("- forward_positive=True: そのまま")
    print("- forward_positive=False: 符号反転")
    print()
    
    # テストベクトルで確認
    test_vectors = [
        ([1, 0], "右向き"),
        ([-1, 0], "左向き"),
        ([0, -1], "上向き"),
        ([0, 1], "下向き"),
        ([1, -1], "右上向き"),
        ([-1, -1], "左上向き"),
        ([1, 1], "右下向き"),
        ([-1, 1], "左下向き")
    ]
    
    print("各方向のベクトルに対するatan2結果:")
    for vector, direction in test_vectors:
        raw_atan2 = np.degrees(np.arctan2(vector[0], -vector[1]))
        angle_true = calculate_absolute_angle_with_vertical(np.array(vector), forward_positive=True)
        angle_false = calculate_absolute_angle_with_vertical(np.array(vector), forward_positive=False)
        
        print(f"  {direction:8} {vector}: raw_atan2={raw_atan2:6.1f}°, True={angle_true:6.1f}°, False={angle_false:6.1f}°")

if __name__ == "__main__":
    analyze_all_angle_calculations()
    analyze_atan2_function()
    
    print("\n" + "=" * 80)
    print("📋 推奨される修正案:")
    print("1. 大腿角度: forward_positive=False を使用")
    print("2. 下腿角度: forward_positive=False を使用") 
    print("3. または、forward_positive=True で計算して明示的に符号反転")
    print("=" * 80)
