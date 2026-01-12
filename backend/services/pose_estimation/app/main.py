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
    
    # フレーム間スムージング用のバッファ（複数フレームの移動平均）
    keypoint_history = []  # 過去Nフレームのキーポイントを保存
    history_size = 5  # 過去5フレームを使用
    smoothing_alpha = 0.6  # スムージング係数を調整（より安定性重視）
    
    # MediaPipe Poseの初期化（精度向上のため設定を最適化）
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,  # 最高精度モデル（0=軽量, 1=標準, 2=高精度）
        enable_segmentation=False,
        min_detection_confidence=0.2,  # さらに低くして検出率を最大化
        min_tracking_confidence=0.2  # さらに低くしてトラッキング安定性を最大化
    ) as pose:
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 画像の前処理：精度向上のための高度な前処理
            # 1. 解像度を上げる（小さい動画の場合）
            scale_factor = max(1.0, 640.0 / max(width, height))
            if scale_factor > 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # 2. ノイズ除去（ガウシアンブラー）
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            
            # 3. バイラテラルフィルター（エッジを保ちながらノイズ除去）
            frame = cv2.bilateralFilter(frame, 5, 50, 50)
            
            # 4. コントラスト調整（CLAHE）
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))  # clipLimitを上げてコントラスト強化
            l = clahe.apply(l)
            frame = cv2.merge([l, a, b])
            frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)
            
            # 5. シャープ化（エッジ強調）
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            frame = cv2.filter2D(frame, -1, kernel * 0.15 + np.eye(3) * 0.55)  # シャープ化を強化
            
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
                current_keypoints = []
                for landmark in results.pose_landmarks.landmark:
                    keypoint = KeyPoint(
                        x=landmark.x,
                        y=landmark.y,
                        z=landmark.z,
                        visibility=landmark.visibility
                    )
                    current_keypoints.append(keypoint)
                    confidence_scores.append(landmark.visibility)
                
                # 左右の区別を改善するためのユークリッド距離による同一性チェック（1-A）
                if len(current_keypoints) > 28 and len(keypoint_history) > 0:
                    # MediaPipeのインデックス定義
                    left_shoulder_idx = 11
                    right_shoulder_idx = 12
                    left_hip_idx = 23
                    right_hip_idx = 24
                    left_knee_idx = 25
                    right_knee_idx = 26
                    left_ankle_idx = 27
                    right_ankle_idx = 28
                    
                    # 前フレームのキーポイントを取得
                    prev_keypoints = keypoint_history[-1]
                    
                    # ユークリッド距離を計算する関数
                    def euclidean_distance(kp1: KeyPoint, kp2: KeyPoint) -> float:
                        """2つのキーポイント間のユークリッド距離を計算"""
                        dx = kp1.x - kp2.x
                        dy = kp1.y - kp2.y
                        dz = kp1.z - kp2.z
                        return np.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    # ユークリッド距離によるID Switch検出（1-A）
                    # 左右の足首について、ID Switchを検出
                    if (len(prev_keypoints) > right_ankle_idx and
                        current_keypoints[left_ankle_idx].visibility > 0.3 and
                        current_keypoints[right_ankle_idx].visibility > 0.3 and
                        prev_keypoints[left_ankle_idx].visibility > 0.3 and
                        prev_keypoints[right_ankle_idx].visibility > 0.3):
                        
                        # 距離を計算
                        # 正しい組み合わせ（左→左、右→右）
                        dist_left_to_left = euclidean_distance(prev_keypoints[left_ankle_idx], current_keypoints[left_ankle_idx])
                        dist_right_to_right = euclidean_distance(prev_keypoints[right_ankle_idx], current_keypoints[right_ankle_idx])
                        dist_correct = dist_left_to_left + dist_right_to_right
                        
                        # 逆の組み合わせ（左→右、右→左）
                        dist_left_to_right = euclidean_distance(prev_keypoints[left_ankle_idx], current_keypoints[right_ankle_idx])
                        dist_right_to_left = euclidean_distance(prev_keypoints[right_ankle_idx], current_keypoints[left_ankle_idx])
                        dist_swapped = dist_left_to_right + dist_right_to_left
                        
                        # ID Switchが発生している場合（逆の方が近い）
                        if dist_swapped < dist_correct * 0.8:  # 20%以上近い場合は入れ替え
                            # 左右の足首を入れ替え（新しいKeyPointインスタンスを作成）
                            left_ankle_data = current_keypoints[left_ankle_idx]
                            right_ankle_data = current_keypoints[right_ankle_idx]
                            current_keypoints[left_ankle_idx] = KeyPoint(
                                x=right_ankle_data.x,
                                y=right_ankle_data.y,
                                z=right_ankle_data.z,
                                visibility=right_ankle_data.visibility
                            )
                            current_keypoints[right_ankle_idx] = KeyPoint(
                                x=left_ankle_data.x,
                                y=left_ankle_data.y,
                                z=left_ankle_data.z,
                                visibility=left_ankle_data.visibility
                            )
                    
                    # 左右の膝についても同様にチェック
                    if (len(prev_keypoints) > right_knee_idx and
                        current_keypoints[left_knee_idx].visibility > 0.3 and
                        current_keypoints[right_knee_idx].visibility > 0.3 and
                        prev_keypoints[left_knee_idx].visibility > 0.3 and
                        prev_keypoints[right_knee_idx].visibility > 0.3):
                        
                        dist_left_to_left = euclidean_distance(prev_keypoints[left_knee_idx], current_keypoints[left_knee_idx])
                        dist_right_to_right = euclidean_distance(prev_keypoints[right_knee_idx], current_keypoints[right_knee_idx])
                        dist_correct = dist_left_to_left + dist_right_to_right
                        
                        dist_left_to_right = euclidean_distance(prev_keypoints[left_knee_idx], current_keypoints[right_knee_idx])
                        dist_right_to_left = euclidean_distance(prev_keypoints[right_knee_idx], current_keypoints[left_knee_idx])
                        dist_swapped = dist_left_to_right + dist_right_to_left
                        
                        if dist_swapped < dist_correct * 0.8:
                            # 左右の膝を入れ替え（新しいKeyPointインスタンスを作成）
                            left_knee_data = current_keypoints[left_knee_idx]
                            right_knee_data = current_keypoints[right_knee_idx]
                            current_keypoints[left_knee_idx] = KeyPoint(
                                x=right_knee_data.x,
                                y=right_knee_data.y,
                                z=right_knee_data.z,
                                visibility=right_knee_data.visibility
                            )
                            current_keypoints[right_knee_idx] = KeyPoint(
                                x=left_knee_data.x,
                                y=left_knee_data.y,
                                z=left_knee_data.z,
                                visibility=left_knee_data.visibility
                            )
                    
                    # 左右の腰についても同様にチェック
                    if (len(prev_keypoints) > right_hip_idx and
                        current_keypoints[left_hip_idx].visibility > 0.3 and
                        current_keypoints[right_hip_idx].visibility > 0.3 and
                        prev_keypoints[left_hip_idx].visibility > 0.3 and
                        prev_keypoints[right_hip_idx].visibility > 0.3):
                        
                        dist_left_to_left = euclidean_distance(prev_keypoints[left_hip_idx], current_keypoints[left_hip_idx])
                        dist_right_to_right = euclidean_distance(prev_keypoints[right_hip_idx], current_keypoints[right_hip_idx])
                        dist_correct = dist_left_to_left + dist_right_to_right
                        
                        dist_left_to_right = euclidean_distance(prev_keypoints[left_hip_idx], current_keypoints[right_hip_idx])
                        dist_right_to_left = euclidean_distance(prev_keypoints[right_hip_idx], current_keypoints[left_hip_idx])
                        dist_swapped = dist_left_to_right + dist_right_to_left
                        
                        if dist_swapped < dist_correct * 0.8:
                            # 左右の腰を入れ替え（新しいKeyPointインスタンスを作成）
                            left_hip_data = current_keypoints[left_hip_idx]
                            right_hip_data = current_keypoints[right_hip_idx]
                            current_keypoints[left_hip_idx] = KeyPoint(
                                x=right_hip_data.x,
                                y=right_hip_data.y,
                                z=right_hip_data.z,
                                visibility=right_hip_data.visibility
                            )
                            current_keypoints[right_hip_idx] = KeyPoint(
                                x=left_hip_data.x,
                                y=left_hip_data.y,
                                z=left_hip_data.z,
                                visibility=left_hip_data.visibility
                            )
                    
                    # 左右の肩についても同様にチェック（オプション、より安定性を高めるため）
                    if (len(prev_keypoints) > right_shoulder_idx and
                        current_keypoints[left_shoulder_idx].visibility > 0.3 and
                        current_keypoints[right_shoulder_idx].visibility > 0.3 and
                        prev_keypoints[left_shoulder_idx].visibility > 0.3 and
                        prev_keypoints[right_shoulder_idx].visibility > 0.3):
                        
                        dist_left_to_left = euclidean_distance(prev_keypoints[left_shoulder_idx], current_keypoints[left_shoulder_idx])
                        dist_right_to_right = euclidean_distance(prev_keypoints[right_shoulder_idx], current_keypoints[right_shoulder_idx])
                        dist_correct = dist_left_to_left + dist_right_to_right
                        
                        dist_left_to_right = euclidean_distance(prev_keypoints[left_shoulder_idx], current_keypoints[right_shoulder_idx])
                        dist_right_to_left = euclidean_distance(prev_keypoints[right_shoulder_idx], current_keypoints[left_shoulder_idx])
                        dist_swapped = dist_left_to_right + dist_right_to_left
                        
                        if dist_swapped < dist_correct * 0.8:
                            # 左右の肩を入れ替え（新しいKeyPointインスタンスを作成）
                            left_shoulder_data = current_keypoints[left_shoulder_idx]
                            right_shoulder_data = current_keypoints[right_shoulder_idx]
                            current_keypoints[left_shoulder_idx] = KeyPoint(
                                x=right_shoulder_data.x,
                                y=right_shoulder_data.y,
                                z=right_shoulder_data.z,
                                visibility=right_shoulder_data.visibility
                            )
                            current_keypoints[right_shoulder_idx] = KeyPoint(
                                x=left_shoulder_data.x,
                                y=left_shoulder_data.y,
                                z=left_shoulder_data.z,
                                visibility=left_shoulder_data.visibility
                            )
                    
                    # 構造的制約チェック（膝と足首の関係）
                    # 左膝(25)と左足首(27)の関係
                    if (current_keypoints[left_knee_idx].visibility > 0.3 and 
                        current_keypoints[left_ankle_idx].visibility > 0.3):
                        # 左足首は左膝より下（y座標が大きい）であるべき
                        if current_keypoints[left_ankle_idx].y < current_keypoints[left_knee_idx].y - 0.15:
                            # 前フレームの値を使用（新しいKeyPointインスタンスを作成）
                            if len(keypoint_history) > 0 and len(keypoint_history[-1]) > left_ankle_idx:
                                prev_ankle = keypoint_history[-1][left_ankle_idx]
                                current_keypoints[left_ankle_idx] = KeyPoint(
                                    x=prev_ankle.x,
                                    y=prev_ankle.y,
                                    z=prev_ankle.z,
                                    visibility=prev_ankle.visibility
                                )
                    
                    # 右膝(26)と右足首(28)の関係
                    if (current_keypoints[right_knee_idx].visibility > 0.3 and 
                        current_keypoints[right_ankle_idx].visibility > 0.3):
                        # 右足首は右膝より下（y座標が大きい）であるべき
                        if current_keypoints[right_ankle_idx].y < current_keypoints[right_knee_idx].y - 0.15:
                            # 前フレームの値を使用（新しいKeyPointインスタンスを作成）
                            if len(keypoint_history) > 0 and len(keypoint_history[-1]) > right_ankle_idx:
                                prev_ankle = keypoint_history[-1][right_ankle_idx]
                                current_keypoints[right_ankle_idx] = KeyPoint(
                                    x=prev_ankle.x,
                                    y=prev_ankle.y,
                                    z=prev_ankle.z,
                                    visibility=prev_ankle.visibility
                                )
                
                # 複数フレームの移動平均によるスムージング
                keypoint_history.append(current_keypoints)
                if len(keypoint_history) > history_size:
                    keypoint_history.pop(0)
                
                # 過去Nフレームの加重平均を計算
                if len(keypoint_history) > 1:
                    smoothed_keypoints = []
                    for i in range(len(current_keypoints)):
                        # 各キーポイントについて、過去フレームの加重平均を計算
                        weights = []
                        values_x = []
                        values_y = []
                        values_z = []
                        visibilities = []
                        
                        # 過去フレームから重み付き平均を計算（新しいフレームほど重みが大きい）
                        for j, hist_kps in enumerate(keypoint_history):
                            if i < len(hist_kps):
                                weight = (j + 1) / len(keypoint_history)  # 新しいフレームほど重い
                                if hist_kps[i].visibility > 0.2:  # 信頼度が低いものは除外
                                    weights.append(weight * hist_kps[i].visibility)
                                    values_x.append(hist_kps[i].x)
                                    values_y.append(hist_kps[i].y)
                                    values_z.append(hist_kps[i].z)
                                    visibilities.append(hist_kps[i].visibility)
                        
                        if len(values_x) > 0:
                            # 加重平均を計算
                            total_weight = sum(weights)
                            if total_weight > 0:
                                avg_x = sum(vx * w for vx, w in zip(values_x, weights)) / total_weight
                                avg_y = sum(vy * w for vy, w in zip(values_y, weights)) / total_weight
                                avg_z = sum(vz * w for vz, w in zip(values_z, weights)) / total_weight
                                avg_visibility = max(visibilities)  # 最大信頼度を使用
                            else:
                                # 重みがない場合は現フレームの値を使用
                                avg_x = current_keypoints[i].x
                                avg_y = current_keypoints[i].y
                                avg_z = current_keypoints[i].z
                                avg_visibility = current_keypoints[i].visibility
                        else:
                            # データがない場合は現フレームの値を使用
                            avg_x = current_keypoints[i].x
                            avg_y = current_keypoints[i].y
                            avg_z = current_keypoints[i].z
                            avg_visibility = current_keypoints[i].visibility
                        
                        smoothed_keypoints.append(KeyPoint(
                            x=avg_x,
                            y=avg_y,
                            z=avg_z,
                            visibility=avg_visibility
                        ))
                    keypoints = smoothed_keypoints
                else:
                    # 履歴が少ない場合はそのまま使用
                    keypoints = current_keypoints
                
                # 平均信頼度を計算
                confidence_score = np.mean(confidence_scores) if confidence_scores else 0.0
            else:
                # 検出失敗時は履歴から補間
                if len(keypoint_history) > 0:
                    landmarks_detected = True
                    # 最新の履歴を使用（信頼度を下げる）
                    last_keypoints = keypoint_history[-1]
                    for last_kp in last_keypoints:
                        keypoints.append(KeyPoint(
                            x=last_kp.x,
                            y=last_kp.y,
                            z=last_kp.z,
                            visibility=last_kp.visibility * 0.6  # 信頼度を40%減衰
                        ))
                    confidence_score = np.mean([kp.visibility for kp in keypoints]) if keypoints else 0.0
                else:
                    landmarks_detected = False
                    confidence_score = 0.0
            
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