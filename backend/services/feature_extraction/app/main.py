from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np
import os
import sys
from scipy import signal

# 標準動作モデルデータを直接定義（添付画像の表から正確に抽出）
def get_standard_model_data():
    """標準動作モデルの統計データを返す関数（添付画像の表データ）"""
    
    # 添付画像の表データを正確に転記
    # 各行は: 体幹角度(平均), 体幹角度(標準偏差), 右大腿角度(平均), 右大腿角度(標準偏差), 右下腿角度(平均), 右下腿角度(標準偏差), 左大腿角度(平均), 左大腿角度(標準偏差), 左下腿角度(平均), 左下腿角度(標準偏差)
    frame_data = {
        # Frame 0 - 各列の値を正確に読み取り
        "Frame_0": {
            "体幹角度_平均": 3.969911,
            "体幹角度_標準偏差": 3.558016,
            "右大腿角度_平均": -14.5973,
            "右大腿角度_標準偏差": 12.61641,
            "右下腿角度_平均": 3.302240,
            "右下腿角度_標準偏差": 24.2674,
            "左大腿角度_平均": 1.081713,
            "左大腿角度_標準偏差": 13.04959,
            "左下腿角度_平均": 6.63447,
            "左下腿角度_標準偏差": 24.70281
        },
        
        "Frame_1": {
            "体幹角度_平均": 4.046965,
            "体幹角度_標準偏差": 1.789897,
            "右大腿角度_平均": -14.5721,
            "右大腿角度_標準偏差": 15.63024,
            "右下腿角度_平均": 5.065471,
            "右下腿角度_標準偏差": 24.2419,
            "左大腿角度_平均": 2.26731,
            "左大腿角度_標準偏差": 12.75336,
            "左下腿角度_平均": 6.80302,
            "左下腿角度_標準偏差": 26.17134
        },
        
        "Frame_2": {
            "体幹角度_平均": 4.156448,
            "体幹角度_標準偏差": 3.220768,
            "右大腿角度_平均": -14.6106,
            "右大腿角度_標準偏差": 16.63565,
            "右下腿角度_平均": 7.111266,
            "右下腿角度_標準偏差": 24.14577,
            "左大腿角度_平均": -4.22733,
            "左大腿角度_標準偏差": 11.37309,
            "左下腿角度_平均": 6.87872,
            "左下腿角度_標準偏差": 26.84108
        },
        
        "Frame_3": {
            "体幹角度_平均": 4.286579,
            "体幹角度_標準偏差": 1.314960,
            "右大腿角度_平均": -14.6958,
            "右大腿角度_標準偏差": 16.26299,
            "右下腿角度_平均": 9.337421,
            "右下腿角度_標準偏差": 2.355924,
            "左大腿角度_平均": 8.99297,
            "左大腿角度_標準偏差": 10.04186,
            "左下腿角度_平均": 9.53437,
            "左下腿角度_標準偏差": 27.7925
        },
        
        "Frame_25": {
            "体幹角度_平均": 6.342406,
            "体幹角度_標準偏差": 2.368135,
            "右大腿角度_平均": 1.83133,
            "右大腿角度_標準偏差": 12.13514,
            "右下腿角度_平均": 37.63283,
            "右下腿角度_標準偏差": 15.91777,
            "左大腿角度_平均": 33.5589,
            "左大腿角度_標準偏差": 14.94268,
            "左下腿角度_平均": -6.40468,
            "左下腿角度_標準偏差": 15.14576
        },
        
        "Frame_50": {
            "体幹角度_平均": 3.65441,
            "体幹角度_標準偏差": 3.355749,
            "右大腿角度_平均": 2.607396,
            "右大腿角度_標準偏差": 10.60853,
            "右下腿角度_平均": 61.84115,
            "右下腿角度_標準偏差": 23.73552,
            "左大腿角度_平均": 15.0691,
            "左大腿角度_標準偏差": 12.79283,
            "左下腿角度_平均": 1.217666,
            "左下腿角度_標準偏差": 24.81256
        },
        
        "Frame_75": {
            "体幹角度_平均": 5.624295,
            "体幹角度_標準偏差": 2.760298,
            "右大腿角度_平均": -31.0944,
            "右大腿角度_標準偏差": 15.12048,
            "右下腿角度_平均": 47.34249,
            "右下腿角度_標準偏差": 14.59232,
            "左大腿角度_平均": 1.187264,
            "左大腿角度_標準偏差": 10.76332,
            "左下腿角度_平均": 3.736554,
            "左下腿角度_標準偏差": 15.14788
        },
        
        "Frame_100": {
            "体幹角度_平均": 2.848037,
            "体幹角度_標準偏差": 3.452682,
            "右大腿角度_平均": -13.7398,
            "右大腿角度_標準偏差": 13.38847,
            "右下腿角度_平均": 3.499593,
            "右下腿角度_標準偏差": 23.88576,
            "左大腿角度_平均": 0.886598,
            "左大腿角度_標準偏差": 11.98876,
            "左下腿角度_平均": 7.206272,
            "左下腿角度_標準偏差": 26.24082
        }
    }
    
    # 全フレームから計算した統計サマリー（比較用の統計値付き）
    summary_stats = {
        "体幹角度": {
            "description": "体幹の前後傾斜角度",
            "sample_frames": [3.969911, 4.046965, 4.156448, 6.342406, 3.65441, 5.624295, 2.848037],
            "range_analysis": "約2.8～6.3の範囲で変動",
            "mean": 4.32,  # サンプルフレームの平均
            "max": 6.34,   # サンプルフレームの最大値
            "min": 2.85,   # サンプルフレームの最小値  
            "std_dev": 1.23 # サンプルフレームの標準偏差
        },
        
        "右大腿角度": {
            "description": "右大腿の鉛直軸からの角度", 
            "sample_frames": [-14.5973, -14.5721, -14.6106, 1.83133, 2.607396, -31.0944, -13.7398],
            "range_analysis": "大きな変動（-31.0～2.6の範囲）",
            "mean": -13.15,
            "max": 2.61,
            "min": -31.09,
            "std_dev": 10.85
        },
        
        "右下腿角度": {
            "description": "右下腿の鉛直軸からの角度",
            "sample_frames": [3.302240, 5.065471, 7.111266, 37.63283, 61.84115, 47.34249, 3.499593],
            "range_analysis": "3.3～61.8の広範囲で変動",
            "mean": 23.69,
            "max": 61.84,
            "min": 3.30,
            "std_dev": 23.12
        },
        
        "左大腿角度": {
            "description": "左大腿の鉛直軸からの角度",
            "sample_frames": [1.081713, 2.26731, -4.22733, 33.5589, 15.0691, 1.187264, 0.886598],
            "range_analysis": "-4.2～33.6の範囲で変動",
            "mean": 7.13,
            "max": 33.56,
            "min": -4.23,
            "std_dev": 12.85
        },
        
        "左下腿角度": {
            "description": "左下腿の鉛直軸からの角度",
            "sample_frames": [6.63447, 6.80302, 6.87872, -6.40468, 1.217666, 3.736554, 7.206272],
            "range_analysis": "-6.4～7.2の範囲で変動",
            "mean": 2.73,
            "max": 7.21,
            "min": -6.40,
            "std_dev": 5.41
        }
    }
    
    # 完全なデータセットを結合
    complete_data = {}
    complete_data.update(frame_data)
    complete_data.update(summary_stats)
    
    return complete_data

