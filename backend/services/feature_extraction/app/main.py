from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np

app = FastAPI(
    title="Feature Extraction Service",
    description="骨格データから5つの主要な関節角度を計算するサービス",
    version="2.0.0"
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

# MediaPipeランドマークのインデックス定義（完全版）
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

def calculate_angle(p1: KeyPoint, p2: KeyPoint, p3: KeyPoint) -> Optional[float]:
    """
    3つのキーポイント（p1, p2, p3）を受け取り、p2を頂点とする角度を計算する
    
    Args:
        p1: 第1のキーポイント
        p2: 頂点となるキーポイント
        p3: 第3のキーポイント
    
    Returns:
        角度（度数法）または None（無効な入力の場合）
    """
    try:
        # 入力の妥当性をチェック
        if any(kp.visibility < 0.5 for kp in [p1, p2, p3]):
            return None
        
        # ベクトル p2->p1 と p2->p3 を作成
        vector1 = np.array([p1.x - p2.x, p1.y - p2.y])
        vector2 = np.array([p3.x - p2.x, p3.y - p2.y])
        
        # ベクトルの長さを計算
        length1 = np.linalg.norm(vector1)
        length2 = np.linalg.norm(vector2)
        
        # ベクトルの長さが0の場合は無効
        if length1 == 0 or length2 == 0:
            return None
        
        # 内積を利用して角度を計算
        cos_angle = np.dot(vector1, vector2) / (length1 * length2)
        
        # 数値誤差対策：cosの値を[-1, 1]にクリップ
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # ラジアンから度数法に変換
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
        
    except Exception:
        return None

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算する
    肩の中心点と腰の中心点をつなぐベクトルと垂直ベクトルとの角度
    """
    try:
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        
        # すべてのキーポイントが有効か確認
        if any(kp.visibility < 0.5 for kp in [left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        # 肩の中心点と腰の中心点を計算
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        
        # 体幹ベクトル（腰から肩へ）
        trunk_vector = np.array([shoulder_center_x - hip_center_x, shoulder_center_y - hip_center_y])
        
        # 垂直ベクトル（上向き）
        vertical_vector = np.array([0, -1])
        
        # ベクトルの長さを計算
        trunk_length = np.linalg.norm(trunk_vector)
        if trunk_length == 0:
            return None
        
        # 角度を計算
        cos_angle = np.dot(trunk_vector, vertical_vector) / trunk_length
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
        
    except Exception:
        return None

def extract_joint_angles_from_frame(keypoints: List[KeyPoint]) -> Dict[str, Optional[float]]:
    """
    1フレームから全ての関節角度を抽出する
    """
    angles = {}
    
    try:
        # ① 体幹角度
        angles['trunk_angle'] = calculate_trunk_angle(keypoints)
        
        # 肩の中心点を計算（股関節角度用）
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        if left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5:
            shoulder_center = KeyPoint(
                x=(left_shoulder.x + right_shoulder.x) / 2,
                y=(left_shoulder.y + right_shoulder.y) / 2,
                z=(left_shoulder.z + right_shoulder.z) / 2,
                visibility=min(left_shoulder.visibility, right_shoulder.visibility)
            )
        else:
            shoulder_center = None
        
        # ② 股関節角度（左右）
        if shoulder_center:
            left_hip = keypoints[LANDMARK_INDICES['left_hip']]
            left_knee = keypoints[LANDMARK_INDICES['left_knee']]
            angles['left_hip_angle'] = calculate_angle(shoulder_center, left_hip, left_knee)
            
            right_hip = keypoints[LANDMARK_INDICES['right_hip']]
            right_knee = keypoints[LANDMARK_INDICES['right_knee']]
            angles['right_hip_angle'] = calculate_angle(shoulder_center, right_hip, right_knee)
        else:
            angles['left_hip_angle'] = None
            angles['right_hip_angle'] = None
        
        # ③ 膝関節角度（左右）
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        angles['left_knee_angle'] = calculate_angle(left_hip, left_knee, left_ankle)
        
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        angles['right_knee_angle'] = calculate_angle(right_hip, right_knee, right_ankle)
        
        # ④ 足関節角度（左右）
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        left_foot_index = keypoints[LANDMARK_INDICES['left_foot_index']]
        angles['left_ankle_angle'] = calculate_angle(left_knee, left_ankle, left_foot_index)
        
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        right_foot_index = keypoints[LANDMARK_INDICES['right_foot_index']]
        angles['right_ankle_angle'] = calculate_angle(right_knee, right_ankle, right_foot_index)
        
        # ⑤ 肘関節角度（左右）
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        left_elbow = keypoints[LANDMARK_INDICES['left_elbow']]
        left_wrist = keypoints[LANDMARK_INDICES['left_wrist']]
        angles['left_elbow_angle'] = calculate_angle(left_shoulder, left_elbow, left_wrist)
        
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        right_elbow = keypoints[LANDMARK_INDICES['right_elbow']]
        right_wrist = keypoints[LANDMARK_INDICES['right_wrist']]
        angles['right_elbow_angle'] = calculate_angle(right_shoulder, right_elbow, right_wrist)
        
    except (IndexError, KeyError):
        # キーポイントが不足している場合はすべてNoneを返す
        for key in ['trunk_angle', 'left_hip_angle', 'right_hip_angle', 
                   'left_knee_angle', 'right_knee_angle', 'left_ankle_angle', 
                   'right_ankle_angle', 'left_elbow_angle', 'right_elbow_angle']:
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
    骨格データから5つの主要な関節角度を抽出する
    """
    try:
        pose_data = request.pose_data
        video_info = request.video_info
        fps = video_info.get('fps', 30.0)
        
        if not pose_data:
            # 空のデータの場合はデフォルト値を返す
            default_stats = {"avg": 0.0, "min": 0.0, "max": 0.0}
            features = {
                "trunk_angle": default_stats.copy(),
                "left_hip_angle": default_stats.copy(),
                "right_hip_angle": default_stats.copy(),
                "left_knee_angle": default_stats.copy(),
                "right_knee_angle": default_stats.copy(),
                "left_ankle_angle": default_stats.copy(),
                "right_ankle_angle": default_stats.copy(),
                "left_elbow_angle": default_stats.copy(),
                "right_elbow_angle": default_stats.copy()
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
        
        # 各角度の時系列データを格納する辞書
        angle_timeseries = {
            'trunk_angle': [],
            'left_hip_angle': [],
            'right_hip_angle': [],
            'left_knee_angle': [],
            'right_knee_angle': [],
            'left_ankle_angle': [],
            'right_ankle_angle': [],
            'left_elbow_angle': [],
            'right_elbow_angle': []
        }
        
        valid_frame_count = 0
        
        # 全フレームをループ処理
        for frame in pose_data:
            if not frame.landmarks_detected or len(frame.keypoints) < 33:
                continue
            
            # フレームから角度を抽出
            frame_angles = extract_joint_angles_from_frame(frame.keypoints)
            
            # 有効な角度を時系列データに追加
            for angle_name, angle_value in frame_angles.items():
                if angle_value is not None and not np.isnan(angle_value):
                    angle_timeseries[angle_name].append(angle_value)
            
            valid_frame_count += 1
        
        # 各角度の統計値を計算
        features = {}
        for angle_name, values in angle_timeseries.items():
            features[angle_name] = calculate_angle_statistics(values)
        
        # 分析詳細
        analysis_details = {
            "total_frames_analyzed": len(pose_data),
            "valid_frames": valid_frame_count,
            "detection_rate": valid_frame_count / len(pose_data) if pose_data else 0,
            "video_duration": len(pose_data) / fps if fps > 0 else 0,
            "analysis_method": "mediapipe_pose_landmarks_v2",
            "angle_data_points": {name: len(values) for name, values in angle_timeseries.items()}
        }
        
        return FeatureExtractionResponse(
            status="success",
            message=f"{len(pose_data)}フレームから5つの主要関節角度を抽出しました",
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
    return {"status": "healthy", "service": "feature_extraction", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 