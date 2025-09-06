from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional
import math
import numpy as np

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

def calculate_trunk_angle(keypoints: List[KeyPoint]) -> Optional[float]:
    """
    体幹角度を計算する（正しい符号規則）
    定義: 腰から肩への直線ベクトルと鉛直軸がなす角度
    ・前傾で正値
    ・後傾で負値
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
        
        # 正しい符号規則: 前傾で正値、後傾で負値
        # forward_positive=True で前方（右）への傾きを正値にする
        angle = calculate_absolute_angle_with_vertical(trunk_vector, forward_positive=True)
        print(f"   計算された体幹角度: {angle:.1f}° (前傾で正値、後傾で負値)")
        
        return angle
        
    except Exception:
        return None

def calculate_thigh_angle(hip: KeyPoint, knee: KeyPoint, side: str) -> Optional[float]:
    """
    大腿角度を計算する（進行方向：左→右固定）
    定義: 大腿ベクトル（膝→股関節）と鉛直軸がなす角度
    ・正値：膝関節点が後方に位置（※参考　離地時）
    ・負値：膝関節点が前方に位置（※参考　接地時）
    """
    try:
        # キーポイントの有効性を確認
        if hip.visibility < 0.5 or knee.visibility < 0.5:
            return None
        
        # 大腿ベクトル（膝→股関節）
        thigh_vector = np.array([hip.x - knee.x, hip.y - knee.y])
        
        print(f"   🦵 {side}大腿ベクトル: [{thigh_vector[0]:.3f}, {thigh_vector[1]:.3f}] (膝→股関節)")
        
        # 絶対角度を計算（フロントエンドリアルタイム表示と一致）
        raw_angle = calculate_absolute_angle_with_vertical(thigh_vector, forward_positive=False)
        angle = -raw_angle  # フロントエンドと同じ符号反転
        
        print(f"   🦵 {side}大腿角度: {angle:.1f}° (膝が後方で正値)")
        
        return angle
        
    except Exception:
        return None

def calculate_lower_leg_angle(knee: KeyPoint, ankle: KeyPoint, side: str) -> Optional[float]:
    """
    下腿角度を計算する（進行方向：左→右固定）
    定義: 下腿ベクトル（足首→膝）と鉛直軸がなす角度
    ・正値：足関節点が後方に位置（※参考　離地時）
    ・負値：足関節点が前方に位置（※参考　接地時）
    """
    try:
        # キーポイントの有効性を確認
        if knee.visibility < 0.5 or ankle.visibility < 0.5:
            return None
        
        # 下腿ベクトル（足首→膝）
        lower_leg_vector = np.array([knee.x - ankle.x, knee.y - ankle.y])
        
        print(f"   🦵 {side}下腿ベクトル: [{lower_leg_vector[0]:.3f}, {lower_leg_vector[1]:.3f}] (足首→膝)")
        
        # 絶対角度を計算（フロントエンドリアルタイム表示と一致）
        raw_angle = calculate_absolute_angle_with_vertical(lower_leg_vector, forward_positive=False)
        angle = -raw_angle  # フロントエンドと同じ符号反転
        
        print(f"   🦵 {side}下腿角度: {angle:.1f}° (足首が後方で正値)")
        
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
                     'left_lower_leg_angle', 'right_lower_leg_angle']
        
        for angle_key in angle_keys:
            valid_values = [frame[angle_key] for frame in all_angles 
                           if frame[angle_key] is not None]
            angle_stats[angle_key] = calculate_angle_statistics(valid_values)
            
            # デバッグ出力: 体幹角度の統計情報
            if angle_key == 'trunk_angle':
                print(f"📊 体幹角度統計: {len(valid_values)}個の値から計算")
                print(f"   平均: {angle_stats[angle_key]['avg']:.1f}°")
                print(f"   範囲: {angle_stats[angle_key]['min']:.1f}° ～ {angle_stats[angle_key]['max']:.1f}°")
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 