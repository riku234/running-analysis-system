#!/usr/bin/env python3
"""
実際のアップロード動画から pose データを取得して体幹角度を計算
"""

import subprocess
import json
import os

def get_latest_video_pose_data():
    """
    最新のアップロード動画の pose data を取得
    """
    print("🎯 最新動画の pose データを取得中...")
    
    latest_video = "20250928_093352_2f3008fa-4b0f-48ec-85a0-df138350f741.mov"
    video_id = "2f3008fa-4b0f-48ec-85a0-df138350f741"
    
    print(f"📹 対象動画: {latest_video}")
    print(f"🆔 動画ID: {video_id}")
    
    # pose_estimation サービスを直接呼び出してみる
    try:
        print("🔍 pose_estimation サービスの直接呼び出し...")
        result = subprocess.run([
            'docker', 'exec', 'running-analysis-system-pose_estimation-1',
            'python', '-c', f"""
import sys
sys.path.append('/app')
from main import process_video
import json

try:
    result = process_video('/app/uploads/{latest_video}')
    print("POSE_DATA_START")
    print(json.dumps(result, indent=2))
    print("POSE_DATA_END")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            output = result.stdout
            if "POSE_DATA_START" in output and "POSE_DATA_END" in output:
                start_idx = output.find("POSE_DATA_START") + len("POSE_DATA_START\n")
                end_idx = output.find("POSE_DATA_END")
                json_data = output[start_idx:end_idx].strip()
                
                try:
                    pose_data = json.loads(json_data)
                    print("✅ pose データの取得に成功しました！")
                    return pose_data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON パースエラー: {e}")
                    print(f"Raw data: {json_data[:200]}...")
            else:
                print("⚠️ 期待されるマーカーが見つかりません")
                print(f"出力: {output[:500]}...")
        else:
            print(f"❌ コマンド実行エラー: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ pose_estimation サービスの呼び出しがタイムアウトしました")
    except Exception as e:
        print(f"❌ pose_estimation サービス呼び出しエラー: {e}")
    
    # video_processing サービス経由での結果取得を試行
    try:
        print("\n🔍 video_processing サービス経由での結果取得...")
        result = subprocess.run([
            'docker', 'exec', 'running-analysis-system-video_processing-1',
            'python', '-c', f"""
import json
import os

# 結果ファイルを探す
result_files = []
for root, dirs, files in os.walk('/app'):
    for file in files:
        if '{video_id}' in file and file.endswith('.json'):
            result_files.append(os.path.join(root, file))

print("Found result files:", result_files)

if result_files:
    with open(result_files[0], 'r') as f:
        data = json.load(f)
    print("RESULT_DATA_START")
    print(json.dumps(data, indent=2))
    print("RESULT_DATA_END")
else:
    print("No result files found")
"""
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "RESULT_DATA_START" in result.stdout:
            print("✅ video_processing から結果データを取得しました")
            # JSON 抽出処理
            output = result.stdout
            start_idx = output.find("RESULT_DATA_START") + len("RESULT_DATA_START\n")
            end_idx = output.find("RESULT_DATA_END")
            json_data = output[start_idx:end_idx].strip()
            
            try:
                result_data = json.loads(json_data)
                return result_data
            except json.JSONDecodeError as e:
                print(f"❌ JSON パースエラー: {e}")
        else:
            print("⚠️ video_processing からの結果取得に失敗")
            print(f"出力: {result.stdout[:300]}...")
            
    except Exception as e:
        print(f"❌ video_processing サービス呼び出しエラー: {e}")
    
    # API Gateway 経由での結果取得を試行
    try:
        print("\n🔍 API Gateway 経由での結果取得...")
        result = subprocess.run([
            'curl', '-s', f'http://localhost:8000/api/video_processing/result/{video_id}'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                api_data = json.loads(result.stdout)
                print("✅ API Gateway から結果データを取得しました")
                return api_data
            except json.JSONDecodeError:
                print("⚠️ API Gateway からの応答はJSONではありませんでした")
                print(f"応答: {result.stdout[:200]}...")
        else:
            print("❌ API Gateway からの結果取得に失敗")
            
    except Exception as e:
        print(f"❌ API Gateway 呼び出しエラー: {e}")
    
    print("❌ 全ての方法での pose データ取得に失敗しました")
    return None

def extract_and_analyze_real_trunk_angles(pose_data):
    """
    実際の pose データから体幹角度を抽出・分析
    """
    import numpy as np
    
    print("📊 実際の pose データから体幹角度を抽出中...")
    
    if not pose_data:
        print("❌ pose データが提供されていません")
        return None
    
    # データ構造を確認
    print(f"🔍 pose データ構造の確認:")
    print(f"   Keys: {list(pose_data.keys()) if isinstance(pose_data, dict) else 'Not a dict'}")
    
    # pose_data の場所を特定
    frames_data = None
    if 'pose_analysis' in pose_data and 'pose_data' in pose_data['pose_analysis']:
        frames_data = pose_data['pose_analysis']['pose_data']
        print(f"✅ pose_analysis.pose_data を発見: {len(frames_data)}フレーム")
    elif 'pose_data' in pose_data:
        frames_data = pose_data['pose_data']
        print(f"✅ pose_data を発見: {len(frames_data)}フレーム")
    elif isinstance(pose_data, list):
        frames_data = pose_data
        print(f"✅ リスト形式の pose_data: {len(frames_data)}フレーム")
    
    if not frames_data:
        print("❌ フレームデータが見つかりません")
        return None
    
    # 体幹角度計算
    timestamps = []
    trunk_angles = []
    valid_frames = 0
    
    for frame in frames_data:
        if not isinstance(frame, dict) or 'keypoints' not in frame:
            continue
            
        keypoints = frame['keypoints']
        timestamp = frame.get('timestamp', valid_frames / 30.0)  # デフォルトは30fps
        
        # MediaPipe インデックス
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_HIP = 23
        RIGHT_HIP = 24
        
        try:
            # 必要なキーポイントの確認
            required_points = [LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP]
            
            if len(keypoints) <= max(required_points):
                continue
                
            # 可視性チェック
            valid_visibility = True
            for idx in required_points:
                if (not keypoints[idx] or 
                    keypoints[idx].get('visibility', 0) < 0.5):
                    valid_visibility = False
                    break
            
            if not valid_visibility:
                continue
            
            # 体幹角度計算
            shoulder_center_x = (keypoints[LEFT_SHOULDER]['x'] + keypoints[RIGHT_SHOULDER]['x']) / 2
            shoulder_center_y = (keypoints[LEFT_SHOULDER]['y'] + keypoints[RIGHT_SHOULDER]['y']) / 2
            hip_center_x = (keypoints[LEFT_HIP]['x'] + keypoints[RIGHT_HIP]['x']) / 2
            hip_center_y = (keypoints[LEFT_HIP]['y'] + keypoints[RIGHT_HIP]['y']) / 2
            
            # 体幹ベクトル（腰→肩）
            trunk_vector = np.array([
                shoulder_center_x - hip_center_x,
                shoulder_center_y - hip_center_y
            ])
            
            # 鉛直軸との角度計算
            vertical_vector = np.array([0.0, -1.0])
            
            trunk_norm = np.linalg.norm(trunk_vector)
            if trunk_norm == 0:
                continue
                
            trunk_normalized = trunk_vector / trunk_norm
            
            cos_angle = np.dot(trunk_normalized, vertical_vector)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle_rad = np.arccos(cos_angle)
            angle_deg = np.degrees(angle_rad)
            
            # 符号の決定（前傾で負値）
            cross_product = np.cross(trunk_vector, vertical_vector)
            trunk_angle = -angle_deg if cross_product > 0 else angle_deg
            
            timestamps.append(timestamp)
            trunk_angles.append(trunk_angle)
            valid_frames += 1
            
        except Exception as e:
            print(f"⚠️ フレーム {valid_frames} 処理エラー: {e}")
            continue
    
    print(f"✅ {valid_frames}/{len(frames_data)} フレームから体幹角度を計算しました")
    
    if not trunk_angles:
        print("❌ 有効な体幹角度データがありません")
        return None
    
    # 統計分析
    mean_angle = np.mean(trunk_angles)
    std_angle = np.std(trunk_angles)
    min_angle = np.min(trunk_angles)
    max_angle = np.max(trunk_angles)
    
    print(f"\n📊 実際の動画データ分析結果:")
    print(f"   解析時間: {timestamps[-1]:.1f}秒")
    print(f"   平均体幹角度: {mean_angle:.2f}°")
    print(f"   標準偏差: {std_angle:.2f}°")
    print(f"   角度範囲: {min_angle:.1f}° 〜 {max_angle:.1f}°")
    
    return {
        'timestamps': timestamps,
        'trunk_angles': trunk_angles,
        'statistics': {
            'mean': mean_angle,
            'std': std_angle,
            'min': min_angle,
            'max': max_angle,
            'duration': timestamps[-1],
            'valid_frames': valid_frames
        }
    }

def main():
    """メイン処理"""
    print("🏃‍♂️ 実際のアップロード動画から体幹角度データを取得")
    print("=" * 60)
    
    # 1. 実際の pose データを取得
    pose_data = get_latest_video_pose_data()
    
    if pose_data:
        # 2. 体幹角度を抽出・分析
        result = extract_and_analyze_real_trunk_angles(pose_data)
        
        if result:
            print("\n🎯 実際のデータ取得成功！")
            print("次のステップ: この実データを使用してグラフを生成できます")
            
            # 結果をファイルに保存
            import json
            with open('real_trunk_angle_data.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("📁 実データを real_trunk_angle_data.json に保存しました")
        else:
            print("❌ 体幹角度の抽出に失敗しました")
    else:
        print("❌ pose データの取得に失敗しました")
        print("💡 代替案: リアルなテンプレートデータを使用します")

if __name__ == "__main__":
    main()
