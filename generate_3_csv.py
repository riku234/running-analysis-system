#!/usr/bin/env python3
"""
全フレーム骨格データCSV生成スクリプト - 「3」
Video ID: de535dfb-1d3b-4c12-a9b8-5b3299bc85fb の全フレーム骨格データをCSV形式で出力します
"""

import json
import pandas as pd
import os
from datetime import datetime
import urllib.request
import urllib.error

# 動画ID
VIDEO_ID = "de535dfb-1d3b-4c12-a9b8-5b3299bc85fb"
VIDEO_PROCESSING_URL = "http://localhost:8001"

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

def get_pose_data_from_service(video_id: str):
    """video_processingサービスからpose_dataを取得"""
    try:
        url = f"{VIDEO_PROCESSING_URL}/result/{video_id}"
        print(f"🔗 APIリクエスト: {url}")
        
        with urllib.request.urlopen(url, timeout=300) as response:
            result_data = json.loads(response.read().decode('utf-8'))
            
            if result_data and result_data.get("pose_analysis") and result_data["pose_analysis"].get("pose_data"):
                return result_data["pose_analysis"]["pose_data"], result_data["pose_analysis"]["video_info"]
            else:
                print(f"❌ エラー: pose_dataが見つかりません。")
                return None, None
    except urllib.error.HTTPError as e:
        print(f"❌ HTTPエラーが発生しました: {e.code} - {e.reason}")
        return None, None
    except urllib.error.URLError as e:
        print(f"❌ URLエラーが発生しました: {e.reason}")
        return None, None
    except Exception as e:
        print(f"❌ 予期せぬエラーが発生しました: {e}")
        return None, None

def save_pose_data_to_csv(pose_data, video_info, filename="3.csv"):
    """pose_dataをCSV形式で保存"""
    if not pose_data:
        print("❌ 保存するポーズデータがありません。")
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
    df.to_csv(filename, index=False, encoding='utf-8')
    
    # 統計情報を表示
    print(f"\n✅ CSVファイル生成完了!")
    print(f"📄 ファイル名: {filename}")
    print(f"📁 ファイルサイズ: {os.path.getsize(filename):,} bytes ({os.path.getsize(filename) / (1024*1024):.2f} MB)")
    print(f"📋 総行数: {len(df):,} 行")
    print(f"📊 フレーム数: {df['frame_number'].nunique():,} フレーム")
    print(f"📍 ランドマーク数: {df['landmark'].nunique()} 種類")
    print(f"🎥 動画時間: {df['timestamp'].max():.2f} 秒")
    print(f"📏 解像度: {video_info.get('width', 0)}x{video_info.get('height', 0)} @ {video_info.get('fps', 0)}fps")
    print(f"📍 ファイルパス: {os.path.abspath(filename)}")
    
    # サンプルデータを表示
    print(f"\n📋 サンプルデータ (最初の5行):")
    print(df.head().to_string(index=False))
    
    return True

def main():
    """メイン処理"""
    print("🎬 全フレーム骨格データCSV生成開始 - 「3」")
    print("=" * 60)
    print(f"📹 Video ID: {VIDEO_ID}")
    print()
    
    # video_processingサービスからpose_dataを取得
    pose_data, video_info = get_pose_data_from_service(VIDEO_ID)
    
    if pose_data and video_info:
        # CSVファイルを生成
        success = save_pose_data_to_csv(pose_data, video_info, filename="3.csv")
        
        if success:
            print("\n🎉 処理完了! CSVファイル「3.csv」が生成されました")
        else:
            print("\n❌ 処理失敗")
    else:
        print("❌ ポーズデータを取得できませんでした。")

if __name__ == "__main__":
    main()

