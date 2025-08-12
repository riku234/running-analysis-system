from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import cv2
import mediapipe as mp
import numpy as np
import os
import json
from pathlib import Path

app = FastAPI(
    title="Pose Estimation Service",
    description="動画フレームからランナーの骨格キーポイントを検出するサービス（YOLO + MediaPipe）",
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

# MediaPipeのセットアップ
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# アップロードディレクトリの設定
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class VideoEstimationRequest(BaseModel):
    video_path: str
    confidence_threshold: Optional[float] = 0.5

class PoseEstimationRequest(BaseModel):
    video_id: str
    frame_paths: List[str]

class KeyPoint(BaseModel):
    x: float
    y: float
    z: float
    visibility: float

class FramePoseData(BaseModel):
    frame_number: int
    timestamp: float
    keypoints: List[KeyPoint]
    landmarks_detected: bool
    confidence_score: float

class PoseEstimationResponse(BaseModel):
    status: str
    message: str
    video_info: Dict[str, Any]
    pose_data: List[FramePoseData]
    summary: Dict[str, Any]

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "pose_estimation"}

def extract_pose_from_video(video_path: str, confidence_threshold: float = 0.5) -> PoseEstimationResponse:
    """
    動画ファイルから骨格キーポイントを抽出する
    
    Args:
        video_path: 動画ファイルのパス
        confidence_threshold: 信頼度の閾値
        
    Returns:
        骨格キーポイントの検出結果
    """
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"動画ファイルが見つかりません: {video_path}")
    
    # OpenCVで動画を開く
    cap = cv2.VideoCapture(video_path)
    
    # 動画情報の取得
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    video_info = {
        "fps": fps,
        "total_frames": total_frames,
        "duration_seconds": duration,
        "width": width,
        "height": height
    }
    
    pose_data_list = []
    frame_number = 0
    
    # MediaPipe Poseの初期化
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=confidence_threshold,
        min_tracking_confidence=confidence_threshold
    ) as pose:
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # BGR to RGB変換（MediaPipe用）
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # ポーズ検出の実行
            results = pose.process(rgb_frame)
            
            # タイムスタンプの計算
            timestamp = frame_number / fps if fps > 0 else 0
            
            keypoints = []
            landmarks_detected = False
            confidence_score = 0.0
            
            if results.pose_landmarks:
                landmarks_detected = True
                confidence_scores = []
                
                # 各ランドマークのキーポイントを抽出
                for landmark in results.pose_landmarks.landmark:
                    keypoint = KeyPoint(
                        x=landmark.x,
                        y=landmark.y,
                        z=landmark.z,
                        visibility=landmark.visibility
                    )
                    keypoints.append(keypoint)
                    confidence_scores.append(landmark.visibility)
                
                # 平均信頼度を計算
                confidence_score = np.mean(confidence_scores) if confidence_scores else 0.0
            
            # フレームのポーズデータを作成
            frame_pose_data = FramePoseData(
                frame_number=frame_number,
                timestamp=timestamp,
                keypoints=keypoints,
                landmarks_detected=landmarks_detected,
                confidence_score=float(confidence_score)
            )
            
            pose_data_list.append(frame_pose_data)
            frame_number += 1
    
    cap.release()
    
    # サマリー情報の計算
    detected_frames = sum(1 for pose_data in pose_data_list if pose_data.landmarks_detected)
    avg_confidence = np.mean([pose_data.confidence_score for pose_data in pose_data_list if pose_data.landmarks_detected]) if detected_frames > 0 else 0.0
    
    summary = {
        "total_processed_frames": len(pose_data_list),
        "detected_pose_frames": detected_frames,
        "detection_rate": detected_frames / len(pose_data_list) if len(pose_data_list) > 0 else 0.0,
        "average_confidence": float(avg_confidence),
        "mediapipe_landmarks_count": 33  # MediaPipe Poseは33個のランドマーク
    }
    
    return PoseEstimationResponse(
        status="success",
        message=f"骨格検出が完了しました。{detected_frames}/{len(pose_data_list)}フレームで姿勢を検出",
        video_info=video_info,
        pose_data=pose_data_list,
        summary=summary
    )

@app.post("/estimate", response_model=PoseEstimationResponse)
async def estimate_pose_from_video(request: VideoEstimationRequest):
    """
    動画ファイルから骨格キーポイントを検出する
    
    Args:
        request: 動画パスと設定を含むリクエスト
        
    Returns:
        骨格キーポイントの検出結果
    """
    try:
        result = extract_pose_from_video(
            video_path=request.video_path,
            confidence_threshold=request.confidence_threshold
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"骨格検出処理中にエラーが発生しました: {str(e)}"
        )

@app.post("/estimate_legacy")
async def estimate_pose_legacy(request: PoseEstimationRequest):
    """
    レガシー API: 動画フレームから骨格キーポイントを検出する（ダミーデータ）
    
    Args:
        request: 動画IDとフレームパスのリスト
        
    Returns:
        各フレームの骨格検出結果（ダミー）
    """
    # ダミーレスポンス（既存のインターフェース互換性のため）
    return {
        "status": "success",
        "video_id": request.video_id,
        "total_frames": len(request.frame_paths),
        "detected_poses": len(request.frame_paths),
        "pose_data": [
            {
                "frame_number": i,
                "timestamp": i * 0.033,
                "keypoints": {
                    "nose": {"x": 0.5, "y": 0.3, "confidence": 0.95},
                    "left_shoulder": {"x": 0.4, "y": 0.4, "confidence": 0.92},
                    "right_shoulder": {"x": 0.6, "y": 0.4, "confidence": 0.91}
                }
            } for i in range(len(request.frame_paths))
        ],
        "model_info": {
            "mediapipe_version": "0.10.7",
            "detection_confidence": 0.5,
            "tracking_confidence": 0.5
        }
    }

@app.get("/models/info")
async def get_model_info():
    """使用中のAIモデル情報を取得"""
    return {
        "yolo": {
            "version": "YOLOv8n",
            "weights": "yolov8n.pt",
            "input_size": [640, 640]
        },
        "mediapipe": {
            "version": "0.10.0",
            "model": "pose_landmarker_heavy.task",
            "keypoints": 33
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 