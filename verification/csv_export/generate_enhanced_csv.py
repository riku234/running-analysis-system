#!/usr/bin/env python3
"""
拡張版CSV生成スクリプト（本番システム準拠）
骨格データ + 角度データ + Zスコアデータを統合したCSVを生成
"""

import json
import csv
import os
import math
from datetime import datetime

# 動画ID
VIDEO_ID = "58bc828c-49e5-457e-84f5-b1eaa8c80d8f"
JSON_FILE = "/tmp/video_result.json"

# MediaPipeランドマーク名の定義
MEDIAPIPE_LANDMARKS = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer", 
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]

# 身体部位マッピング（既存CSVと同じ）
BODY_PARTS_MAP = {
    "nose": "顔", "left_eye_inner": "顔", "left_eye": "顔", "left_eye_outer": "顔",
    "right_eye_inner": "顔", "right_eye": "顔", "right_eye_outer": "顔", 
    "left_ear": "顔", "right_ear": "顔", "mouth_left": "顔", "mouth_right": "顔",
    "left_shoulder": "上肢", "right_shoulder": "上肢", "left_elbow": "上肢", 
    "right_elbow": "上肢", "left_wrist": "上肢", "right_wrist": "上肢", 
    "left_pinky": "上肢", "right_pinky": "上肢", "left_index": "上肢", 
    "right_index": "上肢", "left_thumb": "上肢", "right_thumb": "上肢",
    "left_hip": "体幹", "right_hip": "体幹",
    "left_knee": "下肢", "right_knee": "下肢", "left_ankle": "下肢", 
    "right_ankle": "下肢", "left_heel": "下肢", "right_heel": "下肢", 
    "left_foot_index": "下肢", "right_foot_index": "下肢"
}

