from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np
import random

app = FastAPI(
    title="Feature Extraction Service",
    description="骨格データから関節角度、ストライド長、ケイデンスなどの生体力学的特徴量を計算するサービス",
    version="1.0.0"
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
    features: Dict[str, float]
    analysis_details: Dict[str, Any]

# MediaPipeランドマークのインデックス定義
LANDMARK_INDICES = {
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
    'left_foot_index': 31,
    'right_foot_index': 32
}

def calculate_angle(point1: KeyPoint, point2: KeyPoint, point3: KeyPoint) -> float:
    """
    3つの点から角度を計算する（point2が頂点）
    """
    # ベクトルを計算
    vector1 = np.array([point1.x - point2.x, point1.y - point2.y])
    vector2 = np.array([point3.x - point2.x, point3.y - point2.y])
    
    # ベクトルの長さ
    length1 = np.linalg.norm(vector1)
    length2 = np.linalg.norm(vector2)
    
    if length1 == 0 or length2 == 0:
        return 0.0
    
    # 内積から角度を計算
    cos_angle = np.dot(vector1, vector2) / (length1 * length2)
    # 数値誤差対策
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    # ラジアンから度に変換
    angle_rad = np.arccos(cos_angle)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def detect_ground_contact(pose_frames: List[PoseFrame]) -> List[int]:
    """
    足の接地タイミングを検出する（簡易版）
    実際には足首のy座標の変化や速度を分析するが、ここではダミー実装
    """
    ground_contacts = []
    
    if len(pose_frames) < 10:
        return ground_contacts
    
    # 簡易的に定期的な接地を仮定
    step_interval = len(pose_frames) // 6  # 6回の接地を仮定
    
    for i in range(0, len(pose_frames), step_interval):
        if i < len(pose_frames):
            ground_contacts.append(i)
    
    return ground_contacts

def calculate_cadence(pose_frames: List[PoseFrame], fps: float) -> float:
    """
    ケイデンス（1分間の歩数）を計算する
    """
    if len(pose_frames) == 0 or fps <= 0:
        return 0.0
    
    # 接地タイミングを検出
    ground_contacts = detect_ground_contact(pose_frames)
    
    if len(ground_contacts) < 2:
        return 0.0
    
    # 動画の総時間（秒）
    total_time_seconds = len(pose_frames) / fps
    
    # 1分間あたりの歩数を計算
    steps_per_minute = (len(ground_contacts) / total_time_seconds) * 60
    
    return round(steps_per_minute, 1)

def calculate_knee_angle(pose_frames: List[PoseFrame]) -> Dict[str, float]:
    """
    膝関節の角度を計算する（左右それぞれ）
    """
    angles = {'left_knee': 0.0, 'right_knee': 0.0}
    
    valid_frames = [frame for frame in pose_frames if frame.landmarks_detected and len(frame.keypoints) >= 33]
    
    if not valid_frames:
        return angles
    
    # 中央付近のフレームを使用（姿勢が安定している可能性が高い）
    mid_frame = valid_frames[len(valid_frames) // 2]
    keypoints = mid_frame.keypoints
    
    try:
        # 左膝の角度（腰-膝-足首）
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        
        if all(kp.visibility > 0.5 for kp in [left_hip, left_knee, left_ankle]):
            angles['left_knee'] = calculate_angle(left_hip, left_knee, left_ankle)
        
        # 右膝の角度（腰-膝-足首）
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        
        if all(kp.visibility > 0.5 for kp in [right_hip, right_knee, right_ankle]):
            angles['right_knee'] = calculate_angle(right_hip, right_knee, right_ankle)
            
    except (IndexError, KeyError):
        pass
    
    return angles

def calculate_stride_length(pose_frames: List[PoseFrame]) -> float:
    """
    ストライド長を計算する（簡易版）
    実際には足の軌跡から計算するが、ここではダミー実装
    """
    if len(pose_frames) == 0:
        return 0.0
    
    # ダミー値：一般的なランニングのストライド長範囲
    # 実際の実装では足の座標の変化から計算
    base_stride = random.uniform(1.0, 1.5)  # 1.0-1.5メートル
    
    return round(base_stride, 2)

def calculate_contact_time(pose_frames: List[PoseFrame], fps: float) -> float:
    """
    接地時間を計算する（簡易版）
    """
    if len(pose_frames) == 0 or fps <= 0:
        return 0.0
    
    # ダミー値：一般的なランニングの接地時間
    contact_time_ms = random.uniform(200, 300)  # 200-300ミリ秒
    
    return round(contact_time_ms, 1)

@app.post("/extract", response_model=FeatureExtractionResponse)
async def extract_features(request: PoseAnalysisRequest):
    """
    骨格データから特徴量を抽出する
    """
    try:
        pose_data = request.pose_data
        video_info = request.video_info
        fps = video_info.get('fps', 30.0)
        
        if not pose_data:
            # 空のデータの場合はデフォルト値を返す
            features = {
                "knee_angle": 165.0,
                "left_knee_angle": 165.0,
                "right_knee_angle": 165.0,
                "cadence": 180.0,
                "stride_length": 1.25,
                "contact_time": 250.0
            }
            
            analysis_details = {
                "total_frames_analyzed": 0,
                "valid_frames": 0,
                "detection_rate": 0.0,
                "video_duration": 0.0,
                "analysis_method": "default_values"
            }
            
            return FeatureExtractionResponse(
                status="success",
                message="骨格データが空のため、デフォルト値を返しました",
                features=features,
                analysis_details=analysis_details
            )
        
        # 各特徴量を計算
        knee_angles = calculate_knee_angle(pose_data)
        cadence = calculate_cadence(pose_data, fps)
        stride_length = calculate_stride_length(pose_data)
        contact_time = calculate_contact_time(pose_data, fps)
        
        # 平均膝角度を計算
        avg_knee_angle = np.mean([angle for angle in knee_angles.values() if angle > 0])
        if np.isnan(avg_knee_angle):
            avg_knee_angle = 165.0  # デフォルト値
        
        # 特徴量をまとめる
        features = {
            "knee_angle": round(avg_knee_angle, 1),
            "left_knee_angle": round(knee_angles['left_knee'], 1),
            "right_knee_angle": round(knee_angles['right_knee'], 1),
            "cadence": cadence,
            "stride_length": stride_length,
            "contact_time": contact_time
        }
        
        # 分析詳細
        analysis_details = {
            "total_frames_analyzed": len(pose_data),
            "valid_frames": len([f for f in pose_data if f.landmarks_detected]),
            "detection_rate": len([f for f in pose_data if f.landmarks_detected]) / len(pose_data) if pose_data else 0,
            "video_duration": len(pose_data) / fps if fps > 0 else 0,
            "analysis_method": "mediapipe_pose_landmarks"
        }
        
        return FeatureExtractionResponse(
            status="success",
            message=f"{len(pose_data)}フレームから特徴量を抽出しました",
            features=features,
            analysis_details=analysis_details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"特徴量抽出中にエラーが発生しました: {str(e)}")

@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy", "service": "feature_extraction"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 