#!/usr/bin/env python3
"""
左右大腿角度のみに特化したクリーンで見やすいグラフ生成
視認性を最優先に設計
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
import math

def generate_clear_thigh_angle_data():
    """
    視認性重視の左右大腿角度データを生成
    実装済み符号基準を使用
    """
    print("🦵 左右大腿角度データ（視認性重視）を生成中...")
    
    fps = 30.0
    duration = 12.0  # 少し長めの解析時間
    total_frames = int(duration * fps)
    
    timestamps = []
    left_thigh_angles = []
    right_thigh_angles = []
    
    step_frequency = 2.4  # 144 steps/min（やや遅めで見やすく）
    
    print(f"📊 {total_frames}フレーム（{duration}秒）、ケイデンス {step_frequency * 60:.0f} steps/min")
    print("🔢 実装済み符号基準: 膝が後方=正値（遊脚期）, 膝が前方=負値（接地期）")
    
    for frame in range(total_frames):
        time = frame / fps
        
        # 左右の位相差（0.5で完全に逆位相）
        left_phase = (time * step_frequency) % 1.0
        right_phase = (left_phase + 0.5) % 1.0
        
        # === 左大腿角度計算 ===
        # より明確なランニングサイクル
        if 0.0 <= left_phase <= 0.2:  # 接地期初期（膝前方）
            left_base = -12.0
        elif 0.2 <= left_phase <= 0.4:  # 立脚期（膝やや前方）
            left_base = -8.0
        elif 0.4 <= left_phase <= 0.8:  # 遊脚期（膝後方スイング）
            swing_phase = (left_phase - 0.4) / 0.4
            left_base = -8.0 + 20.0 * np.sin(swing_phase * np.pi)  # 最大12度後方
        else:  # 接地準備（膝前方に戻る）
            prep_phase = (left_phase - 0.8) / 0.2
            left_base = 12.0 * (1 - prep_phase) - 12.0 * prep_phase
        
        # 個人差とノイズ（控えめに）
        left_individual = np.random.normal(0, 1.0)
        left_thigh_angle = left_base + left_individual
        
        # === 右大腿角度計算 ===
        if 0.0 <= right_phase <= 0.2:  # 接地期初期（膝前方）
            right_base = -12.0
        elif 0.2 <= right_phase <= 0.4:  # 立脚期（膝やや前方）
            right_base = -8.0
        elif 0.4 <= right_phase <= 0.8:  # 遊脚期（膝後方スイング）
            swing_phase = (right_phase - 0.4) / 0.4
            right_base = -8.0 + 20.0 * np.sin(swing_phase * np.pi)  # 最大12度後方
        else:  # 接地準備（膝前方に戻る）
            prep_phase = (right_phase - 0.8) / 0.2
            right_base = 12.0 * (1 - prep_phase) - 12.0 * prep_phase
        
        # 個人差とノイズ（控えめに）
        right_individual = np.random.normal(0, 1.0)
        right_thigh_angle = right_base + right_individual
        
        # 物理的制約
        left_thigh_angle = np.clip(left_thigh_angle, -20, 20)
        right_thigh_angle = np.clip(right_thigh_angle, -20, 20)
        
        timestamps.append(time)
        left_thigh_angles.append(left_thigh_angle)
        right_thigh_angles.append(right_thigh_angle)
    
    print(f"✅ {len(timestamps)}個のデータポイント（大腿角度のみ）を生成")
    
    return {
        'timestamps': timestamps,
        'left_thigh': left_thigh_angles,
        'right_thigh': right_thigh_angles
    }

def create_clear_thigh_angles_chart(data: Dict, save_path: str = "clear_thigh_angles.png"):
    """
    視認性を最優先にした左右大腿角度グラフ
    """
    print("📈 視認性重視の左右大腿角度グラフを生成中...")
    
    # フォント設定（大きめで読みやすく）
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
    plt.rcParams['font.size'] = 12
    
    # 大きめの図サイズ
    fig, ax = plt.subplots(figsize=(18, 10))
    fig.patch.set_facecolor('white')
    
    timestamps = data['timestamps']
    
    # 明確に区別できる色と線種
    ax.plot(timestamps, data['left_thigh'], 
            color='#2E86C1', linewidth=4, alpha=0.9, 
            label='左大腿角度', marker='o', markersize=4, markevery=25)
    
    ax.plot(timestamps, data['right_thigh'], 
            color='#E74C3C', linewidth=4, alpha=0.9, 
            label='右大腿角度', marker='s', markersize=4, markevery=25)
    
    # 移動平均を追加（スムージング）
    if len(data['left_thigh']) > 20:
        window = 25
        left_smooth = np.convolve(data['left_thigh'], np.ones(window) / window, mode='same')
        right_smooth = np.convolve(data['right_thigh'], np.ones(window) / window, mode='same')
        
        ax.plot(timestamps, left_smooth, 
                color='#1F618D', linewidth=2, alpha=0.7, linestyle='--',
                label='左大腿（移動平均）')
        ax.plot(timestamps, right_smooth, 
                color='#C0392B', linewidth=2, alpha=0.7, linestyle='--',
                label='右大腿（移動平均）')
    
    # 明確な基準線とガイド
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=2, label='基準線 (0°)')
    ax.axhline(y=10, color='green', linestyle=':', alpha=0.7, linewidth=2, label='遊脚期目標 (+10°)')
    ax.axhline(y=-10, color='orange', linestyle=':', alpha=0.7, linewidth=2, label='接地期目標 (-10°)')
    
    # 理想範囲をより明確に表示
    ax.fill_between(timestamps, 5, 15, alpha=0.15, color='green', label='遊脚期理想範囲')
    ax.fill_between(timestamps, -15, -5, alpha=0.15, color='orange', label='接地期理想範囲')
    
    # 軸とタイトル（大きめのフォント）
    ax.set_xlabel('時間 (秒)', fontsize=16, fontweight='bold')
    ax.set_ylabel('大腿角度 (度)', fontsize=16, fontweight='bold')
    ax.set_title('左右大腿角度推移 - 実装済み符号基準\n膝が後方 = 正値（遊脚期）｜膝が前方 = 負値（接地期）', 
                fontsize=18, fontweight='bold', pad=25)
    
    # グリッド（見やすく）
    ax.grid(True, alpha=0.4, linestyle='-', linewidth=0.8)
    ax.set_axisbelow(True)
    
    # 凡例（大きく、見やすい位置）
    ax.legend(loc='upper right', fontsize=13, frameon=True, 
             fancybox=True, shadow=True, framealpha=0.95, ncol=2)
    
    # Y軸の範囲を適切に設定（余裕を持って）
    all_angles = data['left_thigh'] + data['right_thigh']
    y_margin = (max(all_angles) - min(all_angles)) * 0.1
    ax.set_ylim(min(all_angles) - y_margin, max(all_angles) + y_margin)
    
    # X軸の範囲
    ax.set_xlim(0, max(timestamps))
    
    # 統計情報（見やすい位置とサイズ）
    left_mean = np.mean(data['left_thigh'])
    right_mean = np.mean(data['right_thigh'])
    left_std = np.std(data['left_thigh'])
    right_std = np.std(data['right_thigh'])
    
    stats_text = f"""大腿角度統計 (実装済み符号基準):
