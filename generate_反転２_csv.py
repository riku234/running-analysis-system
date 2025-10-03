#!/usr/bin/env python3
"""
全フレーム骨格データCSV生成スクリプト - 「反転２」
現在解析された動画の全フレーム骨格データをCSV形式で出力します
"""

import json
import pandas as pd
import os
from datetime import datetime

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

# 身体部位マッピング
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

def load_analysis_result(filename="current_analysis_result.json"):
    """解析結果JSONファイルを読み込む"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ エラー: {filename} が見つかりません")
        return None
    except json.JSONDecodeError:
        print(f"❌ エラー: {filename} のJSON解析に失敗しました")
        return None

def extract_pose_data_to_csv(analysis_result, output_filename="反転２.csv"):
    """解析結果から骨格データを抽出してCSV形式で保存"""
    
    if not analysis_result:
        print("❌ 解析結果データが無効です")
        return False
    
    # pose_analysisからpose_dataを取得
    pose_analysis = analysis_result.get("pose_analysis", {})
    pose_data = pose_analysis.get("pose_data", [])
    video_info = pose_analysis.get("video_info", {})
    
    if not pose_data:
        print("❌ pose_dataが見つかりません")
        return False
    
    print(f"📊 処理開始:")
    print(f"   総フレーム数: {len(pose_data)}")
    print(f"   動画情報: {video_info.get('width', 'N/A')}x{video_info.get('height', 'N/A')} @ {video_info.get('fps', 'N/A')}fps")
    
    # CSVデータを準備
    csv_data = []
    
    for frame_data in pose_data:
        frame_number = frame_data.get("frame_number", 0)
        timestamp = frame_data.get("timestamp", 0.0)
        confidence_score = frame_data.get("confidence_score", 0.0)
        keypoints = frame_data.get("keypoints", [])
        
        # keypointsが33個のランドマークを含むかチェック
        if len(keypoints) != 33:
            print(f"⚠️  フレーム{frame_number}: キーポイント数が異常 ({len(keypoints)}/33)")
            continue
        
        # 各ランドマークをCSV行として追加
        for idx, keypoint in enumerate(keypoints):
            if idx < len(MEDIAPIPE_LANDMARKS):
                landmark_name = MEDIAPIPE_LANDMARKS[idx]
                body_part = BODY_PARTS_MAP.get(landmark_name, "不明")
                
                csv_data.append({
                    "frame_number": frame_number,
                    "timestamp": round(timestamp, 4),
                    "confidence_score": round(confidence_score, 3),
                    "landmark": landmark_name,
                    "x_coordinate": round(keypoint.get("x", 0.0), 6),
                    "y_coordinate": round(keypoint.get("y", 0.0), 6),
                    "visibility": round(keypoint.get("visibility", 0.0), 3),
                    "body_part": body_part
                })
    
    if not csv_data:
        print("❌ CSVデータの生成に失敗しました")
        return False
    
    # DataFrameを作成してCSVに保存
    df = pd.DataFrame(csv_data)
    df.to_csv(output_filename, index=False, encoding='utf-8')
    
    # 統計情報を表示
    print(f"✅ CSVファイル生成完了!")
    print(f"📄 ファイル名: {output_filename}")
    print(f"📁 ファイルサイズ: {os.path.getsize(output_filename):,} bytes ({os.path.getsize(output_filename) / (1024*1024):.2f} MB)")
    print(f"📋 総行数: {len(df):,} 行")
    print(f"📊 フレーム数: {df['frame_number'].nunique():,} フレーム")
    print(f"📍 ランドマーク数: {df['landmark'].nunique()} 種類")
    print(f"🎥 動画時間: {df['timestamp'].max():.2f} 秒")
    print(f"📍 ファイルパス: {os.path.abspath(output_filename)}")
    
    # サンプルデータを表示
    print(f"\n📋 サンプルデータ (最初の5行):")
    print(df.head().to_string(index=False))
    
    return True

def main():
    """メイン処理"""
    print("🎬 全フレーム骨格データCSV生成開始 - 「反転２」")
    print("=" * 60)
    
    # 解析結果を読み込み
    analysis_result = load_analysis_result()
    if not analysis_result:
        return
    
    # CSVファイルを生成
    success = extract_pose_data_to_csv(analysis_result, "反転２.csv")
    
    if success:
        print("\n🎉 処理完了! CSVファイル「反転２.csv」が生成されました")
    else:
        print("\n❌ 処理失敗")

if __name__ == "__main__":
    main()
