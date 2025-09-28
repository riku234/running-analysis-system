#!/usr/bin/env python3
"""
体幹角度推移グラフ生成スクリプト
最新のアップロード動画から体幹角度の時系列データを抽出し、グラフを生成します。
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math

@dataclass
class KeyPoint:
    x: float
    y: float
    z: float
    visibility: float

@dataclass
class PoseFrame:
    frame_number: int
    timestamp: float
    keypoints: List[KeyPoint]
    landmarks_detected: bool
    confidence_score: float

# MediaPipeランドマークインデックス
LANDMARK_INDICES = {
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_hip': 23,
    'right_hip': 24,
}

def calculate_absolute_angle_with_vertical(vector: np.ndarray, forward_positive: bool = True) -> Optional[float]:
    """
    ベクトルと鉛直軸（垂直上向き）の角度を計算
    
    Args:
        vector: 2D ベクトル [x, y]
        forward_positive: True なら前傾で正値、False なら前傾で負値
    
    Returns:
        角度（度）。前傾時の符号は forward_positive に依存
    """
    try:
        # 鉛直軸（上向き）ベクトル
        vertical = np.array([0.0, -1.0])  # Y軸は下向きが正なので、上向きは負
        
        # ベクトルを正規化
        vector_norm = np.linalg.norm(vector)
        if vector_norm == 0:
            return None
            
        normalized_vector = vector / vector_norm
        
        # 内積でコサイン値を計算
        cos_angle = np.dot(normalized_vector, vertical)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # 角度を計算（ラジアンから度へ）
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        # 符号の決定（外積のZ成分で左右を判定）
        cross_z = vector[0] * vertical[1] - vector[1] * vertical[0]
        
        if forward_positive:
            # 前傾（右向き）で正値
            return angle_deg if cross_z > 0 else -angle_deg
        else:
            # 前傾（右向き）で負値
            return -angle_deg if cross_z > 0 else angle_deg
            
    except Exception:
        return None

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算（腰中心→肩中心のベクトルと鉛直軸の角度）
    
    Args:
        keypoints: キーポイントリスト
        
    Returns:
        体幹角度（度）。前傾で負値、後傾で正値
    """
    try:
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        
        # 可視性チェック
        if (left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5 or
            left_hip.visibility < 0.5 or right_hip.visibility < 0.5):
            return None
        
        # 肩と腰の中心点を計算
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        
        # 体幹ベクトル（腰→肩）
        trunk_vector = np.array([
            shoulder_center_x - hip_center_x,
            shoulder_center_y - hip_center_y
        ])
        
        # 前傾で負値、後傾で正値の符号規則
        return calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=False)
        
    except Exception:
        return None

def load_pose_data_from_localStorage() -> Optional[List[PoseFrame]]:
    """
    LocalStorageのシミュレーション：最新の解析結果を読み込み
    実際の実装では、Zustandストアやローカルストレージからデータを取得
    """
    # 代替：ダミーデータを生成
    print("📊 ダミーのランニングデータを生成中...")
    
    frames = []
    fps = 30.0
    total_frames = 150  # 5秒間のデータ
    
    for frame in range(total_frames):
        time = frame / fps
        cycle_phase = (time * 3.0 * 2) % 2.0  # 3歩/秒のランニング
        
        # 体幹の動的な変化をシミュレート
        trunk_forward_lean = 5.0 + 3.0 * math.sin(cycle_phase * math.pi)  # 5-8度の前傾
        noise = (np.random.random() - 0.5) * 2.0  # ±1度のノイズ
        
        # 基本的な人体キーポイント（体幹角度計算に必要な部分のみ）
        keypoints = [None] * 33  # MediaPipeの33ポイント
        
        # 肩のキーポイント（インデックス 11, 12）
        keypoints[11] = KeyPoint(x=0.45, y=0.2, z=0.0, visibility=0.9)  # 左肩
        keypoints[12] = KeyPoint(x=0.55, y=0.2, z=0.0, visibility=0.9)  # 右肩
        
        # 腰のキーポイント（インデックス 23, 24）
        # 体幹角度を反映した位置計算
        lean_offset = trunk_forward_lean * 0.001  # 角度に応じたオフセット
        keypoints[23] = KeyPoint(x=0.45 + lean_offset, y=0.5, z=0.0, visibility=0.9)  # 左腰
        keypoints[24] = KeyPoint(x=0.55 + lean_offset, y=0.5, z=0.0, visibility=0.9)  # 右腰
        
        # フレームデータを作成
        frame_data = PoseFrame(
            frame_number=frame,
            timestamp=time,
            keypoints=keypoints,
            landmarks_detected=True,
            confidence_score=0.8 + 0.1 * np.random.random()
        )
        
        frames.append(frame_data)
    
    return frames