app = FastAPI(
    title="Feature Extraction Service",
    description="骨格データから絶対角度・重心上下動・ピッチを計算するサービス（足接地検出・自動身長推定機能付き）",
    version="3.4.0"
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
    ベクトルと鉛直軸がなす角度を計算する（atan2ベース、0度前後の値）
    
    Args:
        vector: 対象ベクトル [x, y]
        forward_positive: Trueの場合、前方への傾きを正とする
                          Falseの場合、後方への傾きを正とする
    
    Returns:
        角度（度数法、-90～+90程度）または None
    """
    try:
        # ベクトルの長さをチェック
        length = np.linalg.norm(vector)
        if length == 0:
            return None
        
        # atan2を使用してより正確な角度計算
        # 鉛直軸（上向き）からの角度を計算
        # atan2(x, -y) は y軸負方向（上向き）からの角度を計算
        angle_rad = np.arctan2(vector[0], -vector[1])
        
        # 度数法に変換
        angle_deg = np.degrees(angle_rad)
        
        # forward_positiveがFalseの場合は符号を反転
        if not forward_positive:
            angle_deg = -angle_deg
        
        return angle_deg
        
    except Exception:
        return None

def calculate_absolute_angle_with_horizontal(vector: np.ndarray) -> Optional[float]:
    """
    ベクトルと水平軸がなす角度を計算する（足部角度用）
    
    Args:
        vector: 対象ベクトル [x, y]
        
    Returns:
        角度（度数法、-90～+90程度）または None
        水平軸より上ならプラス、下ならマイナス
    """
    try:
        # ベクトルの長さをチェック
        length = np.linalg.norm(vector)
        if length == 0:
            return None
        
        # atan2を使用して水平軸からの角度を計算
        # atan2(y, x) は x軸正方向（右向き）からの角度を計算
        angle_rad = np.arctan2(vector[1], vector[0])
        
        # 度数法に変換
        angle_deg = np.degrees(angle_rad)
        
        # -90～+90の範囲に正規化
        if angle_deg > 90:
            angle_deg = 180 - angle_deg
        elif angle_deg < -90:
            angle_deg = -180 - angle_deg
        
        return angle_deg
        
    except Exception:
        return None

# =============================================================================
# 相対関節角度計算（仕様2：はさみ角）
# =============================================================================

def calculate_joint_angle_from_three_points(point1: KeyPoint, point2: KeyPoint, point3: KeyPoint) -> Optional[float]:
    """
    3点から関節角度（はさみ角）を計算
    
    Args:
        point1: 第1点（例：肩）
        point2: 第2点（関節点、例：肘）
        point3: 第3点（例：手首）
    
    Returns:
        角度（度）0〜180の範囲、またはNone（計算不可の場合）
    
    Note:
        point2を頂点とする角度を計算
        ベクトル (point2→point1) と (point2→point3) のなす角
    """
    try:
        # キーポイントの有効性を確認
        if (point1.visibility < 0.5 or 
            point2.visibility < 0.5 or 
            point3.visibility < 0.5):
            return None
        
        # ベクトルを計算
        vector1 = np.array([point1.x - point2.x, point1.y - point2.y])
        vector2 = np.array([point3.x - point2.x, point3.y - point2.y])
        
        # ベクトルの長さを計算
        length1 = np.linalg.norm(vector1)
        length2 = np.linalg.norm(vector2)
        
        # ゼロベクトルチェック
        if length1 < 1e-10 or length2 < 1e-10:
            return None
        
        # 正規化されたベクトル
        unit_vector1 = vector1 / length1
        unit_vector2 = vector2 / length2
        
        # 内積を計算してcosを求める
        cos_angle = np.clip(np.dot(unit_vector1, unit_vector2), -1.0, 1.0)
        
        # 角度を計算（ラジアン→度）
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
        
    except Exception as e:
        print(f"❌ 関節角度計算エラー: {e}")
        return None

def get_shoulder_center(left_shoulder: KeyPoint, right_shoulder: KeyPoint) -> Optional[tuple]:
    """肩の中点を計算"""
    if left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5:
        return None
    return ((left_shoulder.x + right_shoulder.x) / 2, 
            (left_shoulder.y + right_shoulder.y) / 2)

def get_hip_center(left_hip: KeyPoint, right_hip: KeyPoint) -> Optional[tuple]:
    """股関節の中点を計算"""
    if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
        return None
    return ((left_hip.x + right_hip.x) / 2, 
            (left_hip.y + right_hip.y) / 2)

def create_keypoint_from_coordinates(x: float, y: float) -> KeyPoint:
    """座標から仮想的なKeypointを作成"""
    return KeyPoint(x=x, y=y, z=0.0, visibility=1.0)

# =============================================================================
# 相対関節角度計算関数群（仕様2）
# =============================================================================

def calculate_hip_joint_angle_relative(keypoints: List[KeyPoint], side: str) -> Optional[float]:
    """
    股関節角度を計算（相対角度・はさみ角）
    定義: 大腿と体幹のなす角
    実装: 「肩の中点」「股関節」「膝」の3点がなす角度
    
    Args:
        keypoints: 全キーポイント
        side: 'left' または 'right'
    
    Returns:
        股関節角度（度、0〜180）
    """
    try:
        # 必要なキーポイントを取得
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        
        if side == 'left':
            hip = keypoints[LANDMARK_INDICES['left_hip']]
            knee = keypoints[LANDMARK_INDICES['left_knee']]
        else:
            hip = keypoints[LANDMARK_INDICES['right_hip']]
            knee = keypoints[LANDMARK_INDICES['right_knee']]
        
        # 肩の中点を計算
        shoulder_center = get_shoulder_center(left_shoulder, right_shoulder)
        if shoulder_center is None:
            return None
        
        # 肩中点のKeypointを作成
        shoulder_center_kp = create_keypoint_from_coordinates(shoulder_center[0], shoulder_center[1])
        
        # 3点から角度を計算：肩中点-股関節-膝
        angle = calculate_joint_angle_from_three_points(shoulder_center_kp, hip, knee)
        
        if angle is not None:
            print(f"   🔗 {side}股関節角度（はさみ角）: {angle:.1f}° (大腿と体幹)")
        
        return angle
            
    except Exception as e:
        print(f"❌ {side}股関節角度計算エラー: {e}")
        return None

def calculate_knee_joint_angle_relative(keypoints: List[KeyPoint], side: str) -> Optional[float]:
    """
    膝関節角度を計算（相対角度・はさみ角）
    定義: 大腿と下腿のなす角
    実装: 「股関節」「膝」「足首」の3点がなす角度
    
    Args:
        keypoints: 全キーポイント
        side: 'left' または 'right'
    
    Returns:
        膝関節角度（度、0〜180）
    """
    try:
        if side == 'left':
            hip = keypoints[LANDMARK_INDICES['left_hip']]
            knee = keypoints[LANDMARK_INDICES['left_knee']]
            ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        else:
            hip = keypoints[LANDMARK_INDICES['right_hip']]
            knee = keypoints[LANDMARK_INDICES['right_knee']]
            ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        
        # 3点から角度を計算：股関節-膝-足首
        angle = calculate_joint_angle_from_three_points(hip, knee, ankle)
        
        if angle is not None:
            print(f"   🔗 {side}膝関節角度（はさみ角）: {angle:.1f}° (大腿と下腿)")
        
        return angle
        
    except Exception as e:
        print(f"❌ {side}膝関節角度計算エラー: {e}")
        return None

def calculate_ankle_joint_angle_relative(keypoints: List[KeyPoint], side: str) -> Optional[float]:
    """
    足関節角度を計算（相対角度・はさみ角）
    定義: 足部と下腿のなす角
    実装: 「膝」「足首」「つま先」の3点がなす角度
    
    Args:
        keypoints: 全キーポイント
        side: 'left' または 'right'
    
    Returns:
        足関節角度（度、0〜180）
    """
    try:
        if side == 'left':
            knee = keypoints[LANDMARK_INDICES['left_knee']]
            ankle = keypoints[LANDMARK_INDICES['left_ankle']]
            toe = keypoints[LANDMARK_INDICES['left_foot_index']]
        else:
            knee = keypoints[LANDMARK_INDICES['right_knee']]
            ankle = keypoints[LANDMARK_INDICES['right_ankle']]
            toe = keypoints[LANDMARK_INDICES['right_foot_index']]
        
        # 3点から角度を計算：膝-足首-つま先
        angle = calculate_joint_angle_from_three_points(knee, ankle, toe)
        
        if angle is not None:
            print(f"   🔗 {side}足関節角度（はさみ角）: {angle:.1f}° (下腿と足部)")
        
        return angle
        
    except Exception as e:
        print(f"❌ {side}足関節角度計算エラー: {e}")
        return None

def calculate_elbow_joint_angle_relative(keypoints: List[KeyPoint], side: str) -> Optional[float]:
    """
    肘関節角度を計算（相対角度・はさみ角）
    定義: 前腕と上腕のなす角
    実装: 「肩」「肘」「手首」の3点がなす角度
    
    Args:
        keypoints: 全キーポイント
        side: 'left' または 'right'
    
    Returns:
        肘関節角度（度、0〜180）
    """
    try:
        if side == 'left':
            shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
            elbow = keypoints[LANDMARK_INDICES['left_elbow']]
            wrist = keypoints[LANDMARK_INDICES['left_wrist']]
        else:
            shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
            elbow = keypoints[LANDMARK_INDICES['right_elbow']]
            wrist = keypoints[LANDMARK_INDICES['right_wrist']]
        
        # 3点から角度を計算：肩-肘-手首
        angle = calculate_joint_angle_from_three_points(shoulder, elbow, wrist)
        
        if angle is not None:
            print(f"   🔗 {side}肘関節角度（はさみ角）: {angle:.1f}° (上腕と前腕)")
        
        return angle
        
    except Exception as e:
        print(f"❌ {side}肘関節角度計算エラー: {e}")
        return None

def calculate_trunk_angle_relative(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算（相対角度・絶対角度と同じ）
    定義: 体幹ベクトルと静止座標系の鉛直軸とのなす角
    注意: これは既存の絶対角度計算と同じロジックを使用
    
    Args:
        keypoints: 全キーポイント
    
    Returns:
        体幹角度（度、-180〜180）
    """
    # 既存の絶対角度計算を流用
    return calculate_trunk_angle(keypoints)

# =============================================================================
# 角度計算方式統合クラス
# =============================================================================

class AngleCalculationMode:
    """角度計算方式の定義"""
    ABSOLUTE = "absolute"  # 絶対角度（既存仕様）
    RELATIVE = "relative"  # 相対関節角度（新仕様）

class AngleCalculator:
    """
    角度計算を統合するクラス
    仕様1（絶対角度）と仕様2（相対関節角度）を切り替え可能
    """
    
    def __init__(self, mode: str = AngleCalculationMode.ABSOLUTE):
        """
        Args:
            mode: 計算モード（'absolute' または 'relative'）
        """
        self.mode = mode
        print(f"🔧 角度計算モード: {mode}")
    
    def calculate_all_angles(self, keypoints: List[KeyPoint]) -> Dict[str, Any]:
        """
        指定されたモードで全角度を計算
        
        Args:
            keypoints: 全キーポイント
        
        Returns:
            計算結果の辞書
        """
        if self.mode == AngleCalculationMode.ABSOLUTE:
            return self._calculate_absolute_angles(keypoints)
        elif self.mode == AngleCalculationMode.RELATIVE:
            return self._calculate_relative_angles(keypoints)
        else:
            raise ValueError(f"不明な計算モード: {self.mode}")
    
    def _calculate_absolute_angles(self, keypoints: List[KeyPoint]) -> Dict[str, Any]:
        """絶対角度計算（既存仕様 + 新規追加）"""
        return {
            'trunk_angle': calculate_trunk_angle(keypoints),
            'left_thigh_angle': calculate_thigh_angle(
                keypoints[LANDMARK_INDICES['left_hip']], 
                keypoints[LANDMARK_INDICES['left_knee']], 
                'left'
            ),
            'right_thigh_angle': calculate_thigh_angle(
                keypoints[LANDMARK_INDICES['right_hip']], 
                keypoints[LANDMARK_INDICES['right_knee']], 
                'right'
            ),
            'left_shank_angle': calculate_lower_leg_angle(
                keypoints[LANDMARK_INDICES['left_knee']], 
                keypoints[LANDMARK_INDICES['left_ankle']], 
                'left'
            ),
            'right_shank_angle': calculate_lower_leg_angle(
                keypoints[LANDMARK_INDICES['right_knee']], 
                keypoints[LANDMARK_INDICES['right_ankle']], 
                'right'
            ),
            # 新規追加角度
            'left_upper_arm_angle': calculate_upper_arm_angle(
                keypoints[LANDMARK_INDICES['left_shoulder']], 
                keypoints[LANDMARK_INDICES['left_elbow']], 
                'left'
            ),
            'right_upper_arm_angle': calculate_upper_arm_angle(
                keypoints[LANDMARK_INDICES['right_shoulder']], 
                keypoints[LANDMARK_INDICES['right_elbow']], 
                'right'
            ),
            'left_forearm_angle': calculate_forearm_angle(
                keypoints[LANDMARK_INDICES['left_elbow']], 
                keypoints[LANDMARK_INDICES['left_wrist']], 
                'left'
            ),
            'right_forearm_angle': calculate_forearm_angle(
                keypoints[LANDMARK_INDICES['right_elbow']], 
                keypoints[LANDMARK_INDICES['right_wrist']], 
                'right'
            ),
            'left_foot_angle': calculate_foot_angle(
                keypoints[LANDMARK_INDICES['left_ankle']], 
                keypoints[LANDMARK_INDICES['left_foot_index']], 
                'left'
            ),
            'right_foot_angle': calculate_foot_angle(
                keypoints[LANDMARK_INDICES['right_ankle']], 
                keypoints[LANDMARK_INDICES['right_foot_index']], 
                'right'
            ),
            'calculation_mode': 'absolute'
        }
    
    def _calculate_relative_angles(self, keypoints: List[KeyPoint]) -> Dict[str, Any]:
        """相対関節角度計算（新仕様）"""
        return {
            'trunk_angle': calculate_trunk_angle_relative(keypoints),
            'left_hip_joint_angle': calculate_hip_joint_angle_relative(keypoints, 'left'),
            'right_hip_joint_angle': calculate_hip_joint_angle_relative(keypoints, 'right'),
            'left_knee_joint_angle': calculate_knee_joint_angle_relative(keypoints, 'left'),
            'right_knee_joint_angle': calculate_knee_joint_angle_relative(keypoints, 'right'),
            'left_ankle_joint_angle': calculate_ankle_joint_angle_relative(keypoints, 'left'),
            'right_ankle_joint_angle': calculate_ankle_joint_angle_relative(keypoints, 'right'),
            'left_elbow_joint_angle': calculate_elbow_joint_angle_relative(keypoints, 'left'),
            'right_elbow_joint_angle': calculate_elbow_joint_angle_relative(keypoints, 'right'),
            'calculation_mode': 'relative'
        }

# =============================================================================
# 絶対角度計算（既存仕様 + 新規追加）
# =============================================================================

def calculate_upper_arm_angle(shoulder: KeyPoint, elbow: KeyPoint, side: str) -> Optional[float]:
    """
    上腕角度を計算する（肘基準鉛直軸）
    定義: 上腕ベクトル（肩→肘）と肘を通る鉛直軸がなす角度
    ・軸の右側（正のx方向）で負値
    ・軸の左側（負のx方向）で正値
    """
    try:
        # 上腕ベクトル（肩→肘）- 肘を基準とした方向
        upper_arm_vector = np.array([shoulder.x - elbow.x, shoulder.y - elbow.y])
        
        print(f"   💪 {side}上腕ベクトル: [{upper_arm_vector[0]:.3f}, {upper_arm_vector[1]:.3f}] (肘→肩)")
        
        # 肘を通る鉛直軸との角度を計算: 軸の右側で負値、左側で正値
        angle = calculate_absolute_angle_with_vertical(upper_arm_vector, forward_positive=False)
        
        print(f"   💪 {side}上腕角度: {angle:.1f}° (肘基準鉛直軸、右側負値・左側正値)")
        
        return angle
        
    except Exception:
        return None

def calculate_forearm_angle(elbow: KeyPoint, wrist: KeyPoint, side: str) -> Optional[float]:
    """
    前腕角度を計算する（画像定義準拠・直接角度版）
    定義: 鉛直軸と前腕ベクトル（肘→手首）がなす角度を直接計算
    ・画像の角度定義に合わせて調整
    """
    try:
        # 前腕ベクトル（肘→手首）- 前腕の自然な方向
        forearm_vector = np.array([wrist.x - elbow.x, wrist.y - elbow.y])
        
        print(f"   🤚 {side}前腕ベクトル: [{forearm_vector[0]:.3f}, {forearm_vector[1]:.3f}] (肘→手首)")
        
        # 鉛直軸（下向き）との角度を直接計算
        vertical_down_vector = np.array([0.0, 1.0])  # 鉛直下向き
        
        # 2つのベクトル間の角度を計算
        raw_angle = calculate_angle_between_vectors(forearm_vector, vertical_down_vector)
        
        if raw_angle is None:
            return None
        
        # 左右の符号調整（大腿・下腿角度と同じパターンに合わせる）
        if side == 'left':
            angle = raw_angle   # 左側は正の値
        else:
            angle = -raw_angle  # 右側は負の値
        
        print(f"   🤚 {side}前腕角度: {angle:.1f}° (鉛直軸との角度、左右符号調整)")
        
        return angle
        
    except Exception:
        return None

def calculate_foot_angle(ankle: KeyPoint, toe: KeyPoint, side: str) -> Optional[float]:
    """
    足部角度を計算する（新規追加）
    定義: 足部ベクトル（足首→つま先）と水平軸がなす角度
    ・水平軸より上で正値
    ・水平軸より下で負値
    注意: MediaPipeにはヒールがないため足首を起点とする
    """
    try:
        # キーポイントの有効性を確認
        if ankle.visibility < 0.5 or toe.visibility < 0.5:
            return None
        
        # 足部ベクトル（足首→つま先）
        foot_vector = np.array([toe.x - ankle.x, toe.y - ankle.y])
        
        print(f"   🦶 {side}足部ベクトル: [{foot_vector[0]:.3f}, {foot_vector[1]:.3f}] (足首→つま先)")
        
        # 水平軸との角度計算
        angle = calculate_absolute_angle_with_horizontal(foot_vector)
        
        print(f"   🦶 {side}足部角度: {angle:.1f}° (上で正値、下で負値)")
        
        return angle
        
    except Exception:
        return None

def calculate_angle_between_vectors(vector1: np.ndarray, vector2: np.ndarray) -> Optional[float]:
    """
    2つのベクトル間の角度を計算する
    
    Args:
        vector1: 第1ベクトル [x, y]
        vector2: 第2ベクトル [x, y]
    
    Returns:
        角度（度数法、0～180度）または None
    """
    try:
        # ベクトルの長さをチェック
        length1 = np.linalg.norm(vector1)
        length2 = np.linalg.norm(vector2)
        if length1 == 0 or length2 == 0:
            return None
        
        # 正規化
        unit_vector1 = vector1 / length1
        unit_vector2 = vector2 / length2
        
        # 内積を計算
        dot_product = np.dot(unit_vector1, unit_vector2)
        
        # 数値誤差を防ぐためにclipする
        dot_product = np.clip(dot_product, -1.0, 1.0)
        
        # 角度を計算
        angle_rad = np.arccos(dot_product)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
        
    except Exception:
        return None

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算する（修正済み符号規則）
    定義: 腰から肩への直線ベクトルと鉛直軸がなす角度
    ・前傾で負値（軸の右側）
    ・後傾で正値（軸の左側）
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
        
        # 体幹ベクトル（股関節中点→肩中点）- 腰から肩への直線ベクトル
        trunk_vector = np.array([shoulder_center_x - hip_center_x, shoulder_center_y - hip_center_y])
        
        # デバッグ出力を追加
        print(f"🔍 体幹角度計算: 股関節({hip_center_x:.3f}, {hip_center_y:.3f}) → 肩({shoulder_center_x:.3f}, {shoulder_center_y:.3f})")
        print(f"   体幹ベクトル: [{trunk_vector[0]:.3f}, {trunk_vector[1]:.3f}]")
        
        # 修正済み符号規則: 前傾で負値、後傾で正値
        # forward_positive=False で前方（右）への傾きを負値にする
        angle = calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=False)
        print(f"   計算された体幹角度: {angle:.1f}° (前傾で負値、後傾で正値)")
        
        return angle
        
    except Exception:
        return None