左大腿: 平均 {left_mean:.1f}° (±{left_std:.1f}°)
右大腿: 平均 {right_mean:.1f}° (±{right_std:.1f}°)
左右差: {abs(left_mean - right_mean):.1f}°
解析時間: {max(timestamps):.1f}秒

符号規則:
• 正値 = 膝が股関節より後方（遊脚期）
• 負値 = 膝が股関節より前方（接地期）"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.8', 
            facecolor='lightblue', alpha=0.9, edgecolor='navy'))
    
    # より細かい目盛り設定
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    # レイアウトの最適化
    plt.tight_layout()
    
    # 高品質で保存
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"📊 視認性重視の大腿角度グラフ保存: {save_path}")
    return save_path

def analyze_thigh_symmetry(data: Dict):
    """
    左右大腿角度の対称性と動作パターンを詳細分析
    """
    print("\n⚖️ 左右大腿角度の詳細分析:")
    
    left_angles = np.array(data['left_thigh'])
    right_angles = np.array(data['right_thigh'])
    
    # 基本統計
    left_mean = np.mean(left_angles)
    right_mean = np.mean(right_angles)
    left_std = np.std(left_angles)
    right_std = np.std(right_angles)
    
    # 左右差分析
    lr_difference = left_angles - right_angles
    avg_lr_diff = np.mean(lr_difference)
    lr_asymmetry = np.std(lr_difference)
    
    print(f"   左大腿平均: {left_mean:.1f}° (±{left_std:.1f}°)")
    print(f"   右大腿平均: {right_mean:.1f}° (±{right_std:.1f}°)")
    print(f"   平均左右差: {avg_lr_diff:.1f}°")
    print(f"   左右非対称性: ±{lr_asymmetry:.1f}°")
    
    # 対称性評価
    if lr_asymmetry < 2.0:
        print("   ✅ 優秀な左右対称性")
    elif lr_asymmetry < 3.5:
        print("   ✅ 良好な左右対称性")
    elif lr_asymmetry < 5.0:
        print("   ⚠️ 軽度の左右非対称")
    else:
        print("   ❌ 明らかな左右非対称")
    
    # 動作範囲分析
    left_range = np.max(left_angles) - np.min(left_angles)
    right_range = np.max(right_angles) - np.min(right_angles)
    
    print(f"\n📐 動作範囲分析:")
    print(f"   左大腿動作範囲: {left_range:.1f}°")
    print(f"   右大腿動作範囲: {right_range:.1f}°")
    
    # 理想的な動作範囲は15-25度程度
    avg_range = (left_range + right_range) / 2
    if avg_range < 15:
        print("   ⚠️ 動作範囲が小さめ - より大きなスイングを意識してください")
    elif avg_range > 30:
        print("   ⚠️ 動作範囲が大きすぎる - オーバーストライドの可能性")
    else:
        print("   ✅ 適切な動作範囲")

