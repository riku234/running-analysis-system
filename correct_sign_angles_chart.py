#!/usr/bin/env python3
"""
実装済みの正しい符号基準を使用した角度グラフ生成
実際のfeature_extraction実装と同じ符号規則を適用
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
import math

# 実装済みの符号基準（backend/services/feature_extraction/app/main.py より）
IMPLEMENTED_SIGN_CONVENTIONS = {
    'trunk': {
        'description': '体幹角度（腰→肩ベクトルと鉛直軸）',
        'positive': '後傾（左側への傾き）',
        'negative': '前傾（右側への傾き）',
        'implementation': 'forward_positive=False'
    },
    'thigh': {
        'description': '大腿角度（膝→股関節ベクトルと鉛直軸）',
        'positive': '膝が股関節より後方（離地時）',
        'negative': '膝が股関節より前方（接地時）',
        'implementation': 'forward_positive=True'
    },
    'lower_leg': {
        'description': '下腿角度（足首→膝ベクトルと鉛直軸）',
        'positive': '足首が膝より後方（離地時）',
        'negative': '足首が膝より前方（接地時）',
        'implementation': 'forward_positive=True'
    }
}

def calculate_absolute_angle_with_vertical(vector: np.ndarray, forward_positive: bool = True) -> Optional[float]:
    """
    実装済み関数の複製: ベクトルと鉛直軸がなす角度を計算（atan2ベース）
    backend/services/feature_extraction/app/main.py の実装と同じ
    """
    try:
        # ベクトルの長さをチェック
        length = np.linalg.norm(vector)
        if length == 0:
            return None
        
        # atan2を使用して角度を計算
        angle_rad = np.arctan2(vector[0], -vector[1])  # Y軸は下向きが正なので、上向きは負
        
        # 度数法に変換
        angle_deg = np.degrees(angle_rad)
        
        # forward_positive フラグに基づいて符号を調整
        if not forward_positive:
            angle_deg = -angle_deg  # forward_positive=False の場合は符号を反転
        
        return angle_deg
        
    except Exception:
        return None

def generate_realistic_angle_data_with_correct_signs():
    """
    実装済み符号基準を使用したリアルなランニング角度データを生成
    """
    print("🏃‍♂️ 実装済み符号基準でランニング角度データを生成中...")
    
    fps = 30.0
    duration = 10.0
    total_frames = int(duration * fps)
    
    timestamps = []
    trunk_angles = []
    left_thigh_angles = []
    right_thigh_angles = []
    left_lower_leg_angles = []
    right_lower_leg_angles = []
    
    step_frequency = 2.6  # 156 steps/min
    
    print(f"📊 {total_frames}フレーム（{duration}秒）、ケイデンス {step_frequency * 60:.0f} steps/min")
    print("🔢 実装済み符号基準を適用:")
    print("   体幹: 前傾=負値, 後傾=正値")
    print("   大腿・下腿: 後方位置=正値, 前方位置=負値")
    
    for frame in range(total_frames):
        time = frame / fps
        
        # ランニングサイクル
        left_phase = (time * step_frequency) % 1.0
        right_phase = (left_phase + 0.5) % 1.0
        
        # === 体幹角度計算（実装済み符号基準） ===
        # 基本前傾姿勢（前傾で負値になるように）
        base_trunk_forward_lean = -6.0  # 基本前傾 -6度
        trunk_breathing = 1.0 * np.sin(time * 0.4 * 2 * np.pi)  # 呼吸
        trunk_micro_sway = 0.5 * np.sin(time * 1.2 * 2 * np.pi)  # 微細な揺れ
        trunk_noise = np.random.normal(0, 0.3)
        
        trunk_angle = base_trunk_forward_lean + trunk_breathing + trunk_micro_sway + trunk_noise
        trunk_angle = np.clip(trunk_angle, -12.0, 5.0)
        
        # === 大腿角度計算（実装済み符号基準） ===
        # 膝が後方で正値、前方で負値
        
        # 左大腿角度
        if 0.0 <= left_phase <= 0.3:  # 接地期：膝が前方
            left_thigh_base = -8.0
        elif 0.3 <= left_phase <= 0.7:  # 遊脚期：膝が後方に移動
            phase_in_swing = (left_phase - 0.3) / 0.4
            left_thigh_base = -8.0 + 25.0 * np.sin(phase_in_swing * np.pi)
        else:  # 接地準備：膝が前方に戻る
            left_thigh_base = -8.0
        
        left_thigh_noise = np.random.normal(0, 1.5)
        left_thigh_angle = left_thigh_base + left_thigh_noise
        
        # 右大腿角度
        if 0.0 <= right_phase <= 0.3:  # 接地期：膝が前方
            right_thigh_base = -8.0
        elif 0.3 <= right_phase <= 0.7:  # 遊脚期：膝が後方に移動
            phase_in_swing = (right_phase - 0.3) / 0.4
            right_thigh_base = -8.0 + 25.0 * np.sin(phase_in_swing * np.pi)
        else:  # 接地準備：膝が前方に戻る
            right_thigh_base = -8.0
        
        right_thigh_noise = np.random.normal(0, 1.5)
        right_thigh_angle = right_thigh_base + right_thigh_noise
        
        # === 下腿角度計算（実装済み符号基準） ===
        # 足首が後方で正値、前方で負値
        
        # 左下腿角度
        if 0.1 <= left_phase <= 0.6:  # 遊脚期：足首が後方（膝屈曲）
            phase_in_swing = (left_phase - 0.1) / 0.5
            left_lower_leg_base = 15.0 * np.sin(phase_in_swing * np.pi)
        else:  # 立脚期：足首が前方
            left_lower_leg_base = -5.0
        
        left_lower_leg_noise = np.random.normal(0, 2.0)
        left_lower_leg_angle = left_lower_leg_base + left_lower_leg_noise
        
        # 右下腿角度
        if 0.1 <= right_phase <= 0.6:  # 遊脚期：足首が後方（膝屈曲）
            phase_in_swing = (right_phase - 0.1) / 0.5
            right_lower_leg_base = 15.0 * np.sin(phase_in_swing * np.pi)
        else:  # 立脚期：足首が前方
            right_lower_leg_base = -5.0
        
        right_lower_leg_noise = np.random.normal(0, 2.0)
        right_lower_leg_angle = right_lower_leg_base + right_lower_leg_noise
        
        # 物理的制約を適用
        left_thigh_angle = np.clip(left_thigh_angle, -20, 30)
        right_thigh_angle = np.clip(right_thigh_angle, -20, 30)
        left_lower_leg_angle = np.clip(left_lower_leg_angle, -15, 25)
        right_lower_leg_angle = np.clip(right_lower_leg_angle, -15, 25)
        
        timestamps.append(time)
        trunk_angles.append(trunk_angle)
        left_thigh_angles.append(left_thigh_angle)
        right_thigh_angles.append(right_thigh_angle)
        left_lower_leg_angles.append(left_lower_leg_angle)
        right_lower_leg_angles.append(right_lower_leg_angle)
    
    print(f"✅ {len(timestamps)}個のデータポイント（実装済み符号基準）を生成")
    
    return {
        'timestamps': timestamps,
        'trunk_angles': trunk_angles,
        'left_thigh_angles': left_thigh_angles,
        'right_thigh_angles': right_thigh_angles,
        'left_lower_leg_angles': left_lower_leg_angles,
        'right_lower_leg_angles': right_lower_leg_angles
    }

def create_corrected_trunk_angle_chart(data: Dict, save_path: str = "corrected_trunk_angle.png"):
    """
    正しい符号基準を使用した体幹角度グラフ
    """
    print("📈 実装済み符号基準で体幹角度グラフを生成中...")
    
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
    
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    timestamps = data['timestamps']
    trunk_angles = data['trunk_angles']
    
    # メインライン
    ax.plot(timestamps, trunk_angles, 'b-', linewidth=2.5, alpha=0.8, 
            label='体幹角度 (実装済み符号基準)')
    
    # 移動平均
    if len(trunk_angles) > 10:
        window = 20
        moving_avg = np.convolve(trunk_angles, np.ones(window) / window, mode='same')
        ax.plot(timestamps, moving_avg, 'r-', linewidth=3, alpha=0.9, label='移動平均')
    
    # 基準線とガイド
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.6, label='直立 (0°)')
    ax.axhline(y=-5, color='green', linestyle='--', alpha=0.8, linewidth=2, label='理想前傾 (-5°)')
    ax.fill_between(timestamps, -8, -2, alpha=0.1, color='green', label='理想前傾範囲')
    ax.fill_between(timestamps, 0, 5, alpha=0.1, color='orange', label='後傾注意範囲')
    
    # 軸とタイトル
    ax.set_xlabel('時間 (秒)', fontsize=12, fontweight='bold')
    ax.set_ylabel('体幹角度 (度)', fontsize=12, fontweight='bold')
    ax.set_title('体幹角度推移 - 実装済み符号基準\n前傾 = 負値（理想的）, 後傾 = 正値（注意）', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # 統計情報
    mean_angle = np.mean(trunk_angles)
    std_angle = np.std(trunk_angles)
    
    stats_text = f"""実装済み符号基準:
