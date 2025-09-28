#!/usr/bin/env python3
"""
左右大腿角度・左右下腿角度の統合グラフ生成スクリプト
4つの角度推移を1つのグラフに表示
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import math

def generate_realistic_leg_angle_data():
    """
    リアルなランニング脚部角度データを生成
    左右大腿角度、左右下腿角度の4つの角度を生成
    """
    print("🦵 左右大腿・下腿角度データを生成中...")
    
    fps = 30.0
    duration = 10.0  # 10秒間
    total_frames = int(duration * fps)
    
    timestamps = []
    left_thigh_angles = []
    right_thigh_angles = []
    left_lower_leg_angles = []
    right_lower_leg_angles = []
    
    # ランニングパラメータ
    step_frequency = 2.6  # 2.6 Hz (156 steps/min)
    
    print(f"📊 {total_frames}フレーム（{duration}秒）、ケイデンス {step_frequency * 60:.0f} steps/min")
    
    for frame in range(total_frames):
        time = frame / fps
        
        # 左右の位相差（左右の足が交互に動く）
        left_phase = (time * step_frequency) % 1.0
        right_phase = (left_phase + 0.5) % 1.0
        
        # 大腿角度の計算（膝の前後動作）
        # 前方スイング時に正値、後方時に負値
        left_thigh_base = 15.0  # 基本前傾角度
        right_thigh_base = 15.0
        
        # ランニングサイクルによる変動
        left_thigh_swing = 25.0 * np.sin(left_phase * 2 * np.pi)
        right_thigh_swing = 25.0 * np.sin(right_phase * 2 * np.pi)
        
        # 個人差とノイズ
        left_thigh_noise = np.random.normal(0, 1.5)
        right_thigh_noise = np.random.normal(0, 1.5)
        
        left_thigh = left_thigh_base + left_thigh_swing + left_thigh_noise
        right_thigh = right_thigh_base + right_thigh_swing + right_thigh_noise
        
        # 下腿角度の計算（膝の屈曲伸展）
        # 屈曲時に負値、伸展時に正値
        left_lower_base = -10.0  # 基本角度
        right_lower_base = -10.0
        
        # 膝屈曲のパターン（遊脚期に大きく屈曲）
        if 0.1 <= left_phase <= 0.6:  # 遊脚期
            left_lower_flex = -40.0 * np.sin((left_phase - 0.1) / 0.5 * np.pi)
        else:  # 立脚期
            left_lower_flex = -5.0 * np.sin((left_phase - 0.6) / 0.5 * np.pi)
            
        if 0.1 <= right_phase <= 0.6:  # 遊脚期
            right_lower_flex = -40.0 * np.sin((right_phase - 0.1) / 0.5 * np.pi)
        else:  # 立脚期
            right_lower_flex = -5.0 * np.sin((right_phase - 0.6) / 0.5 * np.pi)
        
        # ノイズ追加
        left_lower_noise = np.random.normal(0, 2.0)
        right_lower_noise = np.random.normal(0, 2.0)
        
        left_lower_leg = left_lower_base + left_lower_flex + left_lower_noise
        right_lower_leg = right_lower_base + right_lower_flex + right_lower_noise
        
        # 物理的制約を適用
        left_thigh = np.clip(left_thigh, -20, 50)
        right_thigh = np.clip(right_thigh, -20, 50)
        left_lower_leg = np.clip(left_lower_leg, -60, 20)
        right_lower_leg = np.clip(right_lower_leg, -60, 20)
        
        timestamps.append(time)
        left_thigh_angles.append(left_thigh)
        right_thigh_angles.append(right_thigh)
        left_lower_leg_angles.append(left_lower_leg)
        right_lower_leg_angles.append(right_lower_leg)
    
    print(f"✅ {len(timestamps)}個のデータポイント × 4角度を生成")
    
    return {
        'timestamps': timestamps,
        'left_thigh': left_thigh_angles,
        'right_thigh': right_thigh_angles,
        'left_lower_leg': left_lower_leg_angles,
        'right_lower_leg': right_lower_leg_angles
    }

def create_leg_angles_chart(data: Dict, save_path: str = "leg_angles_progression.png"):
    """
    左右大腿・下腿角度の統合グラフを生成
    """
    print("📈 左右大腿・下腿角度統合グラフを生成中...")
    
    # 日本語フォント設定
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
    
    # 図のサイズとスタイル設定
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('white')
    
    timestamps = data['timestamps']
    
    # 4つの角度をプロット（色分けと線種を工夫）
    ax.plot(timestamps, data['left_thigh'], 'b-', linewidth=2.5, alpha=0.8, 
            label='左大腿角度', marker='o', markersize=2, markevery=20)
    ax.plot(timestamps, data['right_thigh'], 'r-', linewidth=2.5, alpha=0.8, 
            label='右大腿角度', marker='s', markersize=2, markevery=20)
    ax.plot(timestamps, data['left_lower_leg'], 'g--', linewidth=2.5, alpha=0.8, 
            label='左下腿角度', marker='^', markersize=2, markevery=20)
    ax.plot(timestamps, data['right_lower_leg'], 'm--', linewidth=2.5, alpha=0.8, 
            label='右下腿角度', marker='d', markersize=2, markevery=20)
    
    # 基準線を追加
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.6, linewidth=1, label='基準線 (0°)')
    
    # 理想的な範囲の表示（大腿角度用）
    ax.fill_between(timestamps, 10, 30, alpha=0.1, color='blue', label='大腿理想範囲')
    
    # 理想的な範囲の表示（下腿角度用）
    ax.fill_between(timestamps, -50, -10, alpha=0.1, color='green', label='下腿理想範囲')
    
    # 軸の設定
    ax.set_xlabel('時間 (秒)', fontsize=14, fontweight='bold')
    ax.set_ylabel('角度 (度)', fontsize=14, fontweight='bold')
    ax.set_title('ランニング時の左右大腿・下腿角度推移\n(大腿: 前方スイング=正値, 下腿: 膝屈曲=負値)', 
                fontsize=16, fontweight='bold', pad=20)
    
    # グリッドの設定
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 凡例の設定（2列で表示）
    ax.legend(loc='upper right', fontsize=11, frameon=True, 
             fancybox=True, shadow=True, framealpha=0.9, ncol=2)
    
    # Y軸の範囲を適切に設定
    all_angles = (data['left_thigh'] + data['right_thigh'] + 
                  data['left_lower_leg'] + data['right_lower_leg'])
    if all_angles:
        y_margin = (max(all_angles) - min(all_angles)) * 0.05
        ax.set_ylim(min(all_angles) - y_margin, max(all_angles) + y_margin)
    
    # X軸の範囲
    ax.set_xlim(0, max(timestamps))
    
    # 統計情報を表示
    stats_text = f"""統計情報:
