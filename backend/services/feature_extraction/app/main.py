from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np

app = FastAPI(
    title="Feature Extraction Service",
    description="骨格データから絶対角度・重心上下動・ピッチを計算するサービス（自動身長推定・サイクル検出機能付き）",
    version="3.3.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエスト・レスポンスのデータモデル
class KeyPoint(BaseModel):
    x: float
    y: float
    z: float
    visibility: float

class PoseFrame(BaseModel):
    frame_number: int
    timestamp: float
    keypoints: List[KeyPoint]
    landmarks_detected: bool
    confidence_score: float

class PoseAnalysisRequest(BaseModel):
    pose_data: List[PoseFrame]
    video_info: Dict[str, Any]

class FeatureExtractionResponse(BaseModel):
    status: str
    message: str
    features: Dict[str, Any]
    analysis_details: Dict[str, Any]

# MediaPipeランドマークのインデックス定義
LANDMARK_INDICES = {
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
    'left_foot_index': 31,
    'right_foot_index': 32
}

def calculate_absolute_angle_with_vertical(vector: np.ndarray, forward_positive: bool = True) -> Optional[float]:
    """
    ベクトルと鉛直軸がなす角度を計算する
    
    Args:
        vector: 対象ベクトル [x, y]
        forward_positive: Trueの場合、前方への傾きを正とする
                          Falseの場合、後方への傾きを正とする
    
    Returns:
        角度（度数法、-180～+180）または None
    """
    try:
        # ベクトルの長さをチェック
        length = np.linalg.norm(vector)
        if length == 0:
            return None
        
        # 鉛直軸（下向き）: [0, 1] （画像座標系では下がy正方向）
        vertical_vector = np.array([0, 1])
        
        # ベクトルを正規化
        normalized_vector = vector / length
        
        # 内積を使って角度を計算
        cos_angle = np.dot(normalized_vector, vertical_vector)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # ラジアンで角度を計算
        angle_rad = np.arccos(cos_angle)
        
        # x成分の符号で左右を判定
        if vector[0] < 0:  # 左方向（後方）
            angle_rad = -angle_rad
        
        # 度数法に変換
        angle_deg = np.degrees(angle_rad)
        
        # forward_positiveがFalseの場合は符号を反転
        if not forward_positive:
            angle_deg = -angle_deg
        
        return angle_deg
        
    except Exception:
        return None

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算する
    定義: 体幹ベクトル（股関節中点→肩中点）と鉛直軸がなす角度
    正: 前傾、負: 後傾
    """
    try:
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        
        # すべてのキーポイントが有効か確認
        if any(kp.visibility < 0.5 for kp in [left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        # 肩の中心点と股関節の中心点を計算
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        
        # 体幹ベクトル（股関節中点→肩中点）
        trunk_vector = np.array([shoulder_center_x - hip_center_x, shoulder_center_y - hip_center_y])
        
        # 絶対角度を計算（前傾を正とする）
        return calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=True)
        
    except Exception:
        return None

def calculate_thigh_angle(hip: KeyPoint, knee: KeyPoint, side: str) -> Optional[float]:
    """
    大腿角度を計算する
    定義: 大腿ベクトル（股関節→膝）と鉛直軸がなす角度
    正: 膝が股関節より後方、負: 膝が股関節より前方
    """
    try:
        # キーポイントの有効性を確認
        if hip.visibility < 0.5 or knee.visibility < 0.5:
            return None
        
        # 大腿ベクトル（股関節→膝）
        thigh_vector = np.array([knee.x - hip.x, knee.y - hip.y])
        
        # 絶対角度を計算（後方を正とする）
        return calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        
    except Exception:
        return None

def calculate_lower_leg_angle(knee: KeyPoint, ankle: KeyPoint, side: str) -> Optional[float]:
    """
    下腿角度を計算する
    定義: 下腿ベクトル（膝→足首）と鉛直軸がなす角度
    正: 足首が膝より後方、負: 足首が膝より前方
    """
    try:
        # キーポイントの有効性を確認
        if knee.visibility < 0.5 or ankle.visibility < 0.5:
            return None
        
        # 下腿ベクトル（膝→足首）
        lower_leg_vector = np.array([ankle.x - knee.x, ankle.y - knee.y])
        
        # 絶対角度を計算（後方を正とする）
        return calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=False)
        
    except Exception:
        return None

# =============================================================================
# 新機能：重心上下動とピッチの計算
# =============================================================================

def calculate_skeletal_height(frame_keypoints: List[KeyPoint]) -> Optional[float]:
    """
    1フレームの骨格データから「骨格上の全長」を計算する
    
    Args:
        frame_keypoints: 1フレーム分のキーポイントデータ
    
    Returns:
        骨格上の全長（float型）または None
    """
    try:
        if len(frame_keypoints) < 33:
            return None
        
        # 必要なキーポイントを取得
        left_ankle = frame_keypoints[LANDMARK_INDICES['left_ankle']]
        right_ankle = frame_keypoints[LANDMARK_INDICES['right_ankle']]
        left_knee = frame_keypoints[LANDMARK_INDICES['left_knee']]
        right_knee = frame_keypoints[LANDMARK_INDICES['right_knee']]
        left_hip = frame_keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = frame_keypoints[LANDMARK_INDICES['right_hip']]
        left_shoulder = frame_keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = frame_keypoints[LANDMARK_INDICES['right_shoulder']]
        
        # 鼻（頭部の代表点）
        nose = frame_keypoints[0]  # MediaPipeの鼻のインデックス
        
        # 可視性チェック（0.5以上で有効とする）
        required_points = [left_ankle, right_ankle, left_knee, right_knee, 
                          left_hip, right_hip, left_shoulder, right_shoulder, nose]
        
        for point in required_points:
            if point.visibility < 0.5:
                return None
        
        # 各セグメントの長さを計算
        
        # 1. 下腿長: 足首から膝までの距離（左右の平均）
        left_lower_leg = math.sqrt((left_knee.x - left_ankle.x)**2 + (left_knee.y - left_ankle.y)**2)
        right_lower_leg = math.sqrt((right_knee.x - right_ankle.x)**2 + (right_knee.y - right_ankle.y)**2)
        avg_lower_leg_length = (left_lower_leg + right_lower_leg) / 2
        
        # 2. 大腿長: 膝から股関節までの距離（左右の平均）
        left_thigh = math.sqrt((left_hip.x - left_knee.x)**2 + (left_hip.y - left_knee.y)**2)
        right_thigh = math.sqrt((right_hip.x - right_knee.x)**2 + (right_hip.y - right_knee.y)**2)
        avg_thigh_length = (left_thigh + right_thigh) / 2
        
        # 3. 体幹長: 股関節の中点から肩の中点までの距離
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        trunk_length = math.sqrt((shoulder_center_x - hip_center_x)**2 + (shoulder_center_y - hip_center_y)**2)
        
        # 4. 頭部長: 肩の中点から鼻までの距離
        head_length = math.sqrt((nose.x - shoulder_center_x)**2 + (nose.y - shoulder_center_y)**2)
        
        # 骨格上の全長を計算
        total_skeletal_height = avg_lower_leg_length + avg_thigh_length + trunk_length + head_length
        
        return total_skeletal_height
        
    except Exception as e:
        print(f"骨格身長計算エラー: {str(e)}")
        return None

def calculate_vertical_oscillation(time_series_keypoints: List[List[KeyPoint]]) -> Optional[float]:
    """
    重心上下動を計算する（骨格データから自動的に基準身長を算出）
    
    Args:
        time_series_keypoints: 1サイクル分の連続したフレームのキーポイントデータ
    
    Returns:
        計算上の平均身長を基準とした重心上下動の比率（float型）または None
    """
    try:
        if not time_series_keypoints:
            return None
        
        center_of_mass_y_positions = []
        skeletal_heights = []
        
        # 各フレームで重心のY座標と骨格身長を計算
        for frame_keypoints in time_series_keypoints:
            if len(frame_keypoints) < 33:  # MediaPipeの最小ランドマーク数
                continue
                
            left_hip = frame_keypoints[LANDMARK_INDICES['left_hip']]
            right_hip = frame_keypoints[LANDMARK_INDICES['right_hip']]
            
            # 股関節の可視性チェック
            if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
                continue
            
            # 左右股関節の中点を重心として定義
            center_of_mass_y = (left_hip.y + right_hip.y) / 2
            center_of_mass_y_positions.append(center_of_mass_y)
            
            # このフレームの骨格身長を計算
            skeletal_height = calculate_skeletal_height(frame_keypoints)
            if skeletal_height is not None:
                skeletal_heights.append(skeletal_height)
        
        # 有効なデータが不足している場合
        if len(center_of_mass_y_positions) < 3 or len(skeletal_heights) < 3:
            return None
        
        # 「計算上の平均身長」を算出
        avg_skeletal_height = np.mean(skeletal_heights)
        
        # 重心のY座標の最大値と最小値の差を計算（分子）
        max_y = max(center_of_mass_y_positions)
        min_y = min(center_of_mass_y_positions)
        vertical_displacement = max_y - min_y
        
        # 重心上下動の比率を計算（分子 / 分母）
        vertical_oscillation_ratio = vertical_displacement / avg_skeletal_height if avg_skeletal_height > 0 else None
        
        print(f"📏 骨格身長計算詳細:")
        print(f"   - 有効フレーム数: {len(skeletal_heights)}")
        print(f"   - 計算上の平均身長: {avg_skeletal_height:.6f} (正規化座標)")
        print(f"   - 重心上下動: {vertical_displacement:.6f} (正規化座標)")
        print(f"   - 上下動比率: {vertical_oscillation_ratio:.6f}")
        
        return vertical_oscillation_ratio
        
    except Exception as e:
        print(f"重心上下動計算エラー: {str(e)}")
        return None

def calculate_pitch(num_frames_in_cycle: int, video_fps: float) -> Optional[float]:
    """
    ピッチ（ケイデンス）を計算する
    
    Args:
        num_frames_in_cycle: 1サイクルにかかったフレーム数
        video_fps: 動画のフレームレート（例: 30）
    
    Returns:
        ピッチ（ケイデンス）をSPM単位で表した数値（float型）または None
    """
    try:
        if num_frames_in_cycle <= 0 or video_fps <= 0:
            return None
        
        # 1サイクルの所要時間を秒単位で計算
        cycle_duration_seconds = num_frames_in_cycle / video_fps
        
        # ランニングの1サイクル = 2歩（右足接地 + 左足接地）
        steps_per_cycle = 2
        
        # 1分間あたりの歩数（SPM: Steps Per Minute）を計算
        # 計算式: (steps_per_cycle / cycle_duration_seconds) * 60
        steps_per_minute = (steps_per_cycle / cycle_duration_seconds) * 60
        
        return steps_per_minute
        
    except Exception as e:
        print(f"ピッチ計算エラー: {str(e)}")
        return None

def detect_running_cycles(pose_data: List[PoseFrame]) -> int:
    """
    重心の上下動からランニングサイクル数を検出する
    
    Args:
        pose_data: 骨格推定データ
    
    Returns:
        検出されたランニングサイクル数
    """
    try:
        # 有効なフレームのみを抽出
        valid_frames = [frame for frame in pose_data if frame.landmarks_detected and len(frame.keypoints) >= 33]
        
        if len(valid_frames) < 10:
            return 1  # 最小限のデータの場合は1サイクルとする
        
        # 重心のY座標を抽出
        center_of_mass_y = []
        for frame in valid_frames:
            left_hip = frame.keypoints[LANDMARK_INDICES['left_hip']]
            right_hip = frame.keypoints[LANDMARK_INDICES['right_hip']]
            
            if left_hip.visibility > 0.5 and right_hip.visibility > 0.5:
                y_coord = (left_hip.y + right_hip.y) / 2
                center_of_mass_y.append(y_coord)
        
        if len(center_of_mass_y) < 5:
            return 1
        
        # 重心の上下動のピークを検出してサイクル数を推定
        # 簡易的な実装：平均値以上の点の数を数え、サイクル数を推定
        y_mean = np.mean(center_of_mass_y)
        y_std = np.std(center_of_mass_y)
        
        # 閾値を設定（平均値 + 標準偏差の半分）
        threshold = y_mean + y_std * 0.3
        
        # 閾値を超える点を検出
        above_threshold = [y > threshold for y in center_of_mass_y]
        
        # 連続する True の塊を数える（ピーク検出）
        peaks = 0
        in_peak = False
        
        for is_above in above_threshold:
            if is_above and not in_peak:
                peaks += 1
                in_peak = True
            elif not is_above:
                in_peak = False
        
        # ピーク数からサイクル数を推定
        # ランニングでは1サイクルに約1-2回のピークが発生する
        estimated_cycles = max(1, peaks // 2)  # 保守的に見積もり
        
        print(f"🔍 サイクル検出詳細:")
        print(f"   - 有効フレーム数: {len(center_of_mass_y)}")
        print(f"   - 検出されたピーク数: {peaks}")
        print(f"   - 推定サイクル数: {estimated_cycles}")
        
        return estimated_cycles
        
    except Exception as e:
        print(f"サイクル検出エラー: {str(e)}")
        return 1

def analyze_running_cycle(pose_data: List[PoseFrame], video_fps: float) -> Dict[str, Optional[float]]:
    """
    ランニングサイクルの分析（重心上下動とピッチを含む）
    
    Args:
        pose_data: 骨格推定データ
        video_fps: 動画フレームレート
    
    Returns:
        分析結果（重心上下動、ピッチ）
    """
    try:
        # 有効なフレームのみを抽出
        valid_frames = [frame for frame in pose_data if frame.landmarks_detected and len(frame.keypoints) >= 33]
        
        if len(valid_frames) < 10:  # 最小フレーム数チェック
            return {"vertical_oscillation": None, "pitch": None}
        
        # 全フレームのキーポイントデータを抽出
        time_series_keypoints = [frame.keypoints for frame in valid_frames]
        
        # ランニングサイクル数を検出
        detected_cycles = detect_running_cycles(pose_data)
        
        # 1サイクルあたりの平均フレーム数を計算
        avg_frames_per_cycle = len(valid_frames) / detected_cycles
        
        print(f"📊 サイクル分析結果:")
        print(f"   - 全フレーム数: {len(valid_frames)}")
        print(f"   - 検出サイクル数: {detected_cycles}")
        print(f"   - 1サイクル平均フレーム数: {avg_frames_per_cycle:.1f}")
        
        # 重心上下動を計算（骨格データから自動的に基準身長を算出）
        vertical_oscillation = calculate_vertical_oscillation(time_series_keypoints)
        
        # ピッチを計算（1サイクル平均を使用）
        pitch = calculate_pitch(avg_frames_per_cycle, video_fps)
        
        return {
            "vertical_oscillation": vertical_oscillation,
            "pitch": pitch,
            "cycle_frames": int(avg_frames_per_cycle),
            "valid_frames": len(valid_frames),
            "detected_cycles": detected_cycles,
            "total_video_duration": len(valid_frames) / video_fps
        }
        
    except Exception as e:
        print(f"ランニングサイクル分析エラー: {str(e)}")
        return {"vertical_oscillation": None, "pitch": None}

def extract_absolute_angles_from_frame(keypoints: List[KeyPoint]) -> Dict[str, Optional[float]]:
    """
    1フレームから新仕様の絶対角度を抽出する
    """
    angles = {}
    
    try:
        # ① 体幹角度
        angles['trunk_angle'] = calculate_trunk_angle(keypoints)
        
        # ② 大腿角度（左右）
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        angles['left_thigh_angle'] = calculate_thigh_angle(left_hip, left_knee, 'left')
        
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        angles['right_thigh_angle'] = calculate_thigh_angle(right_hip, right_knee, 'right')
        
        # ③ 下腿角度（左右）
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        angles['left_lower_leg_angle'] = calculate_lower_leg_angle(left_knee, left_ankle, 'left')
        
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        angles['right_lower_leg_angle'] = calculate_lower_leg_angle(right_knee, right_ankle, 'right')
        
    except (IndexError, KeyError):
        # キーポイントが不足している場合はすべてNoneを返す
        for key in ['trunk_angle', 'left_thigh_angle', 'right_thigh_angle', 
                   'left_lower_leg_angle', 'right_lower_leg_angle']:
            angles[key] = None
    
    return angles

def calculate_angle_statistics(angle_values: List[float]) -> Dict[str, float]:
    """
    角度の統計値（平均、最小、最大）を計算する
    """
    if not angle_values:
        return {"avg": 0.0, "min": 0.0, "max": 0.0}
    
    return {
        "avg": round(np.mean(angle_values), 1),
        "min": round(np.min(angle_values), 1),
        "max": round(np.max(angle_values), 1)
    }

@app.post("/extract", response_model=FeatureExtractionResponse)
async def extract_features(request: PoseAnalysisRequest):
    """
    骨格データから絶対角度（体幹・大腿・下腿）を抽出する
    """
    try:
        print("🔄 特徴量抽出サービス開始")
        print(f"📊 処理フレーム数: {len(request.pose_data)}")
        
        # 各フレームから角度を抽出
        all_angles = []
        valid_frames = 0
        
        for frame in request.pose_data:
            if frame.landmarks_detected and len(frame.keypoints) >= 33:
                angles = extract_absolute_angles_from_frame(frame.keypoints)
                
                # フレーム情報を追加
                frame_angles = {
                    'frame_number': frame.frame_number,
                    'timestamp': frame.timestamp,
                    'confidence_score': frame.confidence_score,
                    **angles
                }
                all_angles.append(frame_angles)
                valid_frames += 1
        
        print(f"✅ 有効フレーム数: {valid_frames}/{len(request.pose_data)}")
        
        # 統計情報を計算
        angle_stats = {}
        angle_keys = ['trunk_angle', 'left_thigh_angle', 'right_thigh_angle', 
                     'left_lower_leg_angle', 'right_lower_leg_angle']
        
        for angle_key in angle_keys:
            valid_values = [frame[angle_key] for frame in all_angles 
                           if frame[angle_key] is not None]
            angle_stats[angle_key] = calculate_angle_statistics(valid_values)
        
        # 新機能: ランニングサイクル分析（重心上下動とピッチ）
        print("🔄 ランニングサイクル分析を実行中...")
        video_fps = request.video_info.get("fps", 30)
        
        running_cycle_analysis = analyze_running_cycle(request.pose_data, video_fps)
        
        print(f"📊 重心上下動: {running_cycle_analysis.get('vertical_oscillation', 'N/A')}")
        print(f"🏃 ピッチ: {running_cycle_analysis.get('pitch', 'N/A')} SPM")
        
        # レスポンスを構築
        features = {
            "angle_data": all_angles,
            "angle_statistics": angle_stats,
            "frame_count": len(all_angles),
            "running_metrics": {
                "vertical_oscillation": running_cycle_analysis.get('vertical_oscillation'),
                "pitch": running_cycle_analysis.get('pitch'),
                "vertical_oscillation_ratio": running_cycle_analysis.get('vertical_oscillation'),
                "cadence_spm": running_cycle_analysis.get('pitch')
            }
        }
        
        analysis_details = {
            "total_frames_analyzed": len(request.pose_data),
            "valid_frames": valid_frames,
            "detection_rate": round(valid_frames / len(request.pose_data) * 100, 1) if request.pose_data else 0,
            "video_duration": request.video_info.get("duration", 0),
            "fps": request.video_info.get("fps", 30)
        }
        
        print("✅ 特徴量抽出完了")
        
        return FeatureExtractionResponse(
            status="success",
            message="絶対角度・重心上下動・ピッチの特徴量抽出が完了しました",
            features=features,
            analysis_details=analysis_details
        )
        
    except Exception as e:
        print(f"❌ 特徴量抽出エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"特徴量抽出に失敗しました: {str(e)}")

@app.get("/")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {
        "service": "Feature Extraction Service",
        "status": "healthy",
        "version": "3.3.0",
        "description": "絶対角度・重心上下動・ピッチを計算するサービス（自動身長推定・サイクル検出機能付き）",
        "features": [
            "絶対角度計算（体幹・大腿・下腿）",
            "重心上下動（Vertical Oscillation）",
            "ピッチ・ケイデンス（Steps Per Minute）",
            "自動ランニングサイクル検出",
            "骨格データからの自動身長推定"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 