def load_data_from_json():
    """JSONファイルからデータを読み込む"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSONデータ読み込み完了")
        print(f"   ファイルサイズ: {os.path.getsize(JSON_FILE):,} bytes")
        
        # データ構造を確認
        print("\n📊 データ構造:")
        print(f"   pose_analysis: {'✅' if 'pose_analysis' in data else '❌'}")
        print(f"   feature_analysis: {'✅' if 'feature_analysis' in data else '❌'}")
        print(f"   z_score_analysis: {'✅' if 'z_score_analysis' in data else '❌'}")
        
        return data
    except Exception as e:
        print(f"❌ JSONファイル読み込みエラー: {e}")
        return None

def find_best_matching_frames(angle_dict, event_dict, event_angles):
    """
    各イベントタイプごとに、event_anglesと最も一致するフレームを1つだけ特定
    
    Args:
        angle_dict: フレーム番号をキーとした角度データ辞書
        event_dict: フレーム番号をキーとしたイベントタイプ辞書
        event_angles: APIから返された最良サイクルの各イベントの角度データ
    
    Returns:
        dict: {event_type: frame_number} の辞書（各イベントタイプに1つのフレーム番号）
    """
    best_frames = {}
    
    print("\n🔍 最良サイクルのフレーム特定（本番システムロジック準拠）")
    print("=" * 80)
    
    # 各イベントタイプごとに処理
    for event_type, target_angles in event_angles.items():
        print(f"\n【{event_type}】")
        print(f"   目標角度:")
        for angle_name, angle_value in target_angles.items():
            print(f"      {angle_name}: {angle_value:.2f}°")
        
        best_frame = None
        best_diff = float('inf')
        
        # 該当するイベントタイプのフレームのみを走査
        for frame_num, frame_event_type in event_dict.items():
            if frame_event_type != event_type:
                continue
            
            # このフレームの角度データを取得
            frame_angles = angle_dict.get(frame_num, {})
            trunk = frame_angles.get('trunk_angle')
            left_thigh = frame_angles.get('left_thigh_angle')
            right_thigh = frame_angles.get('right_thigh_angle')
            left_lower = frame_angles.get('left_lower_leg_angle')
            right_lower = frame_angles.get('right_lower_leg_angle')
            
            # 全ての角度が存在する場合のみ比較
            if all(v is not None for v in [trunk, left_thigh, right_thigh, left_lower, right_lower]):
                # 目標角度との差分を計算（RMSE: Root Mean Square Error）
                differences = []
                
                if '体幹角度' in target_angles:
                    differences.append((trunk - target_angles['体幹角度']) ** 2)
                if '左大腿角度' in target_angles:
                    differences.append((left_thigh - target_angles['左大腿角度']) ** 2)
                if '右大腿角度' in target_angles:
                    differences.append((right_thigh - target_angles['右大腿角度']) ** 2)
                if '左下腿角度' in target_angles:
                    differences.append((left_lower - target_angles['左下腿角度']) ** 2)
                if '右下腿角度' in target_angles:
                    differences.append((right_lower - target_angles['右下腿角度']) ** 2)
                
                # RMSE（Root Mean Square Error）を計算
                rmse = math.sqrt(sum(differences) / len(differences)) if differences else float('inf')
                
                # より良いマッチを見つけたら更新
                if rmse < best_diff:
                    best_diff = rmse
                    best_frame = frame_num
        
        if best_frame is not None:
            best_frames[event_type] = best_frame
            print(f"   ✅ 最良フレーム: {best_frame} (RMSE: {best_diff:.3f}°)")
        else:
            print(f"   ❌ 一致するフレームなし")
    
    print("\n" + "=" * 80)
    print(f"✅ 最良サイクル特定完了: {len(best_frames)} イベント")
    for event_type, frame_num in sorted(best_frames.items()):
        print(f"   {event_type}: フレーム{frame_num}")
    print("=" * 80)
    
    return best_frames

def create_enhanced_csv(data):
    """拡張版CSVを生成（本番システム準拠）"""
    
    # 1. 骨格データ取得
    pose_data = data.get('pose_analysis', {}).get('pose_data', [])
    video_info = data.get('pose_analysis', {}).get('video_info', {})
    
    # 2. 角度データ取得
    angle_data = data.get('feature_analysis', {}).get('features', {}).get('angle_data', [])
    
    # 3. Zスコア・イベントデータ取得
    z_score_analysis = data.get('z_score_analysis', {})
    z_scores = z_score_analysis.get('z_scores', {})
    events_detected = z_score_analysis.get('events_detected', [])
    event_angles = z_score_analysis.get('event_angles', {})  # 最良サイクルの角度データ
    
    print(f"\n📊 データ件数:")
    print(f"   pose_data: {len(pose_data)} フレーム")
    print(f"   angle_data: {len(angle_data)} フレーム")
    print(f"   events_detected: {len(events_detected)} イベント")
    
    # イベント情報を辞書化（フレーム番号をキーに）
    event_dict = {}
    for event in events_detected:
        frame_num = event[0]
        foot_side = event[1]
        event_type = event[2]
        event_key = f"{foot_side}_{event_type}"  # 例: "right_strike"
        event_dict[frame_num] = event_key
    
    # 角度データを辞書化（フレーム番号をキーに）
    angle_dict = {}
    for angle_frame in angle_data:
        frame_num = angle_frame.get('frame_number', 0)
        angle_dict[frame_num] = angle_frame
    
    # ★★★ 本番システムロジック: 各イベントタイプごとに最良の1フレームを特定 ★★★
    best_cycle_frames = find_best_matching_frames(angle_dict, event_dict, event_angles)
    
    # CSVデータを準備
    csv_data = []
    
    for frame_data in pose_data:
        frame_number = frame_data.get("frame_number", 0)
        timestamp = frame_data.get("timestamp", 0.0)
        confidence_score = frame_data.get("confidence_score", 0.0)
        keypoints = frame_data.get("keypoints", [])
        
        # このフレームの角度データを取得
        frame_angles = angle_dict.get(frame_number, {})
        trunk_angle = frame_angles.get('trunk_angle', None)
        left_thigh_angle = frame_angles.get('left_thigh_angle', None)
        right_thigh_angle = frame_angles.get('right_thigh_angle', None)
        left_lower_leg_angle = frame_angles.get('left_lower_leg_angle', None)
        right_lower_leg_angle = frame_angles.get('right_lower_leg_angle', None)
        
        # このフレームがイベントかどうか確認
        event_type = event_dict.get(frame_number, None)
        
        # ★★★ Z値の設定: 最良サイクルのフレームのみにZ値を設定 ★★★
        z_trunk = None
        z_left_thigh = None
        z_right_thigh = None
        z_left_lower = None
        z_right_lower = None
        
        if event_type and event_type in best_cycle_frames:
            # このフレームが最良サイクルのフレームの場合のみZ値を設定
            if best_cycle_frames[event_type] == frame_number:
                event_z_scores = z_scores.get(event_type, {})
                z_trunk = event_z_scores.get('体幹角度', None)
                z_left_thigh = event_z_scores.get('左大腿角度', None)
                z_right_thigh = event_z_scores.get('右大腿角度', None)
                z_left_lower = event_z_scores.get('左下腿角度', None)
                z_right_lower = event_z_scores.get('右下腿角度', None)
        
        # keypointsが33個のランドマークを含むかチェック
        if len(keypoints) != 33:
            continue
        
        # 各ランドマークをCSV行として追加
        for idx, keypoint in enumerate(keypoints):
            if idx < len(MEDIAPIPE_LANDMARKS):
                landmark_name = MEDIAPIPE_LANDMARKS[idx]
                
                # body_part列を取得
                body_part = BODY_PARTS_MAP.get(landmark_name, "不明")
                
                csv_data.append({
                    # 既存のヘッダー（1.csvと同じ順序）
                    "frame_number": frame_number,
                    "timestamp": round(timestamp, 4),
                    "confidence_score": round(confidence_score, 3),
                    "landmark": landmark_name,
                    "x_coordinate": round(keypoint.get("x", 0.0), 6),
                    "y_coordinate": round(keypoint.get("y", 0.0), 6),
                    "visibility": round(keypoint.get("visibility", 0.0), 3),
                    "body_part": body_part,  # ← 既存CSVに合わせて追加
                    
                    # 新規追加: 角度データ（全フレーム）
                    "trunk_angle": round(trunk_angle, 2) if trunk_angle is not None else None,
                    "left_thigh_angle": round(left_thigh_angle, 2) if left_thigh_angle is not None else None,
                    "right_thigh_angle": round(right_thigh_angle, 2) if right_thigh_angle is not None else None,
                    "left_lower_leg_angle": round(left_lower_leg_angle, 2) if left_lower_leg_angle is not None else None,
                    "right_lower_leg_angle": round(right_lower_leg_angle, 2) if right_lower_leg_angle is not None else None,
                    
                    # 新規追加: イベント情報
                    "event_type": event_type,
                    
                    # 新規追加: Zスコア（最良サイクルのイベントフレームのみ）
                    "z_score_trunk": round(z_trunk, 3) if z_trunk is not None else None,
                    "z_score_left_thigh": round(z_left_thigh, 3) if z_left_thigh is not None else None,
                    "z_score_right_thigh": round(z_right_thigh, 3) if z_right_thigh is not None else None,
                    "z_score_left_lower": round(z_left_lower, 3) if z_left_lower is not None else None,
                    "z_score_right_lower": round(z_right_lower, 3) if z_right_lower is not None else None,
                })
    
    if not csv_data:
        print("❌ CSVデータの生成に失敗しました")
        return False
    
    # カラム名を取得
    if csv_data:
        fieldnames = list(csv_data[0].keys())
    else:
        return False
    
    # 出力ディレクトリを作成
    output_dir = "verification/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # UTF-8版とShift-JIS版の両方を作成
    output_filename_utf8 = f"{output_dir}/enhanced_{VIDEO_ID[:8]}_utf8_v3.csv"
    output_filename_sjis = f"{output_dir}/enhanced_{VIDEO_ID[:8]}_sjis_v3.csv"
    
    # UTF-8版を作成
    with open(output_filename_utf8, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    # Shift-JIS版を作成
    with open(output_filename_sjis, 'w', newline='', encoding='shift_jis') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    # 統計情報を計算
    total_rows = len(csv_data)
    unique_frames = len(set(row['frame_number'] for row in csv_data))
    unique_landmarks = len(set(row['landmark'] for row in csv_data))
    event_rows = sum(1 for row in csv_data if row['event_type'] is not None)
    unique_event_frames = len(set(row['frame_number'] for row in csv_data if row['event_type'] is not None))
    z_score_rows = sum(1 for row in csv_data if row['z_score_trunk'] is not None)
    unique_z_score_frames = len(set(row['frame_number'] for row in csv_data if row['z_score_trunk'] is not None))
    
    # 統計情報を表示
    print(f"\n✅ 拡張版CSVファイル生成完了（本番システム準拠）!")
    print(f"\n📄 UTF-8版:")
    print(f"   ファイル名: {output_filename_utf8}")
    print(f"   ファイルサイズ: {os.path.getsize(output_filename_utf8):,} bytes ({os.path.getsize(output_filename_utf8) / (1024*1024):.2f} MB)")
    print(f"   パス: {os.path.abspath(output_filename_utf8)}")
    print(f"\n📄 Shift-JIS版:")
    print(f"   ファイル名: {output_filename_sjis}")
    print(f"   ファイルサイズ: {os.path.getsize(output_filename_sjis):,} bytes ({os.path.getsize(output_filename_sjis) / (1024*1024):.2f} MB)")
    print(f"   パス: {os.path.abspath(output_filename_sjis)}")
    print(f"\n📊 データ統計:")
    print(f"   総行数: {total_rows:,} 行")
    print(f"   フレーム数: {unique_frames:,} フレーム")
    print(f"   ランドマーク数: {unique_landmarks} 種類")
    print(f"   全イベント: {event_rows:,} 行（{unique_event_frames} フレーム）")
    print(f"   🌟 最良サイクル: {z_score_rows:,} 行（{unique_z_score_frames} フレーム）← Z値あり")
    print(f"   期待値: 132 行（4 フレーム × 33 ランドマーク）")
    print(f"   解像度: {video_info.get('width', 0)}x{video_info.get('height', 0)} @ {video_info.get('fps', 0)}fps")
    
    # 本番システムとの整合性チェック
    print(f"\n🔍 本番システムとの整合性チェック:")
    if unique_z_score_frames == 4:
        print(f"   ✅ Z値フレーム数: {unique_z_score_frames} = 4 (正しい！)")
    else:
        print(f"   ⚠️  Z値フレーム数: {unique_z_score_frames} ≠ 4 (要確認)")
    
    # カラム情報を表示
    print(f"\n📋 CSVカラム（全{len(fieldnames)}列）:")
    for i, col in enumerate(fieldnames, 1):
        print(f"   {i:2d}. {col}")
    
    # Z値ありフレームの詳細を表示
    z_score_frames = set(row['frame_number'] for row in csv_data if row['z_score_trunk'] is not None)
    if z_score_frames:
        print(f"\n🎯 Z値ありフレーム詳細:")
        for frame_num in sorted(z_score_frames):
            sample_row = next(row for row in csv_data if row['frame_number'] == frame_num and row['z_score_trunk'] is not None)
            print(f"   フレーム{frame_num}: {sample_row['event_type']} | trunk={sample_row['trunk_angle']}° | Z={sample_row['z_score_trunk']}")
    
    return True

def main():
    """メイン処理"""
    print("🎬 拡張版CSV生成開始（本番システムロジック準拠）")
    print("=" * 80)
    print(f"📹 Video ID: {VIDEO_ID}")
    print(f"📄 JSONファイル: {JSON_FILE}")
    print()
    
    # JSONデータを読み込み
    data = load_data_from_json()
    
    if data:
        # 拡張版CSVを生成
        success = create_enhanced_csv(data)
        
        if success:
            print("\n🎉 処理完了!")
        else:
            print("\n❌ 処理失敗")
    else:
        print("❌ データを読み込めませんでした。")

if __name__ == "__main__":
    main()