左大腿: 平均 {np.mean(data['left_thigh']):.1f}° (±{np.std(data['left_thigh']):.1f}°)
右大腿: 平均 {np.mean(data['right_thigh']):.1f}° (±{np.std(data['right_thigh']):.1f}°)
左下腿: 平均 {np.mean(data['left_lower_leg']):.1f}° (±{np.std(data['left_lower_leg']):.1f}°)
右下腿: 平均 {np.mean(data['right_lower_leg']):.1f}° (±{np.std(data['right_lower_leg']):.1f}°)
時間: {max(timestamps):.1f}秒"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', 
            facecolor='lightblue', alpha=0.8))
    
    # レイアウトの調整
    plt.tight_layout()
    
    # 高品質で保存
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"📊 脚部角度統合グラフを保存: {save_path}")
    return save_path

def analyze_leg_symmetry(data: Dict):
    """
    左右脚の対称性を分析
    """
    print("\n⚖️ 左右脚対称性分析:")
    
    # 大腿角度の左右差
    thigh_diff = np.array(data['left_thigh']) - np.array(data['right_thigh'])
    thigh_asymmetry = np.std(thigh_diff)
    
    # 下腿角度の左右差
    lower_leg_diff = np.array(data['left_lower_leg']) - np.array(data['right_lower_leg'])
    lower_leg_asymmetry = np.std(lower_leg_diff)
    
    print(f"   大腿角度非対称性: ±{thigh_asymmetry:.1f}°")
    print(f"   下腿角度非対称性: ±{lower_leg_asymmetry:.1f}°")
    
    if thigh_asymmetry < 3.0:
        print("   ✅ 大腿角度: 良好な左右対称性")
    elif thigh_asymmetry < 5.0:
        print("   ⚠️ 大腿角度: 軽度の非対称性")
    else:
        print("   ❌ 大腿角度: 明らかな非対称性")
    
    if lower_leg_asymmetry < 4.0:
        print("   ✅ 下腿角度: 良好な左右対称性")
    elif lower_leg_asymmetry < 6.0:
        print("   ⚠️ 下腿角度: 軽度の非対称性")
    else:
        print("   ❌ 下腿角度: 明らかな非対称性")

def main():
    """メイン処理"""
    print("🎯 左右大腿・下腿角度統合グラフ生成開始")
    print("=" * 55)
    
    # 1. データ生成
    data = generate_realistic_leg_angle_data()
    
    # 2. グラフ生成
    chart_path = create_leg_angles_chart(data)
    
    # 3. 対称性分析
    analyze_leg_symmetry(data)
    
    # 4. 結果サマリー
    print("\n" + "=" * 55)
    print("📊 脚部角度分析結果:")
    print(f"   解析時間: {data['timestamps'][-1]:.1f}秒")
    print(f"   左大腿平均: {np.mean(data['left_thigh']):.1f}°")
    print(f"   右大腿平均: {np.mean(data['right_thigh']):.1f}°")
    print(f"   左下腿平均: {np.mean(data['left_lower_leg']):.1f}°")
    print(f"   右下腿平均: {np.mean(data['right_lower_leg']):.1f}°")
    print(f"📈 グラフファイル: {chart_path}")
    
    print("\n🦵 フォーム評価:")
    # 大腿角度評価
    avg_thigh = (np.mean(data['left_thigh']) + np.mean(data['right_thigh'])) / 2
    if 15 <= avg_thigh <= 25:
        print("✅ 大腿角度: 理想的なスイング動作")
    elif avg_thigh < 15:
        print("⚠️ 大腿角度: スイングが小さめ - より大きな歩幅を意識してください")
    else:
        print("⚠️ 大腿角度: オーバーストライドの可能性")
    
    # 下腿角度評価
    avg_lower_leg = (np.mean(data['left_lower_leg']) + np.mean(data['right_lower_leg'])) / 2
    if -35 <= avg_lower_leg <= -15:
        print("✅ 下腿角度: 適切な膝屈曲")
    elif avg_lower_leg > -15:
        print("⚠️ 下腿角度: 膝屈曲が不足 - より高い膝上げを意識してください")
    else:
        print("⚠️ 下腿角度: 過度な膝屈曲")

if __name__ == "__main__":
    main()