def extract_trunk_angles(pose_frames: List[PoseFrame]) -> Tuple[List[float], List[float]]:
    """
    ポーズフレームから体幹角度の時系列データを抽出
    
    Args:
        pose_frames: ポーズフレームのリスト
        
    Returns:
        (時刻リスト, 体幹角度リスト)
    """
    timestamps = []
    trunk_angles = []
    
    for frame in pose_frames:
        if frame.landmarks_detected and frame.keypoints:
            trunk_angle = calculate_trunk_angle(frame.keypoints)
            
            if trunk_angle is not None:
                timestamps.append(frame.timestamp)
                trunk_angles.append(trunk_angle)
    
    return timestamps, trunk_angles

def create_trunk_angle_chart(timestamps: List[float], trunk_angles: List[float], 
                           save_path: str = "trunk_angle_progression.png") -> str:
    """
    体幹角度推移のグラフを生成
    
    Args:
        timestamps: 時刻データ
        trunk_angles: 体幹角度データ
        save_path: 保存先パス
        
    Returns:
        生成されたグラフファイルのパス
    """
    # 日本語フォントの設定（利用可能な場合）
    try:
        # macOS/Linuxで一般的な日本語フォント
        japanese_fonts = [
            'Hiragino Sans',
            'Hiragino Kaku Gothic Pro', 
            'Yu Gothic',
            'Meiryo',
            'Takao Gothic',
            'DejaVu Sans'
        ]
        
        font_found = False
        for font_name in japanese_fonts:
            try:
                plt.rcParams['font.family'] = font_name
                font_found = True
                break
            except:
                continue
                
        if not font_found:
            print("⚠️ 日本語フォントが見つかりません。英語で表示します。")
            
    except Exception as e:
        print(f"⚠️ フォント設定エラー: {e}")
    
    # グラフの作成
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 体幹角度をプロット
    ax.plot(timestamps, trunk_angles, 'b-', linewidth=2, label='体幹角度 (Trunk Angle)', alpha=0.8)
    
    # 移動平均線を追加（ノイズ除去）
    if len(trunk_angles) > 10:
        window_size = min(10, len(trunk_angles) // 5)
        moving_avg = np.convolve(trunk_angles, np.ones(window_size) / window_size, mode='same')
        ax.plot(timestamps, moving_avg, 'r--', linewidth=2, label=f'移動平均 ({window_size}点)', alpha=0.7)
    
    # 基準線を追加
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='直立 (0°)')
    ax.axhline(y=-5, color='orange', linestyle=':', alpha=0.5, label='理想的前傾 (-5°)')
    
    # グラフの装飾
    ax.set_xlabel('時間 (秒)', fontsize=12)
    ax.set_ylabel('体幹角度 (度)', fontsize=12)
    ax.set_title('ランニング時の体幹角度推移\n(負値=前傾, 正値=後傾)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Y軸の範囲を適切に設定
    if trunk_angles:
        angle_range = max(trunk_angles) - min(trunk_angles)
        margin = angle_range * 0.1
        ax.set_ylim(min(trunk_angles) - margin, max(trunk_angles) + margin)
    
    # 統計情報をテキストボックスで表示
    if trunk_angles:
        stats_text = f"""統計情報:
平均: {np.mean(trunk_angles):.1f}°
標準偏差: {np.std(trunk_angles):.1f}°
最小: {np.min(trunk_angles):.1f}°
最大: {np.max(trunk_angles):.1f}°
サンプル数: {len(trunk_angles)}"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # グラフを保存
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return save_path

def main():
    """メイン処理"""
    print("🏃‍♂️ 体幹角度推移グラフ生成開始")
    
    # 1. ポーズデータの読み込み
    pose_frames = load_pose_data_from_localStorage()
    if not pose_frames:
        print("❌ ポーズデータの読み込みに失敗しました")
        return
    
    print(f"✅ {len(pose_frames)} フレームのデータを読み込みました")
    
    # 2. 体幹角度の抽出
    timestamps, trunk_angles = extract_trunk_angles(pose_frames)
    if not trunk_angles:
        print("❌ 体幹角度の計算に失敗しました")
        return
    
    print(f"✅ {len(trunk_angles)} 個の有効な体幹角度データを抽出しました")
    print(f"📊 体幹角度の範囲: {min(trunk_angles):.1f}° 〜 {max(trunk_angles):.1f}°")
    print(f"📊 平均体幹角度: {np.mean(trunk_angles):.1f}° (標準偏差: {np.std(trunk_angles):.1f}°)")
    
    # 3. グラフの生成
    chart_path = create_trunk_angle_chart(timestamps, trunk_angles)
    print(f"📈 体幹角度推移グラフを生成しました: {chart_path}")
    
    # 4. 詳細分析
    print("\n📋 詳細分析:")
    if np.mean(trunk_angles) < -2:
        print("✅ 適度な前傾姿勢を維持しています")
    elif np.mean(trunk_angles) > 2:
        print("⚠️ 後傾気味です。前傾を意識してみてください")
    else:
        print("ℹ️ ほぼ直立姿勢です")
    
    if np.std(trunk_angles) > 3:
        print("⚠️ 体幹角度の変動が大きいです。安定した姿勢を心がけてください")
    else:
        print("✅ 安定した体幹姿勢を維持しています")

if __name__ == "__main__":
    main()
