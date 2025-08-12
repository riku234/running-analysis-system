from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any
import math

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

class FeatureExtractionRequest(BaseModel):
    video_id: str
    pose_data: List[Dict[str, Any]]

class BiomechanicalFeatures(BaseModel):
    frame_number: int
    timestamp: float
    joint_angles: Dict[str, float]
    stride_metrics: Dict[str, float]
    cadence: float
    ground_contact_time: float
    vertical_oscillation: float
    foot_strike_pattern: str

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "feature_extraction"}

@app.post("/extract")
async def extract_features(request: FeatureExtractionRequest):
    """
    骨格データから生体力学的特徴量を抽出する
    
    Args:
        request: 動画IDと骨格データのリスト
        
    Returns:
        各フレームの特徴量データ
    """
    # TODO: 関節角度計算（膝、股関節、足首など）
    # TODO: ストライド長・ストライド頻度の計算
    # TODO: ケイデンス（歩調）の計算
    # TODO: 着地時接触時間の推定
    # TODO: 上下動振動の計算
    # TODO: フットストライクパターンの分類（前足部/中足部/踵）
    # TODO: 重心位置・重心移動の追跡
    # TODO: 腕振りの周期性解析
    
    biomechanical_features = []
    
    for i, pose_frame in enumerate(request.pose_data):
        # ダミーの特徴量計算
        features = BiomechanicalFeatures(
            frame_number=i,
            timestamp=i * 0.033,  # 30fps想定
            joint_angles={
                "left_knee_angle": 165.5,  # 膝関節角度（度）
                "right_knee_angle": 168.2,
                "left_hip_angle": 175.8,   # 股関節角度
                "right_hip_angle": 172.4,
                "left_ankle_angle": 98.7,  # 足首角度
                "right_ankle_angle": 101.3,
                "trunk_lean_angle": 2.1    # 体幹前傾角度
            },
            stride_metrics={
                "stride_length": 1.45,     # ストライド長（m）
                "step_length": 0.72,       # ステップ長（m）
                "stride_frequency": 1.8,   # ストライド頻度（Hz）
                "step_width": 0.08         # ステップ幅（m）
            },
            cadence=180.0,                 # ケイデンス（steps/min）
            ground_contact_time=0.25,      # 接地時間（秒）
            vertical_oscillation=0.08,     # 上下動（m）
            foot_strike_pattern="midfoot"  # フットストライクパターン
        )
        biomechanical_features.append(features)
    
    # 全体統計の計算
    avg_cadence = sum(f.cadence for f in biomechanical_features) / len(biomechanical_features)
    avg_stride_length = sum(f.stride_metrics["stride_length"] for f in biomechanical_features) / len(biomechanical_features)
    
    return {
        "status": "success",
        "video_id": request.video_id,
        "total_frames": len(request.pose_data),
        "features": biomechanical_features,
        "summary_statistics": {
            "average_cadence": avg_cadence,
            "average_stride_length": avg_stride_length,
            "dominant_foot_strike": "midfoot",
            "running_efficiency_score": 8.2,
            "symmetry_index": 0.95
        },
        "extraction_metadata": {
            "algorithm_version": "1.0",
            "confidence_threshold": 0.8,
            "processing_time_ms": 150
        }
    }

@app.get("/metrics/definitions")
async def get_metrics_definitions():
    """計算する特徴量の定義と単位を取得"""
    return {
        "joint_angles": {
            "knee_angle": {"unit": "degrees", "description": "膝関節の屈曲角度（180度が完全伸展）"},
            "hip_angle": {"unit": "degrees", "description": "股関節の屈曲・伸展角度"},
            "ankle_angle": {"unit": "degrees", "description": "足首の背屈・底屈角度"},
            "trunk_lean": {"unit": "degrees", "description": "体幹の前傾角度"}
        },
        "stride_metrics": {
            "stride_length": {"unit": "meters", "description": "左右の足が同じ足で連続して接地する距離"},
            "step_length": {"unit": "meters", "description": "片足から反対の足までの距離"},
            "cadence": {"unit": "steps/min", "description": "1分間あたりのステップ数"},
            "ground_contact_time": {"unit": "seconds", "description": "足が地面に接触している時間"}
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 