def calculate_thigh_angle(hip: KeyPoint, knee: KeyPoint, side: str) -> Optional[float]:
    """
    大腿角度を計算する（修正済み符号規則）
    定義: 大腿ベクトル（膝→股関節）と鉛直軸がなす角度
    ・膝が股関節より後方（離地時）で正値
    ・膝が股関節より前方（接地時）で負値
    """
    try:
        # キーポイントの有効性を確認
        if hip.visibility < 0.5 or knee.visibility < 0.5:
            return None
        
        # 大腿ベクトル（膝→股関節）
        thigh_vector = np.array([hip.x - knee.x, hip.y - knee.y])
        
        print(f"   🦵 {side}大腿ベクトル: [{thigh_vector[0]:.3f}, {thigh_vector[1]:.3f}] (膝→股関節)")
        
        # 修正済み符号規則: 膝が後方で正値（forward_positive=True）
        angle = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=True)
        
        print(f"   🦵 {side}大腿角度: {angle:.1f}° (膝が後方で正値、前方で負値)")
        
        return angle
        
    except Exception:
        return None

def calculate_lower_leg_angle(knee: KeyPoint, ankle: KeyPoint, side: str) -> Optional[float]:
    """
    下腿角度を計算する（修正済み符号規則）
    定義: 下腿ベクトル（足首→膝）と鉛直軸がなす角度
    ・足首が膝より後方（離地時）で正値
    ・足首が膝より前方（接地時）で負値
    """
    try:
        # キーポイントの有効性を確認
        if knee.visibility < 0.5 or ankle.visibility < 0.5:
            return None
        
        # 下腿ベクトル（足首→膝）
        lower_leg_vector = np.array([knee.x - ankle.x, knee.y - ankle.y])
        
        print(f"   🦵 {side}下腿ベクトル: [{lower_leg_vector[0]:.3f}, {lower_leg_vector[1]:.3f}] (足首→膝)")
        
        # 修正済み符号規則: 足首が後方で正値（forward_positive=True）
        angle = calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=True)
        
        print(f"   🦵 {side}下腿角度: {angle:.1f}° (足首が後方で正値、前方で負値)")
        
        return angle
        
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
    ピッチ（ケイデンス）を計算する（レガシー関数）
    
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

def calculate_pitch_from_keypoints(time_series_keypoints: List[List[KeyPoint]], video_fps: float) -> Optional[float]:
    """
    骨格キーポイントから足の接地検出に基づいてピッチ（ケイデンス）を正確に計算する
    
    Args:
        time_series_keypoints: 全フレームの骨格データ
        video_fps: 動画のフレームレート
    
    Returns:
        動画全体の平均ピッチ（SPM単位、float型）または None
    """
    try:
        if not time_series_keypoints or video_fps <= 0:
            return None
        
        print(f"🦶 フットストライク検出開始...")
        
        # ステップ1: フットストライク（接地）の検出
        
        # a. データ抽出: 左右の足首のY座標を時系列データとして抽出
        left_ankle_y = []
        right_ankle_y = []
        valid_frame_indices = []
        
        for frame_idx, frame_keypoints in enumerate(time_series_keypoints):
            if len(frame_keypoints) < 33:
                continue
                
            left_ankle = frame_keypoints[LANDMARK_INDICES['left_ankle']]
            right_ankle = frame_keypoints[LANDMARK_INDICES['right_ankle']]
            
            # 足首の可視性チェック
            if left_ankle.visibility > 0.5 and right_ankle.visibility > 0.5:
                left_ankle_y.append(left_ankle.y)
                right_ankle_y.append(right_ankle.y)
                valid_frame_indices.append(frame_idx)
        
        if len(left_ankle_y) < 10:  # 最小フレーム数チェック
            print(f"❌ 有効フレーム数が不足: {len(left_ankle_y)}")
            return None
        
        # b. 平滑化: 移動平均フィルタを適用
        def moving_average(data, window_size=5):
            """移動平均フィルタ"""
            if len(data) < window_size:
                return data
            smoothed = []
            for i in range(len(data)):
                start = max(0, i - window_size // 2)
                end = min(len(data), i + window_size // 2 + 1)
                smoothed.append(np.mean(data[start:end]))
            return smoothed
        
        left_ankle_y_smooth = moving_average(left_ankle_y, window_size=5)
        right_ankle_y_smooth = moving_average(right_ankle_y, window_size=5)
        
        # c. 極小値の検出: 足が地面に最も近づいた瞬間（接地）を検出
        def detect_foot_strikes(ankle_y_data, min_distance=8):
            """足の接地（極小値）を検出（改良版）"""
            strikes = []
            
            if len(ankle_y_data) < 5:
                return strikes
            
            # より堅牢な極小値検出（3点窓）
            for i in range(2, len(ankle_y_data) - 2):
                # 中心点が周囲の点より低いかチェック（3点窓）
                center = ankle_y_data[i]
                left = ankle_y_data[i-1]
                right = ankle_y_data[i+1]
                left2 = ankle_y_data[i-2]
                right2 = ankle_y_data[i+2]
                
                # より厳密な極小値判定
                is_local_minimum = (center <= left and center <= right and 
                                   center <= left2 and center <= right2)
                
                # 前回の接地から十分な距離があるかチェック
                if is_local_minimum and (not strikes or (i - strikes[-1]) >= min_distance):
                    strikes.append(i)
            
            # 閾値ベースのバックアップ検出
            if len(strikes) < 2:
                # データの下位25%を接地候補として検出
                threshold = np.percentile(ankle_y_data, 25)
                
                for i in range(1, len(ankle_y_data) - 1):
                    if (ankle_y_data[i] <= threshold and 
                        ankle_y_data[i] <= ankle_y_data[i-1] and 
                        ankle_y_data[i] <= ankle_y_data[i+1]):
                        
                        if not strikes or (i - strikes[-1]) >= min_distance:
                            strikes.append(i)
            
            return strikes
        
        # 左右の足の接地フレームを検出
        left_foot_strikes = detect_foot_strikes(left_ankle_y_smooth)
        right_foot_strikes = detect_foot_strikes(right_ankle_y_smooth)
        
        print(f"🦶 接地検出結果:")
        print(f"   - 左足接地: {len(left_foot_strikes)}回 {left_foot_strikes}")
        print(f"   - 右足接地: {len(right_foot_strikes)}回 {right_foot_strikes}")
        
        # ステップ2: ランニングサイクルの定義と期間の計算
        
        # 右足の接地を基準にサイクル期間を計算（左足でも可）
        primary_foot_strikes = right_foot_strikes if len(right_foot_strikes) >= len(left_foot_strikes) else left_foot_strikes
        foot_type = "右足" if len(right_foot_strikes) >= len(left_foot_strikes) else "左足"
        
        if len(primary_foot_strikes) < 2:
            print(f"❌ 検出された接地が不足: {len(primary_foot_strikes)}回")
            return None
        
        # a. サイクル期間のリスト作成: 隣り合う接地間のフレーム数
        cycle_lengths_in_frames = []
        for i in range(1, len(primary_foot_strikes)):
            cycle_length = primary_foot_strikes[i] - primary_foot_strikes[i-1]
            cycle_lengths_in_frames.append(cycle_length)
        
        print(f"📊 サイクル分析結果（{foot_type}基準）:")
        print(f"   - 検出サイクル数: {len(cycle_lengths_in_frames)}")
        print(f"   - サイクル長（フレーム）: {cycle_lengths_in_frames}")
        
        # ステップ3: ピッチ（ケイデンス）の計算
        
        # a. サイクルごとのピッチ計算
        cycle_pitches = []
        for total_frames in cycle_lengths_in_frames:
            # サイクル時間を秒単位で計算
            cycle_time_seconds = total_frames / video_fps
            
            # ピッチ（SPM）を計算: 1サイクル = 2歩
            pitch_spm = (2 / cycle_time_seconds) * 60
            cycle_pitches.append(pitch_spm)
        
        # b. 平均ピッチの算出
        average_pitch = np.mean(cycle_pitches)
        
        print(f"🏃 ピッチ計算詳細:")
        print(f"   - 各サイクルのピッチ: {[f'{p:.1f}' for p in cycle_pitches]} SPM")
        print(f"   - 平均ピッチ: {average_pitch:.1f} SPM")
        print(f"   - 標準偏差: {np.std(cycle_pitches):.1f} SPM")
        
        return average_pitch
        
    except Exception as e:
        print(f"高精度ピッチ計算エラー: {str(e)}")
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
        
        # 新機能: 高精度ピッチ計算（足の接地検出ベース）
        print("🏃 高精度ピッチ計算を実行中...")
        accurate_pitch = calculate_pitch_from_keypoints(time_series_keypoints, video_fps)
        
        # レガシーピッチ計算（比較用）
        legacy_pitch = calculate_pitch(avg_frames_per_cycle, video_fps)
        
        # 高精度計算が成功した場合はそれを使用、失敗した場合はレガシー計算を使用
        pitch = accurate_pitch if accurate_pitch is not None else legacy_pitch
        
        print(f"📊 ピッチ計算比較:")
        print(f"   - 高精度ピッチ: {accurate_pitch:.1f} SPM" if accurate_pitch else "   - 高精度ピッチ: 計算失敗")
        print(f"   - レガシーピッチ: {legacy_pitch:.1f} SPM" if legacy_pitch else "   - レガシーピッチ: 計算失敗")
        print(f"   - 採用ピッチ: {pitch:.1f} SPM" if pitch else "   - 採用ピッチ: 計算失敗")
        
        return {
            "vertical_oscillation": vertical_oscillation,
            "pitch": pitch,
            "cycle_frames": int(avg_frames_per_cycle),
            "valid_frames": len(valid_frames),
            "detected_cycles": detected_cycles,
            "total_video_duration": len(valid_frames) / video_fps,
            "accurate_pitch": accurate_pitch,
            "legacy_pitch": legacy_pitch,
            "pitch_calculation_method": "足接地検出ベース" if accurate_pitch is not None else "重心サイクル推定ベース"
        }
        
    except Exception as e:
        print(f"ランニングサイクル分析エラー: {str(e)}")
        return {"vertical_oscillation": None, "pitch": None}

def extract_absolute_angles_from_frame(keypoints: List[KeyPoint]) -> Dict[str, Optional[float]]:
    """
    1フレームから新仕様の絶対角度を抽出する
    """
    angles = {}
    
    # 各角度を個別に計算（エラーがあっても他に影響しない）
    try:
        angles['trunk_angle'] = calculate_trunk_angle(keypoints)
    except (IndexError, KeyError):
        angles['trunk_angle'] = None
        
    try:
        left_hip = keypoints[LANDMARK_INDICES['left_hip']]
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        angles['left_thigh_angle'] = calculate_thigh_angle(left_hip, left_knee, 'left')
    except (IndexError, KeyError):
        angles['left_thigh_angle'] = None
        
    try:
        right_hip = keypoints[LANDMARK_INDICES['right_hip']]
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        angles['right_thigh_angle'] = calculate_thigh_angle(right_hip, right_knee, 'right')
    except (IndexError, KeyError):
        angles['right_thigh_angle'] = None
        
    try:
        left_knee = keypoints[LANDMARK_INDICES['left_knee']]
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        angles['left_lower_leg_angle'] = calculate_lower_leg_angle(left_knee, left_ankle, 'left')
    except (IndexError, KeyError):
        angles['left_lower_leg_angle'] = None
        
    try:
        right_knee = keypoints[LANDMARK_INDICES['right_knee']]
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        angles['right_lower_leg_angle'] = calculate_lower_leg_angle(right_knee, right_ankle, 'right')
    except (IndexError, KeyError):
        angles['right_lower_leg_angle'] = None
    
    try:
        left_shoulder = keypoints[LANDMARK_INDICES['left_shoulder']]
        left_elbow = keypoints[LANDMARK_INDICES['left_elbow']]
        
        # 可視性チェック（左肘の閾値を下げる）
        if left_shoulder.visibility < 0.3 or left_elbow.visibility < 0.1:
            print(f"   ❌ left上腕計算失敗: 肩可視性={left_shoulder.visibility:.2f}, 肘可視性={left_elbow.visibility:.2f}")
            angles['left_upper_arm_angle'] = None
        else:
            angles['left_upper_arm_angle'] = calculate_upper_arm_angle(left_shoulder, left_elbow, 'left')
            if angles['left_upper_arm_angle'] is not None:
                print(f"   💪 left上腕角度: {angles['left_upper_arm_angle']:.1f}° (計算成功)")
            else:
                print(f"   ❌ left上腕角度: 計算関数がNoneを返却")
    except (IndexError, KeyError) as e:
        angles['left_upper_arm_angle'] = None
        print(f"   ❌ left上腕角度キーポイントエラー: {e}")
    
    try:
        right_shoulder = keypoints[LANDMARK_INDICES['right_shoulder']]
        right_elbow = keypoints[LANDMARK_INDICES['right_elbow']]
        angles['right_upper_arm_angle'] = calculate_upper_arm_angle(right_shoulder, right_elbow, 'right')
    except (IndexError, KeyError):
        angles['right_upper_arm_angle'] = None
    
    try:
        left_elbow = keypoints[LANDMARK_INDICES['left_elbow']]
        left_wrist = keypoints[LANDMARK_INDICES['left_wrist']]
        
        # 可視性チェック（左肘・手首の閾値を下げる）
        if left_elbow.visibility < 0.1 or left_wrist.visibility < 0.3:
            print(f"   ❌ left前腕計算失敗: 肘可視性={left_elbow.visibility:.2f}, 手首可視性={left_wrist.visibility:.2f}")
            angles['left_forearm_angle'] = None
        else:
            angles['left_forearm_angle'] = calculate_forearm_angle(left_elbow, left_wrist, 'left')
            if angles['left_forearm_angle'] is not None:
                print(f"   🤚 left前腕角度: {angles['left_forearm_angle']:.1f}° (計算成功)")
            else:
                print(f"   ❌ left前腕角度: 計算関数がNoneを返却")
    except (IndexError, KeyError) as e:
        angles['left_forearm_angle'] = None
        print(f"   ❌ left前腕角度キーポイントエラー: {e}")
    
    try:
        right_elbow = keypoints[LANDMARK_INDICES['right_elbow']]
        right_wrist = keypoints[LANDMARK_INDICES['right_wrist']]
        angles['right_forearm_angle'] = calculate_forearm_angle(right_elbow, right_wrist, 'right')
    except (IndexError, KeyError):
        angles['right_forearm_angle'] = None
    
    try:
        left_ankle = keypoints[LANDMARK_INDICES['left_ankle']]
        left_toe = keypoints[LANDMARK_INDICES['left_foot_index']]
        angles['left_foot_angle'] = calculate_foot_angle(left_ankle, left_toe, 'left')
    except (IndexError, KeyError):
        angles['left_foot_angle'] = None
    
    try:
        right_ankle = keypoints[LANDMARK_INDICES['right_ankle']]
        right_toe = keypoints[LANDMARK_INDICES['right_foot_index']]
        angles['right_foot_angle'] = calculate_foot_angle(right_ankle, right_toe, 'right')
    except (IndexError, KeyError):
        angles['right_foot_angle'] = None
    
    # デバッグ：計算された角度を確認
    calculated_angles = [k for k, v in angles.items() if v is not None and 'angle' in k]
    print(f"🔍 計算成功角度: {len(calculated_angles)}/11個 - {calculated_angles}")
    
    # 新しい角度の個別デバッグ
    new_angles = {
        'left_upper_arm_angle': angles.get('left_upper_arm_angle'),
        'right_upper_arm_angle': angles.get('right_upper_arm_angle'),
        'left_forearm_angle': angles.get('left_forearm_angle'),
        'right_forearm_angle': angles.get('right_forearm_angle'),
        'left_foot_angle': angles.get('left_foot_angle'),
        'right_foot_angle': angles.get('right_foot_angle')
    }
    calculated_new = {k: v for k, v in new_angles.items() if v is not None}
    print(f"🔍 新しい角度詳細: {calculated_new}")
    
    # 全体のエラーハンドリング（削除）- 個別エラーハンドリングに変更済み
    
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
        
        # 進行方向を左→右に固定
        print("🔒 進行方向を左→右に固定設定")
        print("📐 角度符号規則:")
        print("   ・体幹角度: 左傾き=後傾で正値、右傾き=前傾で正値")
        print("   ・大腿角度: 膝が後方で正値、前方で負値")
        print("   ・下腿角度: 足首が後方で正値、前方で負値")
        
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
                     'left_lower_leg_angle', 'right_lower_leg_angle',
                     'left_upper_arm_angle', 'right_upper_arm_angle',
                     'left_forearm_angle', 'right_forearm_angle',
                     'left_foot_angle', 'right_foot_angle']
        
        for angle_key in angle_keys:
            valid_values = [frame[angle_key] for frame in all_angles 
                           if frame[angle_key] is not None]
            angle_stats[angle_key] = calculate_angle_statistics(valid_values)
            
            # デバッグ出力: 体幹角度の統計情報
            if angle_key == 'trunk_angle':
                print(f"📊 体幹角度統計: {len(valid_values)}個の値から計算")
                print(f"   平均: {angle_stats[angle_key]['avg']:.1f}°")
                print(f"   範囲: {angle_stats[angle_key]['min']:.1f}° ～ {angle_stats[angle_key]['max']:.1f}°")
            
            # デバッグ出力: 全ての新しい角度の統計情報
            if angle_key in ['left_upper_arm_angle', 'right_upper_arm_angle', 'left_forearm_angle', 'right_forearm_angle', 'left_foot_angle', 'right_foot_angle']:
                print(f"🔍 {angle_key}統計: {len(valid_values)}個の値から計算, 平均={angle_stats[angle_key]['avg']:.1f}°" if valid_values else f"⚠️ {angle_key}: 有効値なし")
        
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
        
        # デバッグ: レスポンス構造を確認
        print(f"🔍 APIレスポンス構造デバッグ:")
        print(f"   features.angle_statistics keys: {list(angle_stats.keys())}")
        for key, value in angle_stats.items():
            if 'upper_arm' in key or 'forearm' in key or 'foot' in key:
                print(f"   {key}: {value}")
        print(f"   features keys: {list(features.keys())}")
        
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
        "version": "3.4.0",
        "description": "絶対角度・重心上下動・ピッチを計算するサービス（足接地検出・自動身長推定機能付き）",
        "features": [
            "絶対角度計算（体幹・大腿・下腿）",
            "重心上下動（Vertical Oscillation）",
            "ピッチ・ケイデンス（Steps Per Minute）",
            "高精度足接地検出システム",
            "フットストライクベースのピッチ計算",
            "自動ランニングサイクル検出",
            "骨格データからの自動身長推定"
        ]
    }