平均: {mean_angle:.1f}°
標準偏差: ±{std_angle:.1f}°
符号規則: 前傾=負値, 後傾=正値
実装: forward_positive=False"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"📊 体幹角度グラフ保存: {save_path}")
    return save_path

def create_corrected_leg_angles_chart(data: Dict, save_path: str = "corrected_leg_angles.png"):
    """
    正しい符号基準を使用した脚部角度グラフ
    """
    print("📈 実装済み符号基準で脚部角度グラフを生成中...")
    
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'Hiragino Sans']
    
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('white')
    
    timestamps = data['timestamps']
    
    # 4つの角度をプロット
    ax.plot(timestamps, data['left_thigh_angles'], 'b-', linewidth=2.5, alpha=0.8, 
            label='左大腿角度', marker='o', markersize=2, markevery=20)
    ax.plot(timestamps, data['right_thigh_angles'], 'r-', linewidth=2.5, alpha=0.8, 
            label='右大腿角度', marker='s', markersize=2, markevery=20)
    ax.plot(timestamps, data['left_lower_leg_angles'], 'g--', linewidth=2.5, alpha=0.8, 
            label='左下腿角度', marker='^', markersize=2, markevery=20)
    ax.plot(timestamps, data['right_lower_leg_angles'], 'm--', linewidth=2.5, alpha=0.8, 
            label='右下腿角度', marker='d', markersize=2, markevery=20)
    
    # 基準線
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.6, label='基準線 (0°)')
    
    # 理想範囲（参考）
    ax.fill_between(timestamps, 5, 20, alpha=0.05, color='blue', label='大腿後方範囲（遊脚期）')
    ax.fill_between(timestamps, -15, -5, alpha=0.05, color='red', label='接地期範囲')
    
    # 軸とタイトル
    ax.set_xlabel('時間 (秒)', fontsize=12, fontweight='bold')
    ax.set_ylabel('角度 (度)', fontsize=12, fontweight='bold')
    ax.set_title('脚部角度推移 - 実装済み符号基準\n後方位置 = 正値（遊脚期）, 前方位置 = 負値（接地期）', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=2)
    
    # 統計情報
    stats_text = f"""実装済み符号基準:
左大腿: {np.mean(data['left_thigh_angles']):.1f}° (±{np.std(data['left_thigh_angles']):.1f}°)
右大腿: {np.mean(data['right_thigh_angles']):.1f}° (±{np.std(data['right_thigh_angles']):.1f}°)
左下腿: {np.mean(data['left_lower_leg_angles']):.1f}° (±{np.std(data['left_lower_leg_angles']):.1f}°)
右下腿: {np.mean(data['right_lower_leg_angles']):.1f}° (±{np.std(data['right_lower_leg_angles']):.1f}°)
符号規則: 後方=正値, 前方=負値
実装: forward_positive=True"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"📊 脚部角度グラフ保存: {save_path}")
    return save_path

def display_implementation_details():
    """
    実装の詳細を表示
    """
    print("\n🔧 実装詳細:")
    print("=" * 60)
    for angle_type, details in IMPLEMENTED_SIGN_CONVENTIONS.items():
        print(f"\n📐 {angle_type.upper()}角度:")
        print(f"   {details['description']}")
        print(f"   ✅ 正値: {details['positive']}")
        print(f"   ❌ 負値: {details['negative']}")
        print(f"   💻 実装: {details['implementation']}")

def main():
    """メイン処理"""
    print("🎯 実装済み符号基準に基づく角度グラフ生成")
    print("=" * 60)
    
    # 実装詳細の表示
    display_implementation_details()
    
    # データ生成
    print("\n📊 データ生成:")
    angle_data = generate_realistic_angle_data_with_correct_signs()
    
    # グラフ生成
    print("\n📈 グラフ生成:")
    trunk_chart = create_corrected_trunk_angle_chart(angle_data)
    leg_chart = create_corrected_leg_angles_chart(angle_data)
    
    # 結果分析
    print("\n" + "=" * 60)
    print("📊 実装済み符号基準による分析結果:")
    print(f"   解析時間: {angle_data['timestamps'][-1]:.1f}秒")
    print(f"   体幹角度平均: {np.mean(angle_data['trunk_angles']):.1f}° (前傾基調 ✅)")
    
    trunk_mean = np.mean(angle_data['trunk_angles'])
    if trunk_mean < -2:
        print("   🏃‍♂️ 体幹評価: 適切な前傾姿勢（理想的）")
    elif trunk_mean > 2:
        print("   ⚠️ 体幹評価: 後傾気味（改善推奨）")
    else:
        print("   ℹ️ 体幹評価: ほぼ直立姿勢")
    
    print(f"\n📁 生成ファイル:")
    print(f"   - {trunk_chart}")
    print(f"   - {leg_chart}")

if __name__ == "__main__":
    main()
