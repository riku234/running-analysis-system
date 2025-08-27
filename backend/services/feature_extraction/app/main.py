from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np

app = FastAPI(
    title="Feature Extraction Service",
    description="骨格データから絶対角度（体幹・大腿・下腿）を計算するサービス",
    version="3.0.0"
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
        
        # レスポンスを構築
        features = {
            "angle_data": all_angles,
            "angle_statistics": angle_stats,
            "frame_count": len(all_angles)
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
            message="絶対角度の特徴量抽出が完了しました",
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
        "version": "3.0.0",
        "description": "絶対角度（体幹・大腿・下腿）を計算するサービス"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 