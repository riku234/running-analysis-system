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
import math
import csv
import time
from datetime import datetime
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

# =============================================================================
# OneEuroFilter クラス（スムージング用）
# =============================================================================
class LowPassFilter:
    """ローパスフィルタ（1次IIRフィルタ）"""
    def __init__(self, alpha, init_value=None):
        self.__setAlpha(alpha)
        self.y = init_value
        self.s = init_value

    def __setAlpha(self, alpha):
        alpha = float(alpha)
        if alpha <= 0 or alpha > 1.0:
            self.alpha = 1.0  # フィルタなし
        else:
            self.alpha = alpha

    def filter(self, value, alpha=None):
        if alpha is not None:
            self.__setAlpha(alpha)
        if self.s is None:
            self.s = value
        else:
            self.s = self.alpha * value + (1.0 - self.alpha) * self.s
        return self.s

class OneEuroFilter:
    """1€ Filter（リアルタイムスムージング用）"""
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        """
        Args:
            t0: 初期タイムスタンプ（秒）
            x0: 初期値
            min_cutoff: 低速時の最小カットオフ周波数（低いほど滑らかだが遅延増）
            beta: 速度係数（高いほど高速動作時の追従性が良くなる＝遅延減）
            d_cutoff: 微分フィルタのカットオフ周波数
        """
        self.frequency = 0.0
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_filter = LowPassFilter(self.alpha(min_cutoff))
        self.dx_filter = LowPassFilter(self.alpha(d_cutoff))
        self.t_prev = t0
        self.x_filter.s = x0
        self.dx_filter.s = 0

    def alpha(self, cutoff):
        """カットオフ周波数からアルファ値を計算"""
        if self.frequency <= 0:
            return 1.0
        te = 1.0 / self.frequency
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def process(self, t, x):
        """フィルタ処理を実行"""
        t_e = t - self.t_prev

        # タイムスタンプが更新されていない、または異常な場合のガード処理
        if t_e <= 0.0:
            return self.x_filter.s if self.x_filter.s is not None else x
            
        self.frequency = 1.0 / t_e
        self.t_prev = t
        
        # 微分（速度）の計算とフィルタリング
        dx = (x - self.x_filter.s) * self.frequency
        edx = self.dx_filter.filter(dx, self.alpha(self.d_cutoff))
        
        # 速度に応じたカットオフ周波数の動的調整
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self.x_filter.filter(x, self.alpha(cutoff))

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "pose_estimation"}

