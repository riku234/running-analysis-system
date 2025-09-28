#!/usr/bin/env python3
"""
シンプルな体幹角度推移グラフ生成スクリプト
角度の推移のみに特化したクリーンなビジュアライゼーション
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import math

def generate_realistic_trunk_angle_data():
    """
    リアルなランニング体幹角度データを生成
    """
    print("🏃‍♂️ シンプルな体幹角度推移データを生成中...")
    
    fps = 30.0
    duration = 10.0  # 10秒間
    total_frames = int(duration * fps)
    
    timestamps = []
    trunk_angles = []
    
    # より現実的なランニングパラメータ
    step_frequency = 2.7  # 2.7 Hz (162 steps/min)
    base_lean = -5.5  # 基本前傾角度
    
    print(f"📊 {total_frames}フレーム（{duration}秒）、ケイデンス {step_frequency * 60:.0f} steps/min")
    
    for frame in range(total_frames):
        time = frame / fps
        
        # ランニングサイクルによる体幹角度の変動
        cycle_phase = (time * step_frequency) % 1.0
        
        # 主要な変動要素
        cycle_variation = 1.5 * np.sin(cycle_phase * 2 * np.pi)  # ランニングサイクル
        breathing_variation = 0.3 * np.sin(time * 0.4 * 2 * np.pi)  # 呼吸
        fatigue_drift = time * 0.2  # 疲労による徐々の変化
        micro_adjustments = 0.2 * np.sin(time * 1.8 * 2 * np.pi)  # 微細な調整
        noise = np.random.normal(0, 0.15)  # 測定ノイズ
        
        # 最終的な体幹角度
        trunk_angle = (base_lean + cycle_variation + breathing_variation + 
                      fatigue_drift + micro_adjustments + noise)
        
        # 物理的制約
        trunk_angle = np.clip(trunk_angle, -12.0, 5.0)
        
        timestamps.append(time)
        trunk_angles.append(trunk_angle)
    
    print(f"✅ {len(trunk_angles)}個のデータポイントを生成")
    return timestamps, trunk_angles

def create_simple_trunk_angle_chart(timestamps: List[float], angles: List[float], 
                                   save_path: str = "simple_trunk_angle_progression.png"):
    """
    シンプルな体幹角度推移グラフを生成
    """
    print("📈 シンプルな体幹角度推移グラフを生成中...")
    
    # 日本語フォント設定
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
    
    # 図のサイズとスタイル設定
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # メインの角度推移をプロット
    ax.plot(timestamps, angles, 'b-', linewidth=2.5, alpha=0.8, label='体幹角度')
    
    # 移動平均を追加（スムージング）
    if len(angles) > 10:
        window_size = 20
        moving_avg = np.convolve(angles, np.ones(window_size) / window_size, mode='same')
        ax.plot(timestamps, moving_avg, 'r-', linewidth=3, alpha=0.9, label='移動平均')
    
    # 理想的な範囲とガイドライン
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.6, linewidth=1, label='直立 (0°)')
    ax.axhline(y=-5, color='green', linestyle='--', alpha=0.8, linewidth=2, label='理想前傾 (-5°)')
    ax.fill_between(timestamps, -8, -2, alpha=0.1, color='green', label='理想範囲 (-2° to -8°)')
    
    # 軸の設定
    ax.set_xlabel('時間 (秒)', fontsize=14, fontweight='bold')
    ax.set_ylabel('体幹角度 (度)', fontsize=14, fontweight='bold')
    ax.set_title('ランニング時の体幹角度推移\n(負値=前傾, 正値=後傾)', 
                fontsize=16, fontweight='bold', pad=20)
    
    # グリッドの設定
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 凡例の設定
    ax.legend(loc='upper right', fontsize=12, frameon=True, 
             fancybox=True, shadow=True, framealpha=0.9)
    
    # Y軸の範囲を適切に設定
    if angles:
        y_margin = (max(angles) - min(angles)) * 0.1
        ax.set_ylim(min(angles) - y_margin, max(angles) + y_margin)
    
    # X軸の範囲
    ax.set_xlim(0, max(timestamps))
    
    # 統計情報を簡潔に表示
    if angles:
        mean_angle = np.mean(angles)
        std_angle = np.std(angles)
        
        stats_text = f"""統計:
平均: {mean_angle:.1f}°
変動: ±{std_angle:.1f}°
時間: {max(timestamps):.1f}秒"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', 
                facecolor='lightblue', alpha=0.8))
    
    # レイアウトの調整
    plt.tight_layout()
    
    # 高品質で保存
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"📊 シンプルな角度推移グラフを保存: {save_path}")
    return save_path

def main():
    """メイン処理"""
    print("🎯 シンプルな体幹角度推移グラフ生成開始")
    print("=" * 50)
    
    # 1. データ生成
    timestamps, trunk_angles = generate_realistic_trunk_angle_data()
    
    # 2. グラフ生成
    chart_path = create_simple_trunk_angle_chart(timestamps, trunk_angles)
    
    # 3. 結果サマリー
    mean_angle = np.mean(trunk_angles)
    std_angle = np.std(trunk_angles)
    
    print("\n" + "=" * 50)
    print("📊 角度推移分析結果:")
    print(f"   解析時間: {timestamps[-1]:.1f}秒")
    print(f"   平均角度: {mean_angle:.2f}°")
    print(f"   角度変動: ±{std_angle:.2f}°")
    print(f"   データ数: {len(trunk_angles)}ポイント")
    print(f"📈 グラフファイル: {chart_path}")
    
    # フォーム評価
    print("\n🏃‍♂️ 簡易フォーム評価:")
    if -8 <= mean_angle <= -2:
        print("✅ 理想的な前傾姿勢です")
    elif mean_angle > -2:
        print("⚠️ もう少し前傾を意識してください")
    else:
        print("⚠️ 前傾が強すぎる可能性があります")

if __name__ == "__main__":
    main()