def main():
    """メイン処理"""
    print("🎯 視認性重視の左右大腿角度グラフ生成")
    print("=" * 60)
    
    # データ生成
    thigh_data = generate_clear_thigh_angle_data()
    
    # 視認性重視のグラフ生成
    chart_path = create_clear_thigh_angles_chart(thigh_data)
    
    # 詳細分析
    analyze_thigh_symmetry(thigh_data)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 左右大腿角度分析結果:")
    print(f"   解析時間: {thigh_data['timestamps'][-1]:.1f}秒")
    print(f"   データポイント数: {len(thigh_data['timestamps'])}")
    print(f"📈 生成グラフ: {chart_path}")
    
    # フォーム評価
    left_mean = np.mean(thigh_data['left_thigh'])
    right_mean = np.mean(thigh_data['right_thigh'])
    overall_mean = (left_mean + right_mean) / 2
    
    print(f"\n🏃‍♂️ 大腿角度フォーム評価:")
    print(f"   全体平均角度: {overall_mean:.1f}°")
    
    if -5 <= overall_mean <= 5:
        print("   ✅ バランスの良い大腿角度パターン")
    elif overall_mean > 5:
        print("   ⚠️ 後方スイング傾向 - 歩幅が大きめ")
    else:
        print("   ⚠️ 前方傾向 - より積極的な膝上げを意識してください")

if __name__ == "__main__":
    main()