def extract_pose_from_video(video_path: str, confidence_threshold: float = 0.5, enable_debug_log: bool = False) -> PoseEstimationResponse:
    """
    動画ファイルから骨格キーポイントを抽出する
    
    Args:
        video_path: 動画ファイルのパス
        confidence_threshold: 信頼度の閾値
        enable_debug_log: デバッグログを出力するかどうか
        
    Returns:
        骨格キーポイントの検出結果
    """
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"動画ファイルが見つかりません: {video_path}")
    
    # 処理時間計測用
    timing_info = {
        'total_start': time.time(),
        'video_open': 0,
        'mediapipe_init': 0,
        'frame_processing': [],
        'outlier_rejection': [],
        'oneeuro_filter': [],
        'debug_log_save': 0,
        'total_end': 0
    }
    
    # デバッグログ用のデータ保存（enable_debug_logがTrueの場合のみ）
    debug_data = {
        'raw_mediapipe': [],  # MediaPipeの生データ
        'filtered_oneeuro': [],  # OneEuroFilter後のデータ
        'timestamps': []
    } if enable_debug_log else None
    
    # OpenCVで動画を開く
    timing_info['video_open'] = time.time()
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
    
    # OneEuroFilter用のフィルタ辞書（33個のランドマーク × 3次元(x,y,z)）
    # キー: ランドマークインデックス, 値: {'x': OneEuroFilter, 'y': OneEuroFilter, 'z': OneEuroFilter}
    filters = {}
    
    # Outlier Rejection用：前回の良好な座標を保持
    # キー: ランドマークインデックス, 値: {'x': float, 'y': float, 'z': float}
    last_valid_landmarks = {}
    
    # Outlier Rejection用：連続異常値カウンター
    # キー: ランドマークインデックス, 値: 連続異常値のフレーム数
    outlier_count = {}
    
    # ID Switch検出と構造的制約チェック用の履歴（過去2フレームのみ保持）
    keypoint_history = []
    
    # OneEuroFilterのパラメータ（ランニングは動きが速いので beta を少し大きめに設定）
    MIN_CUTOFF = 0.5  # 静止時のブレ軽減（滑らか重視）
    BETA = 0.01       # 動き出しの反応速度（ラグより滑らかさ優先）
    D_CUTOFF = 1.0    # 微分フィルタのカットオフ周波数
    
    # Outlier Rejectionのパラメータ
    JUMP_THRESHOLD = 0.1  # 1フレームでこれ以上動いたら「異常」とみなす（画面の10%）
    MAX_CONSECUTIVE_OUTLIERS = 5  # 連続して異常値が出続ける場合の最大フレーム数（これを超えたら強制更新）
    
    # MediaPipe Poseの初期化（精度向上のため設定を最適化）
    timing_info['mediapipe_init'] = time.time()
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,  # 最高精度モデル（0=軽量, 1=標準, 2=高精度）
        enable_segmentation=False,
        min_detection_confidence=0.5,  # 誤検出を防ぐため標準値に戻す
        min_tracking_confidence=0.5  # 誤検出を防ぐため標準値に戻す
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
                # 全体の検出信頼度をチェック（誤検出を防ぐため）
                # 主要なキーポイント（肩、腰、膝、足首）の平均visibilityを計算
                key_landmark_indices = [11, 12, 23, 24, 25, 26, 27, 28]  # 左右の肩、腰、膝、足首
                key_visibilities = [results.pose_landmarks.landmark[i].visibility 
                                   for i in key_landmark_indices 
                                   if i < len(results.pose_landmarks.landmark)]
                avg_key_visibility = np.mean(key_visibilities) if key_visibilities else 0.0
                
                # 主要キーポイントの平均visibilityが低い場合は検出を無視（誤検出の可能性）
                confidence_scores = []  # 常に初期化
                is_valid_detection = True
                
                if avg_key_visibility < 0.3:
                    is_valid_detection = False
                else:
                    # 体のプロポーションチェック（コーンなど非人物の誤検出を防止）
                    lm = results.pose_landmarks.landmark
                    shoulder_y = (lm[11].y + lm[12].y) / 2
                    hip_y = (lm[23].y + lm[24].y) / 2
                    torso_height = abs(hip_y - shoulder_y)
                    
                    MIN_TORSO_HEIGHT = 0.08  # 画面高さの8%未満は人物ではない
                    if torso_height < MIN_TORSO_HEIGHT:
                        is_valid_detection = False
                        if frame_number < 5 or frame_number % 30 == 0:
                            print(f"   ⚠️  フレーム{frame_number}: 胴体高さ={torso_height:.4f} < {MIN_TORSO_HEIGHT} → 非人物として除外")
                
                if not is_valid_detection:
                    # 非人物検出: キーポイント抽出をスキップし、検出失敗として扱う
                    landmarks_detected = False
                    confidence_score = 0.0
                else:
                    landmarks_detected = True
                
                # 各ランドマークのキーポイントを抽出（Outlier Rejection → OneEuroFilterでスムージング）
                # ※ is_valid_detectionがFalseの場合はスキップ（非人物検出の場合）
                current_keypoints = []
                raw_keypoints_frame = []  # デバッグ用：MediaPipeの生データ
                filtered_keypoints_frame = []  # デバッグ用：OneEuroFilter後のデータ
                
                for i, landmark in enumerate(results.pose_landmarks.landmark if is_valid_detection else []):
                    # MediaPipeの生データを保存（デバッグ用）
                    if enable_debug_log:
                        raw_keypoints_frame.append({
                            'index': i,
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility
                        })
                    
                    # Outlier Rejection: 異常な「飛び」を検出して前回の値を採用
                    processed_x, processed_y, processed_z = landmark.x, landmark.y, landmark.z
                    
                    if i not in last_valid_landmarks:
                        # 初回フレームはそのまま採用
                        last_valid_landmarks[i] = {'x': landmark.x, 'y': landmark.y, 'z': landmark.z}
                        outlier_count[i] = 0
                    else:
                        prev = last_valid_landmarks[i]
                        
                        # 移動距離（ユークリッド距離の簡易版）をチェック
                        dist = abs(landmark.x - prev['x']) + abs(landmark.y - prev['y'])
                        
                        if dist > JUMP_THRESHOLD:
                            # 異常な飛びを検知
                            outlier_count[i] = outlier_count.get(i, 0) + 1
                            
                            # 連続して異常値が出続ける場合の対策
                            if outlier_count[i] >= MAX_CONSECUTIVE_OUTLIERS:
                                # 強制更新（検出が完全に失敗している可能性があるため）
                                last_valid_landmarks[i] = {'x': landmark.x, 'y': landmark.y, 'z': landmark.z}
                                outlier_count[i] = 0
                                processed_x, processed_y, processed_z = landmark.x, landmark.y, landmark.z
                            else:
                                # 前回の値を維持（フリーズ）
                                processed_x, processed_y, processed_z = prev['x'], prev['y'], prev['z']
                        else:
                            # 正常範囲なら更新
                            last_valid_landmarks[i] = {'x': landmark.x, 'y': landmark.y, 'z': landmark.z}
                            outlier_count[i] = 0
                    
                    # OneEuroFilterでスムージング（Outlier Rejection後の値を使用）
                    if i not in filters:
                        # フィルタが存在しない場合は初期化
                        filters[i] = {
                            'x': OneEuroFilter(timestamp, processed_x, min_cutoff=MIN_CUTOFF, beta=BETA, d_cutoff=D_CUTOFF),
                            'y': OneEuroFilter(timestamp, processed_y, min_cutoff=MIN_CUTOFF, beta=BETA, d_cutoff=D_CUTOFF),
                            'z': OneEuroFilter(timestamp, processed_z, min_cutoff=MIN_CUTOFF, beta=BETA, d_cutoff=D_CUTOFF)
                        }
                        smoothed_x, smoothed_y, smoothed_z = processed_x, processed_y, processed_z
                    else:
                        # フィルタ処理の実行（Outlier Rejection後の値を使用）
                        smoothed_x = filters[i]['x'].process(timestamp, processed_x)
                        smoothed_y = filters[i]['y'].process(timestamp, processed_y)
                        smoothed_z = filters[i]['z'].process(timestamp, processed_z)
                    
                    # OneEuroFilter後のデータを保存（デバッグ用）
                    if enable_debug_log:
                        filtered_keypoints_frame.append({
                            'index': i,
                            'x': smoothed_x,
                            'y': smoothed_y,
                            'z': smoothed_z,
                            'visibility': landmark.visibility
                        })
                    
                    keypoint = KeyPoint(
                        x=smoothed_x,
                        y=smoothed_y,
                        z=smoothed_z,
                        visibility=landmark.visibility
                    )
                    current_keypoints.append(keypoint)
                    confidence_scores.append(landmark.visibility)
                
                # デバッグデータを保存（enable_debug_logがTrueの場合のみ）
                if enable_debug_log and debug_data is not None:
                    debug_data['raw_mediapipe'].append(raw_keypoints_frame)
                    debug_data['filtered_oneeuro'].append(filtered_keypoints_frame)
                    debug_data['timestamps'].append(timestamp)
                
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
                
                # ID Switch検出と構造的制約チェック用に履歴を保存（OneEuroFilterで既にスムージング済み）
                # keypoint_historyはID Switch検出と構造的制約チェックで使用するため、最小限の履歴を保持
                keypoint_history.append(current_keypoints)
                history_size = 2  # ID Switch検出用に過去2フレームのみ保持
                if len(keypoint_history) > history_size:
                    keypoint_history.pop(0)
                
                # OneEuroFilterで既にスムージング済みなので、そのまま使用
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
    
    # デバッグログをファイルに出力（enable_debug_logがTrueで、データが存在する場合のみ）
    if enable_debug_log and debug_data is not None and len(debug_data.get('raw_mediapipe', [])) > 0:
        try:
            # タイムスタンプ付きのファイル名を生成
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = Path(video_path).stem
            
            # JSON形式で出力
            json_output_path = f"debug_coordinates_{video_name}_{timestamp_str}.json"
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            print(f"📊 デバッグログ（JSON）を出力しました: {json_output_path}")
            
            # CSV形式で出力（フレームごと、キーポイントごと）
            csv_output_path = f"debug_coordinates_{video_name}_{timestamp_str}.csv"
            with open(csv_output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # ヘッダー行
                writer.writerow([
                    'frame_number', 'timestamp', 'keypoint_index',
                    'raw_x', 'raw_y', 'raw_z', 'raw_visibility',
                    'filtered_x', 'filtered_y', 'filtered_z', 'filtered_visibility',
                    'diff_x', 'diff_y', 'diff_z'
                ])
                
                # データ行
                for frame_idx in range(len(debug_data['raw_mediapipe'])):
                    raw_frame = debug_data['raw_mediapipe'][frame_idx]
                    filtered_frame = debug_data['filtered_oneeuro'][frame_idx]
                    timestamp = debug_data['timestamps'][frame_idx]
                    
                    for kp_idx in range(len(raw_frame)):
                        raw_kp = raw_frame[kp_idx]
                        filtered_kp = filtered_frame[kp_idx]
                        
                        # 差分を計算
                        diff_x = filtered_kp['x'] - raw_kp['x']
                        diff_y = filtered_kp['y'] - raw_kp['y']
                        diff_z = filtered_kp['z'] - raw_kp['z']
                        
                        writer.writerow([
                            frame_idx,
                            f"{timestamp:.6f}",
                            raw_kp['index'],
                            f"{raw_kp['x']:.6f}", f"{raw_kp['y']:.6f}", f"{raw_kp['z']:.6f}", f"{raw_kp['visibility']:.6f}",
                            f"{filtered_kp['x']:.6f}", f"{filtered_kp['y']:.6f}", f"{filtered_kp['z']:.6f}", f"{filtered_kp['visibility']:.6f}",
                            f"{diff_x:.6f}", f"{diff_y:.6f}", f"{diff_z:.6f}"
                        ])
            
            print(f"📊 デバッグログ（CSV）を出力しました: {csv_output_path}")
            print(f"   - 総フレーム数: {len(debug_data['raw_mediapipe'])}")
            print(f"   - キーポイント数: {len(debug_data['raw_mediapipe'][0]) if debug_data['raw_mediapipe'] else 0}")
        except Exception as e:
            print(f"⚠️ デバッグログの出力に失敗しました: {e}")
    
    # サマリー情報の計算
    detected_frames = sum(1 for pose_data in pose_data_list if pose_data.landmarks_detected)
    avg_confidence = np.mean([pose_data.confidence_score for pose_data in pose_data_list if pose_data.landmarks_detected]) if detected_frames > 0 else 0.0
    
    # 処理時間の計算
    timing_info['total_end'] = time.time()
    total_time = timing_info['total_end'] - timing_info['total_start']
    video_open_time = timing_info['video_open'] - timing_info['total_start']
    # MediaPipe初期化時間（mediapipe_initが0の場合は0として扱う）
    if timing_info['mediapipe_init'] > 0:
        mediapipe_init_time = timing_info['mediapipe_init'] - timing_info['video_open']
        frame_processing_start = timing_info['mediapipe_init']
    else:
        mediapipe_init_time = 0.0
        frame_processing_start = timing_info['video_open']
    processing_time = timing_info['total_end'] - frame_processing_start
    
    summary = {
        "total_processed_frames": len(pose_data_list),
        "detected_pose_frames": detected_frames,
        "detection_rate": detected_frames / len(pose_data_list) if len(pose_data_list) > 0 else 0.0,
        "average_confidence": float(avg_confidence),
        "mediapipe_landmarks_count": 33,  # MediaPipe Poseは33個のランドマーク
        "processing_time_seconds": round(total_time, 2),
        "frames_per_second": round(len(pose_data_list) / total_time, 2) if total_time > 0 else 0.0,
        "debug_log_enabled": enable_debug_log
    }
    
    # 処理時間と検出率のログ出力
    print(f"⏱️  処理時間サマリー:")
    print(f"   - 総処理時間: {total_time:.2f}秒")
    print(f"   - 動画オープン: {video_open_time:.2f}秒")
    print(f"   - MediaPipe初期化: {mediapipe_init_time:.2f}秒")
    print(f"   - フレーム処理: {processing_time:.2f}秒 ({len(pose_data_list)}フレーム)")
    print(f"   - 処理速度: {summary['frames_per_second']:.2f} FPS")
    print(f"📊 検出結果サマリー:")
    print(f"   - 総フレーム数: {len(pose_data_list)}")
    print(f"   - 検出成功フレーム数: {detected_frames}")
    print(f"   - 検出率: {summary['detection_rate']*100:.1f}%")
    print(f"   - 平均信頼度: {avg_confidence:.3f}")
    if enable_debug_log:
        print(f"   - ⚠️  デバッグログ出力が有効です（処理時間に影響する可能性があります）")
    
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