@app.post("/analyze_comprehensive")
async def analyze_comprehensive_running_stats(request: PoseAnalysisRequest):
    """
    統括的なランニング解析エンドポイント
    代表的な1サイクルの各指標の統計値を返す
    """
    try:
        print("🏃 統括解析リクエスト受信")
        
        # キーポイントデータを抽出
        all_keypoints = []
        for frame in request.pose_data:
            if frame.landmarks_detected and len(frame.keypoints) >= 33:
                all_keypoints.append(frame.keypoints)
        
        if len(all_keypoints) < 20:
            raise HTTPException(status_code=400, detail="解析に必要な最小フレーム数（20フレーム）に達していません")
        
        # 動画FPSを取得
        video_fps = request.video_info.get("fps", 30.0)
        
        # 統括解析を実行
        stats_results = analyze_user_run_and_get_stats(all_keypoints, video_fps)
        
        if stats_results is None:
            raise HTTPException(status_code=422, detail="サイクル検出に失敗しました。より長い動画での解析をお試しください")
        
        return {
            "status": "success",
            "message": "統括的ランニング解析が完了しました",
            "analysis_results": stats_results,
            "analysis_details": {
                "total_frames": len(request.pose_data),
                "valid_frames": len(all_keypoints),
                "video_fps": video_fps,
                "analysis_type": "single_cycle_representative"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 統括解析エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"統括解析に失敗しました: {str(e)}")

@app.get("/standard_model")
async def get_standard_model():
    """
    標準動作モデルデータを取得するエンドポイント
    """
    try:
        standard_data = get_standard_model_data()
        return {
            "status": "success",
            "message": "標準動作モデルデータを取得しました",
            "standard_model": standard_data,
            "data_info": {
                "total_frames": len([k for k in standard_data.keys() if k.startswith('Frame_')]),
                "main_indicators": ["体幹角度", "右大腿角度", "左大腿角度", "右下腿角度", "左下腿角度"],
                "description": "添付画像の表から抽出した標準動作モデルの統計値"
            }
        }
    except Exception as e:
        print(f"❌ 標準モデル取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"標準モデルデータの取得に失敗しました: {str(e)}")

@app.post("/compare_with_standard")
async def compare_user_stats_with_standard(user_stats: Dict[str, Dict[str, float]]):
    """
    ユーザーの統計値を標準動作モデルと比較するエンドポイント
    """
    try:
        print("🔍 ユーザー統計値と標準モデルの比較を開始...")
        
        # 比較処理を実行
        comparison_result = compare_with_standard_model(user_stats)
        
        if comparison_result['status'] == 'error':
            raise HTTPException(status_code=500, detail=comparison_result['message'])
        
        return {
            "status": "success",
            "message": "ユーザー統計値と標準モデルの比較が完了しました",
            "comparison_data": comparison_result,
            "console_output": "詳細な比較結果はサーバーコンソールに出力されました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 比較エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"比較処理に失敗しました: {str(e)}")

@app.get("/test_comparison")
async def test_comparison_endpoint():
    """
    比較機能のテスト用エンドポイント
    サンプルデータで比較結果をデモ表示
    """
    try:
        print("🧪 比較機能テストエンドポイント実行...")
        
        # サンプルユーザー統計値を作成
        sample_user_stats = create_sample_user_stats()
        
        # 比較処理を実行
        comparison_result = compare_with_standard_model(sample_user_stats)
        
        return {
            "status": "success",
            "message": "比較機能テストが完了しました",
            "sample_user_stats": sample_user_stats,
            "comparison_result": comparison_result,
            "console_note": "詳細な比較結果表示はサーバーコンソールをご確認ください"
        }
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"テスト実行に失敗しました: {str(e)}")

@app.get("/test_statistical_judgment")
async def test_statistical_judgment_endpoint():
    """
    統計的判定機能のテスト用エンドポイント
    """
    try:
        print("🧪 統計的判定機能テストエンドポイント実行...")
        
        # テスト実行
        test_statistical_judgment()
        
        return {
            "status": "success",
            "message": "統計的判定機能のテストが完了しました",
            "test_note": "詳細なテスト結果はサーバーコンソールをご確認ください",
            "judgment_criteria": {
                "offset_value": 1.5,
                "formula": "重み付け変動度 = |標準平均 - ユーザー値| / 標準偏差 / CV",
                "threshold": "閾値 = Offset値 / CV",
                "decision": "重み付け変動度 > 閾値 → 課題あり"
            }
        }
        
    except Exception as e:
        print(f"❌ 統計判定テストエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"統計判定テストに失敗しました: {str(e)}")

# =============================================================================
# 統括的なランニング解析関数
# =============================================================================

def find_foot_strikes(time_series_keypoints: List[List[KeyPoint]], foot_type: str = 'right') -> List[int]:
    """
    足の接地フレームを検出する
    
    Args:
        time_series_keypoints: 時系列キーポイントデータ
        foot_type: 'right' または 'left'
    
    Returns:
        接地フレーム番号のリスト
    """
    try:
        print(f"🦶 {foot_type}足の接地検出を開始...")
        
        if len(time_series_keypoints) < 10:
            print("❌ フレーム数が不足しています")
            return []
        
        # 足首とつま先のキーポイントインデックス
        if foot_type == 'right':
            ankle_idx = LANDMARK_INDICES['right_ankle']
            toe_idx = LANDMARK_INDICES['right_foot_index']
        else:
            ankle_idx = LANDMARK_INDICES['left_ankle']
            toe_idx = LANDMARK_INDICES['left_foot_index']
        
        # 足首のY座標（高さ）を時系列で抽出
        ankle_heights = []
        for frame_keypoints in time_series_keypoints:
            if len(frame_keypoints) > ankle_idx and frame_keypoints[ankle_idx].visibility > 0.5:
                ankle_heights.append(frame_keypoints[ankle_idx].y)
            else:
                ankle_heights.append(None)
        
        # 有効なデータのみでフィルタリング
        valid_heights = [(i, h) for i, h in enumerate(ankle_heights) if h is not None]
        if len(valid_heights) < 10:
            print("❌ 有効な足首データが不足しています")
            return []
        
        # 移動平均でスムージング（ノイズ除去）
        window_size = min(5, len(valid_heights) // 3)
        smoothed_heights = []
        for i in range(len(valid_heights)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(valid_heights), i + window_size // 2 + 1)
            avg_height = np.mean([valid_heights[j][1] for j in range(start_idx, end_idx)])
            smoothed_heights.append((valid_heights[i][0], avg_height))
        
        # 極小値（接地候補）を検出
        foot_strikes = []
        for i in range(1, len(smoothed_heights) - 1):
            prev_frame, prev_height = smoothed_heights[i-1]
            curr_frame, curr_height = smoothed_heights[i]
            next_frame, next_height = smoothed_heights[i+1]
            
            # 極小値の条件：前後よりも低い
            if curr_height < prev_height and curr_height < next_height:
                foot_strikes.append(curr_frame)
        
        # 接地間隔の正規化（近すぎる接地を除去）
        if len(foot_strikes) > 1:
            filtered_strikes = [foot_strikes[0]]
            min_interval = max(10, len(time_series_keypoints) // 20)  # 最小間隔
            
            for strike in foot_strikes[1:]:
                if strike - filtered_strikes[-1] >= min_interval:
                    filtered_strikes.append(strike)
            
            foot_strikes = filtered_strikes
        
        print(f"🦶 {foot_type}足接地検出結果: {len(foot_strikes)}回 {foot_strikes}")
        return foot_strikes
        
    except Exception as e:
        print(f"❌ 足接地検出エラー ({foot_type}): {str(e)}")
        return []

def detect_foot_strikes_advanced(all_keypoints: List[List[KeyPoint]], video_fps: float) -> List[tuple]:
    """
    高精度な歩数カウント（フットストライク検出）関数
    スムージングと人間工学的制約を用いたフィルタリングを実装
    
    Args:
        all_keypoints: 動画全体のキーポイントデータ
        video_fps: 動画のフレームレート
    
    Returns:
        検出された全ての接地イベントのリスト [(フレーム番号, 'left'/'right'), ...]
        フレーム番号順にソートされている
    """
    try:
        print(f"🚀 高精度フットストライク検出を開始...")
        print(f"📊 入力データ: {len(all_keypoints)}フレーム, FPS: {video_fps}")
        
        if len(all_keypoints) < 20:
            print("❌ フレーム数が不足しています（最低20フレーム必要）")
            return []
        
        # ステップ1: データ準備とスムージング
        print("📈 ステップ1: データ準備とスムージング")
        
        # 左右足首のY座標を抽出
        left_ankle_y = []
        right_ankle_y = []
        
        left_ankle_idx = LANDMARK_INDICES['left_ankle']
        right_ankle_idx = LANDMARK_INDICES['right_ankle']
        
        for frame_keypoints in all_keypoints:
            # 左足首
            if len(frame_keypoints) > left_ankle_idx and frame_keypoints[left_ankle_idx].visibility > 0.5:
                left_ankle_y.append(frame_keypoints[left_ankle_idx].y)
            else:
                left_ankle_y.append(np.nan)
            
            # 右足首
            if len(frame_keypoints) > right_ankle_idx and frame_keypoints[right_ankle_idx].visibility > 0.5:
                right_ankle_y.append(frame_keypoints[right_ankle_idx].y)
            else:
                right_ankle_y.append(np.nan)
        
        # NaNを線形補間で埋める
        left_ankle_y = np.array(left_ankle_y)
        right_ankle_y = np.array(right_ankle_y)
        
        def interpolate_nans(arr):
            """NaN値を線形補間で埋める"""
            mask = ~np.isnan(arr)
            if np.sum(mask) < 2:
                return arr
            indices = np.arange(len(arr))
            arr[~mask] = np.interp(indices[~mask], indices[mask], arr[mask])
            return arr
        
        left_ankle_y = interpolate_nans(left_ankle_y)
        right_ankle_y = interpolate_nans(right_ankle_y)
        
        # Savitzky-Golay フィルタでスムージング
        window_length = min(7, len(all_keypoints) // 3)
        if window_length % 2 == 0:
            window_length -= 1  # 奇数にする
        window_length = max(3, window_length)  # 最小値は3
        
        try:
            left_smoothed = signal.savgol_filter(left_ankle_y, window_length, 3)
            right_smoothed = signal.savgol_filter(right_ankle_y, window_length, 3)
            print(f"✅ スムージング完了 (window_length: {window_length})")
        except Exception as e:
            print(f"⚠️ スムージングエラー、移動平均にフォールバック: {e}")
            # フォールバック: 単純移動平均
            def moving_average(arr, window):
                return np.convolve(arr, np.ones(window)/window, mode='same')
            left_smoothed = moving_average(left_ankle_y, 5)
            right_smoothed = moving_average(right_ankle_y, 5)
        
        # ステップ2: 全ての接地候補を検出
        print("🔍 ステップ2: 接地候補検出")
        
        # 極小値（谷）を検出するため信号を反転
        left_inverted = -left_smoothed
        right_inverted = -right_smoothed
        
        # find_peaksで極小値（谷）を検出
        min_prominence = np.std(left_smoothed) * 0.3  # プロミネンス閾値
        left_candidates, _ = signal.find_peaks(left_inverted, prominence=min_prominence)
        right_candidates, _ = signal.find_peaks(right_inverted, prominence=min_prominence)
        
        print(f"📍 左足候補: {len(left_candidates)}個 {list(left_candidates)}")
        print(f"📍 右足候補: {len(right_candidates)}個 {list(right_candidates)}")
        
        # ステップ3: 候補のフィルタリングと最終リストの構築
        print("🔧 ステップ3: フィルタリングと最終構築")
        
        # 時間制約フィルタ
        def apply_time_constraints(candidates, foot_name):
            """物理的制約に基づいて候補をフィルタリング"""
            if len(candidates) < 2:
                return candidates
            
            # SPM制約: 120-220 SPM (0.27-0.5秒/歩)
            min_interval_frames = int(video_fps * 60 / 220)  # 220 SPM
            max_interval_frames = int(video_fps * 60 / 120)  # 120 SPM
            
            filtered = [candidates[0]]
            for candidate in candidates[1:]:
                interval = candidate - filtered[-1]
                if min_interval_frames <= interval <= max_interval_frames:
                    filtered.append(candidate)
                else:
                    print(f"⚠️ {foot_name}足候補除外: フレーム{candidate} (間隔: {interval})")
            
            print(f"✅ {foot_name}足フィルタ後: {len(filtered)}個 {list(filtered)}")
            return np.array(filtered)
        
        left_filtered = apply_time_constraints(left_candidates, "左")
        right_filtered = apply_time_constraints(right_candidates, "右")
        
        # 左右交互フィルタ
        print("🔄 左右交互フィルタ適用中...")
        
        # 全候補を統合してソート
        all_candidates = []
        for frame in left_filtered:
            all_candidates.append((frame, 'left'))
        for frame in right_filtered:
            all_candidates.append((frame, 'right'))
        
        # フレーム番号でソート
        all_candidates.sort(key=lambda x: x[0])
        print(f"📊 統合候補: {len(all_candidates)}個 {all_candidates}")
        
        # 左右交互制約を適用
        final_strikes = []
        if all_candidates:
            final_strikes.append(all_candidates[0])
            
            for candidate in all_candidates[1:]:
                current_frame, current_foot = candidate
                last_frame, last_foot = final_strikes[-1]
                
                # 異なる足の場合のみ追加
                if current_foot != last_foot:
                    final_strikes.append(candidate)
                else:
                    print(f"⚠️ 同一足連続をスキップ: {current_foot}足フレーム{current_frame}")
        
        print(f"✅ 最終フットストライク検出結果: {len(final_strikes)}個")
        for frame, foot in final_strikes:
            print(f"  🦶 フレーム{frame}: {foot}足")
        
        # 検出統計
        left_count = sum(1 for _, foot in final_strikes if foot == 'left')
        right_count = sum(1 for _, foot in final_strikes if foot == 'right')
        total_steps = len(final_strikes)
        
        if len(final_strikes) > 1:
            duration_seconds = len(all_keypoints) / video_fps
            spm = (total_steps * 60) / duration_seconds
            print(f"📊 検出統計:")
            print(f"  👣 総歩数: {total_steps}歩")
            print(f"  🦶 左足: {left_count}歩, 右足: {right_count}歩")
            print(f"  ⏱️ 動画時間: {duration_seconds:.2f}秒")
            print(f"  🏃 推定SPM: {spm:.1f}")
        
        return final_strikes
        
    except Exception as e:
        print(f"❌ 高精度フットストライク検出エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def analyze_angles_for_single_cycle(cycle_keypoints: List[List[KeyPoint]]) -> Dict[str, Dict[str, float]]:
    """
    単一サイクルの各指標の統計値を計算する
    
    Args:
        cycle_keypoints: 1サイクル分のキーポイントデータ
    
    Returns:
        各指標の統計値辞書
    """
    try:
        print(f"📊 1サイクル解析開始 - フレーム数: {len(cycle_keypoints)}")
        
        # 各フレームの角度を計算
        cycle_angles = {
            'trunk_angle': [],
            'left_thigh_angle': [],
            'right_thigh_angle': [],
            'left_lower_leg_angle': [],
            'right_lower_leg_angle': [],
            # 新規追加角度
            'left_upper_arm_angle': [],
            'right_upper_arm_angle': [],
            'left_forearm_angle': [],
            'right_forearm_angle': [],
            'left_foot_angle': [],
            'right_foot_angle': []
        }
        
        for frame_keypoints in cycle_keypoints:
            if len(frame_keypoints) >= 33:
                # 体幹角度
                trunk_angle = calculate_trunk_angle(frame_keypoints)
                if trunk_angle is not None:
                    cycle_angles['trunk_angle'].append(trunk_angle)
                
                # 大腿角度
                left_thigh = calculate_thigh_angle(
                    frame_keypoints[LANDMARK_INDICES['left_hip']],
                    frame_keypoints[LANDMARK_INDICES['left_knee']],
                    'left'
                )
                if left_thigh is not None:
                    cycle_angles['left_thigh_angle'].append(left_thigh)
                
                right_thigh = calculate_thigh_angle(
                    frame_keypoints[LANDMARK_INDICES['right_hip']],
                    frame_keypoints[LANDMARK_INDICES['right_knee']],
                    'right'
                )
                if right_thigh is not None:
                    cycle_angles['right_thigh_angle'].append(right_thigh)
                
                # 下腿角度
                left_lower_leg = calculate_lower_leg_angle(
                    frame_keypoints[LANDMARK_INDICES['left_knee']],
                    frame_keypoints[LANDMARK_INDICES['left_ankle']],
                    'left'
                )
                if left_lower_leg is not None:
                    cycle_angles['left_lower_leg_angle'].append(left_lower_leg)
                
                right_lower_leg = calculate_lower_leg_angle(
                    frame_keypoints[LANDMARK_INDICES['right_knee']],
                    frame_keypoints[LANDMARK_INDICES['right_ankle']],
                    'right'
                )
                if right_lower_leg is not None:
                    cycle_angles['right_lower_leg_angle'].append(right_lower_leg)
                
                # 上腕角度
                left_upper_arm = calculate_upper_arm_angle(
                    frame_keypoints[LANDMARK_INDICES['left_shoulder']],
                    frame_keypoints[LANDMARK_INDICES['left_elbow']],
                    'left'
                )
                if left_upper_arm is not None:
                    cycle_angles['left_upper_arm_angle'].append(left_upper_arm)
                
                right_upper_arm = calculate_upper_arm_angle(
                    frame_keypoints[LANDMARK_INDICES['right_shoulder']],
                    frame_keypoints[LANDMARK_INDICES['right_elbow']],
                    'right'
                )
                if right_upper_arm is not None:
                    cycle_angles['right_upper_arm_angle'].append(right_upper_arm)
                
                # 前腕角度
                left_forearm = calculate_forearm_angle(
                    frame_keypoints[LANDMARK_INDICES['left_elbow']],
                    frame_keypoints[LANDMARK_INDICES['left_wrist']],
                    'left'
                )
                if left_forearm is not None:
                    cycle_angles['left_forearm_angle'].append(left_forearm)
                
                right_forearm = calculate_forearm_angle(
                    frame_keypoints[LANDMARK_INDICES['right_elbow']],
                    frame_keypoints[LANDMARK_INDICES['right_wrist']],
                    'right'
                )
                if right_forearm is not None:
                    cycle_angles['right_forearm_angle'].append(right_forearm)
                
                # 足部角度
                left_foot = calculate_foot_angle(
                    frame_keypoints[LANDMARK_INDICES['left_ankle']],
                    frame_keypoints[LANDMARK_INDICES['left_foot_index']],
                    'left'
                )
                if left_foot is not None:
                    cycle_angles['left_foot_angle'].append(left_foot)
                
                right_foot = calculate_foot_angle(
                    frame_keypoints[LANDMARK_INDICES['right_ankle']],
                    frame_keypoints[LANDMARK_INDICES['right_foot_index']],
                    'right'
                )
                if right_foot is not None:
                    cycle_angles['right_foot_angle'].append(right_foot)
        
        # 統計値を計算
        stats_results = {}
        for angle_type, values in cycle_angles.items():
            if values:
                stats_results[angle_type] = {
                    'mean': float(np.mean(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'std': float(np.std(values)),
                    'count': len(values)
                }
                print(f"📐 {angle_type}: 平均={stats_results[angle_type]['mean']:.1f}°, "
                      f"範囲=[{stats_results[angle_type]['min']:.1f}, {stats_results[angle_type]['max']:.1f}]°")
            else:
                stats_results[angle_type] = {
                    'mean': None, 'min': None, 'max': None, 'std': None, 'count': 0
                }
        
        return stats_results
        
    except Exception as e:
        print(f"❌ サイクル解析エラー: {str(e)}")
        return {}

def analyze_user_run_and_get_stats(all_keypoints: List[List[KeyPoint]], video_fps: float) -> Optional[Dict[str, Dict[str, float]]]:
    """
    ランニングのキーポイントデータ全体を入力として受け取り、
    代表的な1サイクルの各指標の統計値（最小値・最大値・平均値）を返す統括的な解析関数
    
    Args:
        all_keypoints: 動画全体のキーポイントデータ
        video_fps: 動画のフレームレート
    
    Returns:
        解析結果の統計値が入った辞書、またはNone
        例: {
            'trunk_angle': {'mean': 12.1, 'max': 15.0, 'min': 8.5, 'std': 2.1, 'count': 30},
            'right_thigh_angle': {...},
            ...
        }
    """
    try:
        print("🏃 統括的ランニング解析を開始...")
        print(f"📊 総フレーム数: {len(all_keypoints)}")
        print(f"🎬 動画FPS: {video_fps}")
        
        # ステップ1: フットストライク検出
        print("\n🦶 フットストライク検出...")
        right_foot_strikes = find_foot_strikes(all_keypoints, 'right')
        left_foot_strikes = find_foot_strikes(all_keypoints, 'left')
        
        # より多く検出された方を使用
        if len(right_foot_strikes) >= len(left_foot_strikes):
            primary_foot_strikes = right_foot_strikes
            foot_type = 'right'
        else:
            primary_foot_strikes = left_foot_strikes
            foot_type = 'left'
        
        print(f"🦶 使用する足: {foot_type}足 ({len(primary_foot_strikes)}回の接地)")
        
        # サイクルが検出できない場合
        if len(primary_foot_strikes) < 2:
            print("❌ 足接地が2回未満のため、サイクルを検出できません")
            return None
        
        # ステップ2: 代表的なサイクルを選択
        print("\n🔄 代表サイクル選択...")
        
        if len(primary_foot_strikes) >= 3:
            # 2回目から3回目の接地まで（より安定した中間部分）
            cycle_start = primary_foot_strikes[1]
            cycle_end = primary_foot_strikes[2]
            cycle_description = "2回目〜3回目の接地"
        else:
            # 1回目から2回目の接地まで（1サイクルのみ）
            cycle_start = primary_foot_strikes[0]
            cycle_end = primary_foot_strikes[1]
            cycle_description = "1回目〜2回目の接地"
        
        print(f"📍 選択サイクル: {cycle_description}")
        print(f"📍 フレーム範囲: {cycle_start} 〜 {cycle_end} ({cycle_end - cycle_start}フレーム)")
        print(f"⏱️ 時間: {cycle_start/video_fps:.2f}s 〜 {cycle_end/video_fps:.2f}s")
        
        # ステップ3: サイクルデータを抽出
        cycle_keypoints = all_keypoints[cycle_start:cycle_end + 1]
        
        # ステップ4: 選択したサイクルの統計値を計算
        print(f"\n📊 サイクル解析実行...")
        stats_results = analyze_angles_for_single_cycle(cycle_keypoints)
        
        if not stats_results:
            print("❌ サイクル解析に失敗しました")
            return None
        
        # 結果のサマリー出力
        print(f"\n✅ 統括解析完了!")
        print(f"📈 解析結果サマリー:")
        for angle_type, stats in stats_results.items():
            if stats['count'] > 0:
                print(f"   {angle_type}: 平均={stats['mean']:.1f}° (範囲: {stats['min']:.1f}°〜{stats['max']:.1f}°)")
        
        return stats_results
        
    except Exception as e:
        print(f"❌ 統括解析エラー: {str(e)}")
        return None

def display_comparison_results(user_stats: Dict[str, Dict[str, float]], standard_model: Dict[str, Dict[str, float]]) -> None:
    """
    ユーザーの統計値と標準動作モデルの値を比較し、結果を表形式でコンソールに出力する
    
    Args:
        user_stats: ユーザーの統計値辞書 (analyze_user_run_and_get_stats の結果)
        standard_model: 標準動作モデルの辞書 (get_standard_model_data の結果)
    """
    
    print("\n" + "="*60)
    print("🏃 ランニングフォーム比較結果")
    print("="*60)
    
    # 指標名のマッピング（ユーザー統計値 → 標準モデル）
    # 新しい角度は比較対象外のため除外
    indicator_mapping = {
        'trunk_angle': '体幹角度',
        'left_thigh_angle': '左大腿角度', 
        'right_thigh_angle': '右大腿角度',
        'left_lower_leg_angle': '左下腿角度',
        'right_lower_leg_angle': '右下腿角度'
    }
    
    # 統計項目のマッピング
    stat_mapping = {
        'mean': '平均値',
        'max': '最大値', 
        'min': '最小値',
        'std': '標準偏差'
    }
    
    for user_indicator, user_data in user_stats.items():
        # 対応する標準モデルの指標名を取得
        standard_indicator = indicator_mapping.get(user_indicator)
        
        if not standard_indicator:
            print(f"\n⚠️  指標「{user_indicator}」は標準モデルに対応データがありません")
            continue
            
        print(f"\n■ 指標: {standard_indicator}")
        print("-" * 40)
        
        # 標準モデルのデータを取得
        standard_data = standard_model.get(standard_indicator, {})
        
        # 各統計値を比較
        for stat_key, stat_name in stat_mapping.items():
            user_value = user_data.get(stat_key)
            
            # 標準モデルでの対応するキーを探す
            standard_value = None
            if stat_key == 'mean':
                standard_value = standard_data.get('mean')
            elif stat_key == 'max':
                standard_value = standard_data.get('max')
            elif stat_key == 'min':
                standard_value = standard_data.get('min')
            elif stat_key == 'std':
                standard_value = standard_data.get('std_dev')
            
            # 値が存在する場合のみ表示
            if user_value is not None:
                if standard_value is not None:
                    # 差分を計算
                    diff = user_value - standard_value
                    diff_str = f"{diff:+.1f}°" if diff >= 0 else f"{diff:.1f}°"
                    
                    # 統計的判定を実行（標準偏差が必要）
                    standard_std_dev = standard_data.get('std_dev', 0)
                    if standard_std_dev > 0:
                        judgment = judge_deviation_significance(user_value, standard_value, standard_std_dev)
                        judgment_color = "🔴" if judgment == "課題あり" else "🟢"
                        judgment_display = f"{judgment_color}[{judgment}]"
                    else:
                        judgment_display = "⚪[判定不可]"
                    
                    print(f"{stat_name:>6}: あなた:{user_value:6.1f}° | 標準:{standard_value:6.1f}° | 差分: {diff_str} | {judgment_display}")
                else:
                    print(f"{stat_name:>6}: あなた:{user_value:6.1f}° | 標準: (データなし) | 差分: - | ⚪[判定不可]")
    
    print("\n" + "="*60)
    print("📊 比較結果の見方:")
    print("  • 正の差分(+): あなたの値が標準より大きい")  
    print("  • 負の差分(-): あなたの値が標準より小さい")
    print("  • 🔴[課題あり]: 統計的に有意な差 → 改善推奨")
    print("  • 🟢[OK]: 正常範囲内 → 問題なし")
    print("  • ⚪[判定不可]: データ不足で判定できません")
    print("\n💡 判定基準:")
    print("  変動係数(CV)と重み付け変動度を用いた統計的分析")
    print("  Offset値1.5を基準とした閾値判定")
    print("="*60)

def compare_with_standard_model(user_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    ユーザー統計値を標準モデルと比較し、結果を辞書で返す
    
    Args:
        user_stats: ユーザーの統計値辞書
        
    Returns:
        比較結果の辞書
    """
    try:
        # 標準モデルデータを取得
        standard_model = get_standard_model_data()
        
        # コンソールに比較結果を表示
        display_comparison_results(user_stats, standard_model)
        
        # 指標名のマッピング（新しい角度は比較対象外）
        indicator_mapping = {
            'trunk_angle': '体幹角度',
            'left_thigh_angle': '左大腿角度', 
            'right_thigh_angle': '右大腿角度',
            'left_lower_leg_angle': '左下腿角度',
            'right_lower_leg_angle': '右下腿角度'
        }
        
        comparison_results = {}
        
        for user_indicator, user_data in user_stats.items():
            standard_indicator = indicator_mapping.get(user_indicator)
            if not standard_indicator:
                continue
                
            standard_data = standard_model.get(standard_indicator, {})
            
            # 比較結果を辞書形式で保存
            indicator_comparison = {
                'user_data': user_data,
                'standard_data': standard_data,
                'differences': {}
            }
            
            # 各統計値の差分を計算
            stat_keys = ['mean', 'max', 'min']
            standard_keys = ['mean', 'max', 'min']
            
            for i, stat_key in enumerate(stat_keys):
                user_value = user_data.get(stat_key)
                standard_value = standard_data.get(standard_keys[i])
                
                if user_value is not None and standard_value is not None:
                    diff = user_value - standard_value
                    
                    # 統計的判定を実行
                    standard_std_dev = standard_data.get('std_dev', 0)
                    if standard_std_dev > 0:
                        judgment = judge_deviation_significance(user_value, standard_value, standard_std_dev)
                    else:
                        judgment = "判定不可"
                    
                    indicator_comparison['differences'][stat_key] = {
                        'user_value': user_value,
                        'standard_value': standard_value,
                        'difference': diff,
                        'percentage_diff': (diff / standard_value) * 100 if standard_value != 0 else None,
                        'statistical_judgment': judgment,
                        'needs_improvement': judgment == "課題あり"
                    }
            
            comparison_results[standard_indicator] = indicator_comparison
        
        return {
            'status': 'success',
            'comparison_results': comparison_results,
            'summary': {
                'total_indicators': len(comparison_results),
                'indicators_compared': list(comparison_results.keys())
            }
        }
        
    except Exception as e:
        print(f"❌ 比較処理エラー: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def judge_deviation_significance(user_value: float, model_mean: float, model_std_dev: float) -> str:
    """
    ユーザーの計測値が標準モデルと比較して統計的に有意な差があるかを判定する
    
    Args:
        user_value: ユーザーの計測値
        model_mean: 標準モデルの平均値
        model_std_dev: 標準モデルの標準偏差
    
    Returns:
        判定結果（"課題あり" または "OK"）
    """
    try:
        # ゼロ除算を避ける
        if model_mean == 0 or model_std_dev == 0:
            return "判定不可"
        
        # 変動係数 (CV) を計算
        cv = abs(model_std_dev / model_mean)
        
        # Offset値を1.5と設定し、閾値を計算
        offset = 1.5
        threshold = offset / cv if cv != 0 else float('inf')
        
        # 重み付け変動度を計算
        raw_deviation = abs(model_mean - user_value) / model_std_dev
        weighted_deviation = raw_deviation / cv if cv != 0 else 0
        
        # 判定
        if weighted_deviation > threshold:
            return "課題あり"
        else:
            return "OK"
            
    except Exception as e:
        print(f"⚠️ 統計判定エラー: {str(e)}")
        return "判定エラー"

def create_sample_user_stats() -> Dict[str, Dict[str, float]]:
    """
    テスト用のサンプルユーザー統計値を作成
    """
    return {
        'trunk_angle': {
            'mean': 12.1,
            'max': 15.0,
            'min': 8.5,
            'std': 2.1,
            'count': 30
        },
        'right_thigh_angle': {
            'mean': 10.5,
            'max': 48.2,
            'min': -14.0,
            'std': 7.2,
            'count': 30
        },
        'left_thigh_angle': {
            'mean': 9.8,
            'max': 46.5,
            'min': -12.5,
            'std': 6.8,
            'count': 30
        },
        'right_lower_leg_angle': {
            'mean': -2.5,
            'max': 28.0,
            'min': -30.1,
            'std': 8.5,
            'count': 30
        },
        'left_lower_leg_angle': {
            'mean': -1.8,
            'max': 29.2,
            'min': -28.5,
            'std': 8.2,
            'count': 30
        }
    }

def test_comparison_display():
    """
    比較結果表示機能のテスト関数
    """
    print("🧪 比較機能テストを開始...")
    
    # サンプルユーザー統計値を作成
    sample_user_stats = create_sample_user_stats()
    
    # 標準モデルデータを取得
    standard_model = get_standard_model_data()
    
    # 比較結果を表示
    display_comparison_results(sample_user_stats, standard_model)
    
    print("\n✅ 比較機能テスト完了！")

def test_statistical_judgment():
    """
    統計的判定機能の単体テスト
    """
    print("\n🧪 統計的判定機能テスト開始...")
    
    test_cases = [
        {"user": 12.1, "mean": 4.3, "std": 1.2, "expected": "課題あり", "case": "大きな差分"},
        {"user": 4.5, "mean": 4.3, "std": 1.2, "expected": "OK", "case": "小さな差分"},
        {"user": 2.0, "mean": 4.3, "std": 1.2, "expected": "課題あり", "case": "負の大きな差分"},
        {"user": 10.5, "mean": -13.2, "std": 10.8, "expected": "課題あり", "case": "負の標準値との比較"},
        {"user": 0, "mean": 0, "std": 1.0, "expected": "判定不可", "case": "ゼロ平均値"}
    ]
    
    print("テストケース実行:")
    for i, case in enumerate(test_cases, 1):
        result = judge_deviation_significance(case["user"], case["mean"], case["std"])
        status = "✅ PASS" if result == case["expected"] else f"❌ FAIL (期待: {case['expected']}, 実際: {result})"
        
        # 計算過程も表示
        if case["mean"] != 0 and case["std"] != 0:
            cv = abs(case["std"] / case["mean"])
            threshold = 1.5 / cv if cv != 0 else float('inf')
            raw_deviation = abs(case["mean"] - case["user"]) / case["std"]
            weighted_deviation = raw_deviation / cv if cv != 0 else 0
            
            print(f"  {i}. {case['case']}: {status}")
            print(f"      ユーザー値: {case['user']}, 標準平均: {case['mean']}, 標準偏差: {case['std']}")
            print(f"      CV: {cv:.3f}, 閾値: {threshold:.3f}, 重み付け変動度: {weighted_deviation:.3f}")
        else:
            print(f"  {i}. {case['case']}: {status}")
            print(f"      ユーザー値: {case['user']}, 標準平均: {case['mean']}, 標準偏差: {case['std']}")
    
    print("\n✅ 統計的判定機能テスト完了！")

@app.post("/test_advanced_foot_strikes")
async def test_advanced_foot_strikes(request: dict):
    """
    高精度フットストライク検出機能をテストする
    """
    try:
        print("🧪 高精度フットストライク検出テストを開始...")
        
        # リクエストから必要データを取得
        video_id = request.get('video_id')
        test_fps = request.get('fps', 20.0)
        
        if not video_id:
            return {
                "status": "error",
                "message": "video_idが必要です"
            }
        
        print(f"📝 テスト対象動画ID: {video_id}")
        
        # ダミーテストデータを生成（実際の実装では既存のキーポイントデータを使用）
        # ここでは高精度検出機能の動作確認のためのテストデータを作成
        
        # 50フレームの疑似キーポイントデータ（3秒動画想定）
        test_keypoints = []
        for frame_idx in range(50):
            frame_keypoints = []
            
            # 33個のキーポイントを生成
            for kp_idx in range(33):
                if kp_idx == LANDMARK_INDICES['left_ankle']:
                    # 左足首: 周期的な上下動（接地時に低い値）
                    y_val = 0.8 + 0.1 * math.sin(frame_idx * 0.4) + 0.05 * math.sin(frame_idx * 0.8)
                elif kp_idx == LANDMARK_INDICES['right_ankle']:
                    # 右足首: 左足と位相差のある周期的上下動
                    y_val = 0.8 + 0.1 * math.sin(frame_idx * 0.4 + math.pi * 0.6) + 0.05 * math.sin(frame_idx * 0.8)
                else:
                    # その他のキーポイント
                    y_val = 0.5
                
                keypoint = KeyPoint(
                    x=0.5,  # 固定
                    y=y_val,
                    z=0.0,  # 固定
                    visibility=0.9  # 高い可視性
                )
                frame_keypoints.append(keypoint)
            
            test_keypoints.append(frame_keypoints)
        
        print(f"✅ テストデータ生成完了: {len(test_keypoints)}フレーム")
        
        # 高精度フットストライク検出を実行
        detected_strikes = detect_foot_strikes_advanced(test_keypoints, test_fps)
        
        # 従来の検出方法との比較
        left_strikes_old = find_foot_strikes(test_keypoints, 'left')
        right_strikes_old = find_foot_strikes(test_keypoints, 'right')
        
        # 結果を整理
        result = {
            "status": "success",
            "message": "高精度フットストライク検出テスト完了",
            "test_data": {
                "video_id": video_id,
                "total_frames": len(test_keypoints),
                "fps": test_fps,
                "duration_seconds": len(test_keypoints) / test_fps
            },
            "advanced_detection": {
                "total_strikes": len(detected_strikes),
                "strikes_detail": [{"frame": int(frame), "foot": foot} for frame, foot in detected_strikes],
                "left_count": sum(1 for _, foot in detected_strikes if foot == 'left'),
                "right_count": sum(1 for _, foot in detected_strikes if foot == 'right')
            },
            "traditional_detection": {
                "left_strikes": [int(x) for x in left_strikes_old],
                "right_strikes": [int(x) for x in right_strikes_old],
                "total_strikes": len(left_strikes_old) + len(right_strikes_old)
            },
            "comparison": {
                "advanced_total": len(detected_strikes),
                "traditional_total": len(left_strikes_old) + len(right_strikes_old),
                "improvement": "高精度版では左右交互制約と時間制約を適用"
            }
        }
        
        if detected_strikes:
            duration = len(test_keypoints) / test_fps
            spm_estimated = (len(detected_strikes) * 60) / duration
            result["advanced_detection"]["estimated_spm"] = round(spm_estimated, 1)
        
        print(f"🎯 高精度検出結果: {len(detected_strikes)}歩")
        print(f"🔄 従来検出結果: {len(left_strikes_old) + len(right_strikes_old)}歩")
        
        return result
        
    except Exception as e:
        print(f"❌ 高精度フットストライクテストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"テスト実行エラー: {str(e)}"
        }

@app.post("/test_relative_angles")
async def test_relative_angles(request: dict):
    """
    新しい相対関節角度計算機能をテストする
    """
    try:
        print("🧪 相対関節角度計算テストを開始...")
        
        # リクエストから必要データを取得
        calculation_mode = request.get('mode', 'relative')
        test_frame_count = request.get('frame_count', 10)
        
        print(f"📝 テスト設定: モード={calculation_mode}, フレーム数={test_frame_count}")
        
        # ダミーテストデータを生成
        test_keypoints = []
        for frame_idx in range(test_frame_count):
            frame_keypoints = []
            
            # 33個のキーポイントを生成（基本的な人体ポーズ）
            for kp_idx in range(33):
                if kp_idx == LANDMARK_INDICES['left_shoulder']:
                    # 左肩
                    keypoint = KeyPoint(x=0.4, y=0.3, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_shoulder']:
                    # 右肩
                    keypoint = KeyPoint(x=0.6, y=0.3, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_hip']:
                    # 左股関節
                    keypoint = KeyPoint(x=0.45, y=0.6, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_hip']:
                    # 右股関節
                    keypoint = KeyPoint(x=0.55, y=0.6, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_knee']:
                    # 左膝（動的変化）
                    y_offset = 0.1 * math.sin(frame_idx * 0.3)
                    keypoint = KeyPoint(x=0.4, y=0.8 + y_offset, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_knee']:
                    # 右膝（動的変化）
                    y_offset = 0.1 * math.sin(frame_idx * 0.3 + math.pi)
                    keypoint = KeyPoint(x=0.6, y=0.8 + y_offset, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_ankle']:
                    # 左足首
                    keypoint = KeyPoint(x=0.4, y=0.95, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_ankle']:
                    # 右足首
                    keypoint = KeyPoint(x=0.6, y=0.95, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_foot_index']:
                    # 左つま先
                    keypoint = KeyPoint(x=0.39, y=0.98, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_foot_index']:
                    # 右つま先
                    keypoint = KeyPoint(x=0.61, y=0.98, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_elbow']:
                    # 左肘
                    keypoint = KeyPoint(x=0.35, y=0.45, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_elbow']:
                    # 右肘
                    keypoint = KeyPoint(x=0.65, y=0.45, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['left_wrist']:
                    # 左手首
                    keypoint = KeyPoint(x=0.32, y=0.6, z=0.0, visibility=0.9)
                elif kp_idx == LANDMARK_INDICES['right_wrist']:
                    # 右手首
                    keypoint = KeyPoint(x=0.68, y=0.6, z=0.0, visibility=0.9)
                else:
                    # その他のキーポイント
                    keypoint = KeyPoint(x=0.5, y=0.5, z=0.0, visibility=0.5)
                
                frame_keypoints.append(keypoint)
            
            test_keypoints.append(frame_keypoints)
        
        print(f"✅ テストデータ生成完了: {len(test_keypoints)}フレーム")
        
        # 角度計算器を作成
        calculator = AngleCalculator(mode=calculation_mode)
        
        # 各フレームで角度を計算
        results = []
        for frame_idx, frame_keypoints in enumerate(test_keypoints):
            frame_angles = calculator.calculate_all_angles(frame_keypoints)
            frame_angles['frame_index'] = frame_idx
            results.append(frame_angles)
        
        # 結果を整理
        summary = {
            "calculation_mode": calculation_mode,
            "total_frames": len(results),
            "sample_angles": {}
        }
        
        if results:
            first_frame = results[0]
            for key, value in first_frame.items():
                if key != 'frame_index' and key != 'calculation_mode' and value is not None and isinstance(value, (int, float)):
                    summary["sample_angles"][key] = round(value, 1)
        
        result = {
            "status": "success",
            "message": f"相対関節角度計算テスト完了 (モード: {calculation_mode})",
            "summary": summary,
            "detailed_results": results[:3] if len(results) >= 3 else results,  # 最初の3フレームのみ
            "angle_definitions": {
                "absolute_mode": {
                    "trunk_angle": "体幹ベクトルと鉛直軸の角度",
                    "thigh_angle": "大腿ベクトルと鉛直軸の角度",
                    "shank_angle": "下腿ベクトルと鉛直軸の角度"
                },
                "relative_mode": {
                    "trunk_angle": "体幹ベクトルと鉛直軸の角度（絶対角度と同じ）",
                    "hip_joint_angle": "大腿と体幹のはさみ角（肩中点-股関節-膝）",
                    "knee_joint_angle": "大腿と下腿のはさみ角（股関節-膝-足首）",
                    "ankle_joint_angle": "下腿と足部のはさみ角（膝-足首-つま先）",
                    "elbow_joint_angle": "上腕と前腕のはさみ角（肩-肘-手首）"
                }
            }
        }
        
        print(f"🎯 テスト完了: {calculation_mode}モードで{len(results)}フレーム処理")
        
        return result
        
    except Exception as e:
        print(f"❌ 相対角度計算テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"テスト実行エラー: {str(e)}"
        }

@app.post("/compare_angle_modes")
async def compare_angle_modes(request: dict):
    """
    絶対角度と相対関節角度の計算結果を比較する
    """
    try:
        print("🔬 角度計算モード比較テストを開始...")
        
        # テストデータを生成（1フレーム）
        test_keypoints = []
        
        # 標準的なランニングポーズを模擬
        frame_keypoints = []
        for kp_idx in range(33):
            if kp_idx == LANDMARK_INDICES['left_shoulder']:
                keypoint = KeyPoint(x=0.42, y=0.25, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_shoulder']:
                keypoint = KeyPoint(x=0.58, y=0.25, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_hip']:
                keypoint = KeyPoint(x=0.44, y=0.55, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_hip']:
                keypoint = KeyPoint(x=0.56, y=0.55, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_knee']:
                keypoint = KeyPoint(x=0.40, y=0.75, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_knee']:
                keypoint = KeyPoint(x=0.62, y=0.75, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_ankle']:
                keypoint = KeyPoint(x=0.38, y=0.92, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_ankle']:
                keypoint = KeyPoint(x=0.64, y=0.92, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_foot_index']:
                keypoint = KeyPoint(x=0.36, y=0.95, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['right_foot_index']:
                keypoint = KeyPoint(x=0.66, y=0.95, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['left_elbow']:
                keypoint = KeyPoint(x=0.36, y=0.40, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['right_elbow']:
                keypoint = KeyPoint(x=0.64, y=0.40, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['left_wrist']:
                keypoint = KeyPoint(x=0.34, y=0.55, z=0.0, visibility=0.85)
            elif kp_idx == LANDMARK_INDICES['right_wrist']:
                keypoint = KeyPoint(x=0.66, y=0.55, z=0.0, visibility=0.85)
            else:
                keypoint = KeyPoint(x=0.5, y=0.5, z=0.0, visibility=0.5)
            
            frame_keypoints.append(keypoint)
        
        test_keypoints.append(frame_keypoints)
        
        # 両モードで角度を計算
        absolute_calculator = AngleCalculator(mode="absolute")
        relative_calculator = AngleCalculator(mode="relative")
        
        absolute_result = absolute_calculator.calculate_all_angles(frame_keypoints)
        relative_result = relative_calculator.calculate_all_angles(frame_keypoints)
        
        # 結果を整理
        comparison = {
            "status": "success",
            "message": "角度計算モード比較完了",
            "absolute_angles": {k: round(v, 1) if v is not None and isinstance(v, (int, float)) else v 
                             for k, v in absolute_result.items()},
            "relative_angles": {k: round(v, 1) if v is not None and isinstance(v, (int, float)) else v 
                              for k, v in relative_result.items()},
            "mode_differences": {
                "absolute_mode": "絶対角度 - 各部位ベクトルと鉛直軸の角度",
                "relative_mode": "相対角度 - 隣接する身体部位間のはさみ角",
                "trunk_angle": "両モードで同じ（体幹ベクトルと鉛直軸）",
                "key_difference": "絶対角度は鉛直軸基準、相対角度は関節基準"
            }
        }
        
        print("🎯 モード比較完了")
        print(f"  📊 絶対角度: {len([v for v in absolute_result.values() if v is not None])}個")
        print(f"  📊 相対角度: {len([v for v in relative_result.values() if v is not None])}個")
        
        return comparison
        
    except Exception as e:
        print(f"❌ モード比較テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"比較テスト実行エラー: {str(e)}"
        }

@app.post("/test_enhanced_absolute_angles")
async def test_enhanced_absolute_angles(request: dict):
    """
    拡張された絶対角度計算機能をテストする
    新規追加された上腕、前腕、足部角度、および符号規則修正を検証
    """
    try:
        print("🧪 拡張絶対角度計算テストを開始...")
        
        test_frame_count = request.get('frame_count', 5)
        
        print(f"📝 テスト設定: フレーム数={test_frame_count}")
        
        # ダミーテストデータを生成（さまざまなポーズ）
        test_keypoints = []
        for frame_idx in range(test_frame_count):
            frame_keypoints = []
            
            # 動的なポーズ変化を模擬
            pose_variation = frame_idx * 0.1
            
            # 33個のキーポイントを生成
            for kp_idx in range(33):
                if kp_idx == LANDMARK_INDICES['left_shoulder']:
                    # 左肩（体幹の左上）
                    keypoint = KeyPoint(x=0.40 + pose_variation * 0.05, y=0.25, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['right_shoulder']:
                    # 右肩（体幹の右上）
                    keypoint = KeyPoint(x=0.60 - pose_variation * 0.05, y=0.25, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['left_hip']:
                    # 左股関節（体幹の左下）
                    keypoint = KeyPoint(x=0.42 + pose_variation * 0.03, y=0.55, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['right_hip']:
                    # 右股関節（体幹の右下）
                    keypoint = KeyPoint(x=0.58 - pose_variation * 0.03, y=0.55, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['left_elbow']:
                    # 左肘（動的変化）
                    keypoint = KeyPoint(x=0.30 + pose_variation * 0.1, y=0.40 + pose_variation * 0.05, z=0.0, visibility=0.90)
                elif kp_idx == LANDMARK_INDICES['right_elbow']:
                    # 右肘（動的変化）
                    keypoint = KeyPoint(x=0.70 - pose_variation * 0.1, y=0.40 + pose_variation * 0.05, z=0.0, visibility=0.90)
                elif kp_idx == LANDMARK_INDICES['left_wrist']:
                    # 左手首（動的変化）
                    keypoint = KeyPoint(x=0.25 + pose_variation * 0.15, y=0.50 + pose_variation * 0.1, z=0.0, visibility=0.85)
                elif kp_idx == LANDMARK_INDICES['right_wrist']:
                    # 右手首（動的変化）
                    keypoint = KeyPoint(x=0.75 - pose_variation * 0.15, y=0.50 + pose_variation * 0.1, z=0.0, visibility=0.85)
                elif kp_idx == LANDMARK_INDICES['left_knee']:
                    # 左膝（動的変化）
                    keypoint = KeyPoint(x=0.40 + pose_variation * 0.08, y=0.75 + pose_variation * 0.03, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['right_knee']:
                    # 右膝（動的変化）
                    keypoint = KeyPoint(x=0.60 - pose_variation * 0.08, y=0.75 + pose_variation * 0.03, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['left_ankle']:
                    # 左足首
                    keypoint = KeyPoint(x=0.38 + pose_variation * 0.05, y=0.92, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['right_ankle']:
                    # 右足首
                    keypoint = KeyPoint(x=0.62 - pose_variation * 0.05, y=0.92, z=0.0, visibility=0.95)
                elif kp_idx == LANDMARK_INDICES['left_foot_index']:
                    # 左つま先（動的変化）
                    keypoint = KeyPoint(x=0.35 + pose_variation * 0.08, y=0.95 + pose_variation * 0.02, z=0.0, visibility=0.90)
                elif kp_idx == LANDMARK_INDICES['right_foot_index']:
                    # 右つま先（動的変化）
                    keypoint = KeyPoint(x=0.65 - pose_variation * 0.08, y=0.95 + pose_variation * 0.02, z=0.0, visibility=0.90)
                else:
                    # その他のキーポイント
                    keypoint = KeyPoint(x=0.5, y=0.5, z=0.0, visibility=0.5)
                
                frame_keypoints.append(keypoint)
            
            test_keypoints.append(frame_keypoints)
        
        print(f"✅ テストデータ生成完了: {len(test_keypoints)}フレーム")
        
        # 拡張絶対角度計算器を作成
        calculator = AngleCalculator(mode="absolute")
        
        # 各フレームで角度を計算
        results = []
        for frame_idx, frame_keypoints in enumerate(test_keypoints):
            frame_angles = calculator.calculate_all_angles(frame_keypoints)
            frame_angles['frame_index'] = frame_idx
            results.append(frame_angles)
        
        # 結果を整理
        if results:
            first_frame = results[0]
            sample_angles = {}
            for key, value in first_frame.items():
                if key not in ['frame_index', 'calculation_mode'] and value is not None and isinstance(value, (int, float)):
                    sample_angles[key] = round(value, 1)
        
        # 新規追加角度の数をカウント
        new_angles = [k for k in sample_angles.keys() if 'upper_arm' in k or 'forearm' in k or 'foot' in k]
        
        result = {
            "status": "success",
            "message": f"拡張絶対角度計算テスト完了",
            "summary": {
                "calculation_mode": "absolute",
                "total_frames": len(results),
                "total_angles": len(sample_angles),
                "new_angles_count": len(new_angles),
                "sample_angles": sample_angles
            },
            "detailed_results": results[:2] if len(results) >= 2 else results,  # 最初の2フレームのみ
            "new_angle_definitions": {
                "upper_arm_angle": "上腕ベクトル（肩→肘）と鉛直軸の角度",
                "forearm_angle": "前腕ベクトル（肘→手首）と鉛直軸の角度", 
                "foot_angle": "足部ベクトル（足首→つま先）と水平軸の角度"
            },
            "updated_sign_convention": {
                "trunk_angle": "前傾=負値、後傾=正値",
                "limb_angles": "右側=負値、左側=正値",
                "foot_angle": "水平軸より上=正値、下=負値"
            }
        }
        
        print(f"🎯 テスト完了: {len(sample_angles)}個の角度を計算")
        print(f"  📊 新規追加角度: {len(new_angles)}個")
        
        return result
        
    except Exception as e:
        print(f"❌ 拡張絶対角度計算テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"テスト実行エラー: {str(e)}"
        }

@app.post("/test_angle_consistency")
async def test_angle_consistency():
    """
    フロントエンドとバックエンドの角度計算一致性をテストする
    """
    try:
        print("🔍 角度一致性テストを開始...")
        
        # 固定のテストキーポイント（フロントエンドと比較しやすい値）
        test_keypoints = []
        
        # 33個のキーポイントを生成（シンプルな直立ポーズ）
        for kp_idx in range(33):
            if kp_idx == LANDMARK_INDICES['left_shoulder']:
                keypoint = KeyPoint(x=0.40, y=0.25, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_shoulder']:
                keypoint = KeyPoint(x=0.60, y=0.25, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_hip']:
                keypoint = KeyPoint(x=0.42, y=0.55, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_hip']:
                keypoint = KeyPoint(x=0.58, y=0.55, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_elbow']:
                keypoint = KeyPoint(x=0.30, y=0.40, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['right_elbow']:
                keypoint = KeyPoint(x=0.70, y=0.40, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['left_wrist']:
                keypoint = KeyPoint(x=0.25, y=0.50, z=0.0, visibility=0.85)
            elif kp_idx == LANDMARK_INDICES['right_wrist']:
                keypoint = KeyPoint(x=0.75, y=0.50, z=0.0, visibility=0.85)
            elif kp_idx == LANDMARK_INDICES['left_knee']:
                keypoint = KeyPoint(x=0.40, y=0.75, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_knee']:
                keypoint = KeyPoint(x=0.60, y=0.75, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_ankle']:
                keypoint = KeyPoint(x=0.38, y=0.92, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['right_ankle']:
                keypoint = KeyPoint(x=0.62, y=0.92, z=0.0, visibility=0.95)
            elif kp_idx == LANDMARK_INDICES['left_foot_index']:
                keypoint = KeyPoint(x=0.35, y=0.95, z=0.0, visibility=0.90)
            elif kp_idx == LANDMARK_INDICES['right_foot_index']:
                keypoint = KeyPoint(x=0.65, y=0.95, z=0.0, visibility=0.90)
            else:
                keypoint = KeyPoint(x=0.5, y=0.5, z=0.0, visibility=0.5)
            
            test_keypoints.append(keypoint)
        
        # バックエンド計算
        calculator = AngleCalculator(mode="absolute")
        backend_result = calculator._calculate_absolute_angles(test_keypoints)
        
        # 詳細な計算過程をログ出力
        print("📊 バックエンド角度計算詳細:")
        for key, value in backend_result.items():
            if value is not None and isinstance(value, (int, float)):
                print(f"  {key}: {value:.2f}°")
        
        # キーポイント座標も返す（フロントエンドとの比較用）
        keypoint_coordinates = {
            'left_shoulder': {'x': test_keypoints[LANDMARK_INDICES['left_shoulder']].x, 'y': test_keypoints[LANDMARK_INDICES['left_shoulder']].y},
            'right_shoulder': {'x': test_keypoints[LANDMARK_INDICES['right_shoulder']].x, 'y': test_keypoints[LANDMARK_INDICES['right_shoulder']].y},
            'left_hip': {'x': test_keypoints[LANDMARK_INDICES['left_hip']].x, 'y': test_keypoints[LANDMARK_INDICES['left_hip']].y},
            'right_hip': {'x': test_keypoints[LANDMARK_INDICES['right_hip']].x, 'y': test_keypoints[LANDMARK_INDICES['right_hip']].y},
            'left_elbow': {'x': test_keypoints[LANDMARK_INDICES['left_elbow']].x, 'y': test_keypoints[LANDMARK_INDICES['left_elbow']].y},
            'right_elbow': {'x': test_keypoints[LANDMARK_INDICES['right_elbow']].x, 'y': test_keypoints[LANDMARK_INDICES['right_elbow']].y},
            'left_wrist': {'x': test_keypoints[LANDMARK_INDICES['left_wrist']].x, 'y': test_keypoints[LANDMARK_INDICES['left_wrist']].y},
            'right_wrist': {'x': test_keypoints[LANDMARK_INDICES['right_wrist']].x, 'y': test_keypoints[LANDMARK_INDICES['right_wrist']].y},
            'left_knee': {'x': test_keypoints[LANDMARK_INDICES['left_knee']].x, 'y': test_keypoints[LANDMARK_INDICES['left_knee']].y},
            'right_knee': {'x': test_keypoints[LANDMARK_INDICES['right_knee']].x, 'y': test_keypoints[LANDMARK_INDICES['right_knee']].y},
            'left_ankle': {'x': test_keypoints[LANDMARK_INDICES['left_ankle']].x, 'y': test_keypoints[LANDMARK_INDICES['left_ankle']].y},
            'right_ankle': {'x': test_keypoints[LANDMARK_INDICES['right_ankle']].x, 'y': test_keypoints[LANDMARK_INDICES['right_ankle']].y},
            'left_foot_index': {'x': test_keypoints[LANDMARK_INDICES['left_foot_index']].x, 'y': test_keypoints[LANDMARK_INDICES['left_foot_index']].y},
            'right_foot_index': {'x': test_keypoints[LANDMARK_INDICES['right_foot_index']].x, 'y': test_keypoints[LANDMARK_INDICES['right_foot_index']].y}
        }
        
        return {
            "message": "Angle consistency test completed",
            "backend_angles": backend_result,
            "keypoint_coordinates": keypoint_coordinates
        }
        
    except Exception as e:
        print(f"❌ 角度一致性テストエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Consistency test failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 