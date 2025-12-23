"""
背後（トレッドミル）からの撮影動画を解析するサービス

3つの指標を計算:
1. Hip Drop（骨盤の沈み込み）
2. Vertical Oscillation（上下動）
3. Crossover（着地のクロスオーバー）
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import math
import uvicorn

app = FastAPI(
    title="Back View Analysis Service",
    description="背後からの撮影動画を解析するサービス",
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

# MediaPipe Pose Landmark インデックス
# https://google.github.io/mediapipe/solutions/pose.html
LANDMARK_INDICES = {
    "NOSE": 0,
    "LEFT_SHOULDER": 11,
    "RIGHT_SHOULDER": 12,
    "LEFT_HIP": 23,
    "RIGHT_HIP": 24,
    "LEFT_KNEE": 25,
    "RIGHT_KNEE": 26,
    "LEFT_ANKLE": 27,
    "RIGHT_ANKLE": 28,
    "LEFT_HEEL": 29,
    "RIGHT_HEEL": 30,
}

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

class BackViewAnalysisRequest(BaseModel):
    pose_data: List[FramePoseData]
    video_info: Dict[str, Any]

class BackViewAnalysisResult(BaseModel):
    hip_drop: Dict[str, Any]
    vertical_oscillation: Dict[str, Any]
    crossover: Dict[str, Any]
    summary: Dict[str, Any]

class BackViewAnalysisResponse(BaseModel):
    status: str
    message: str
    video_id: Optional[str] = None
    analysis_result: Optional[BackViewAnalysisResult] = None

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "back_view_analysis"}

def calculate_hip_drop(pose_data: List[FramePoseData]) -> Dict[str, Any]:
    """
    Hip Drop（骨盤の沈み込み）を計算
    
    LEFT_HIP (idx 23) と RIGHT_HIP (idx 24) のY座標の差分から
    骨盤の左右の傾きを計算する
    """
    hip_drops = []
    hip_drop_angles = []
    
    for frame in pose_data:
        if not frame.landmarks_detected or len(frame.keypoints) < 33:
            continue
        
        left_hip = frame.keypoints[LANDMARK_INDICES["LEFT_HIP"]]
        right_hip = frame.keypoints[LANDMARK_INDICES["RIGHT_HIP"]]
        
        # 両方のhipが検出されているか確認
        if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
            continue
        
        # Y座標の差分（MediaPipeはYが下が正なので、差分が大きいほど傾いている）
        y_diff = abs(left_hip.y - right_hip.y)
        hip_drops.append(y_diff)
        
        # 角度計算（度数法）
        # 2点間の距離
        distance = math.sqrt(
            (left_hip.x - right_hip.x) ** 2 + 
            (left_hip.y - right_hip.y) ** 2
        )
        if distance > 0:
            # 水平線との角度
            angle_rad = math.asin(abs(left_hip.y - right_hip.y) / distance)
            angle_deg = math.degrees(angle_rad)
            hip_drop_angles.append(angle_deg)
    
    if not hip_drops:
        return {
            "value": 0.0,
            "unit": "normalized_coordinate",
            "max_drop": 0.0,
            "average_drop": 0.0,
            "angle_degrees": 0.0,
            "max_angle_degrees": 0.0,
            "average_angle_degrees": 0.0,
            "status": "no_data"
        }
    
    return {
        "value": max(hip_drops),
        "unit": "normalized_coordinate",
        "max_drop": max(hip_drops),
        "average_drop": np.mean(hip_drops),
        "angle_degrees": np.mean(hip_drop_angles) if hip_drop_angles else 0.0,
        "max_angle_degrees": max(hip_drop_angles) if hip_drop_angles else 0.0,
        "average_angle_degrees": np.mean(hip_drop_angles) if hip_drop_angles else 0.0,
        "status": "success"
    }

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
        left_ankle = frame_keypoints[LANDMARK_INDICES["LEFT_ANKLE"]]
        right_ankle = frame_keypoints[LANDMARK_INDICES["RIGHT_ANKLE"]]
        left_knee = frame_keypoints[LANDMARK_INDICES["LEFT_KNEE"]]
        right_knee = frame_keypoints[LANDMARK_INDICES["RIGHT_KNEE"]]
        left_hip = frame_keypoints[LANDMARK_INDICES["LEFT_HIP"]]
        right_hip = frame_keypoints[LANDMARK_INDICES["RIGHT_HIP"]]
        left_shoulder = frame_keypoints[LANDMARK_INDICES["LEFT_SHOULDER"]]
        right_shoulder = frame_keypoints[LANDMARK_INDICES["RIGHT_SHOULDER"]]
        nose = frame_keypoints[LANDMARK_INDICES["NOSE"]]
        
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

def calculate_vertical_oscillation(pose_data: List[FramePoseData]) -> Dict[str, Any]:
    """
    Vertical Oscillation（上下動）を計算
    
    左右の腰の中点のY座標を全フレームで計算し、
    最大値と最小値の差分を身長比で求める
    """
    hip_center_ys = []
    skeletal_heights = []
    
    for frame in pose_data:
        if not frame.landmarks_detected or len(frame.keypoints) < 33:
            continue
        
        left_hip = frame.keypoints[LANDMARK_INDICES["LEFT_HIP"]]
        right_hip = frame.keypoints[LANDMARK_INDICES["RIGHT_HIP"]]
        
        # 両方のhipが検出されているか確認
        if left_hip.visibility < 0.5 or right_hip.visibility < 0.5:
            continue
        
        # 左右の腰の中点のY座標
        hip_center_y = (left_hip.y + right_hip.y) / 2.0
        hip_center_ys.append(hip_center_y)
        
        # このフレームの骨格身長を計算
        skeletal_height = calculate_skeletal_height(frame.keypoints)
        if skeletal_height is not None:
            skeletal_heights.append(skeletal_height)
    
    if not hip_center_ys:
        return {
            "value": 0.0,
            "unit": "height_ratio",
            "min_y": 0.0,
            "max_y": 0.0,
            "oscillation_range": 0.0,
            "oscillation_range_ratio": 0.0,
            "status": "no_data"
        }
    
    min_y = min(hip_center_ys)
    max_y = max(hip_center_ys)
    oscillation_range = max_y - min_y
    
    # 身長比を計算
    oscillation_range_ratio = None
    if skeletal_heights and len(skeletal_heights) >= 3:
        avg_skeletal_height = np.mean(skeletal_heights)
        if avg_skeletal_height > 0:
            oscillation_range_ratio = oscillation_range / avg_skeletal_height
            print(f"📏 上下動計算詳細:")
            print(f"   - 有効フレーム数: {len(skeletal_heights)}")
            print(f"   - 平均骨格身長: {avg_skeletal_height:.6f} (正規化座標)")
            print(f"   - 上下動範囲: {oscillation_range:.6f} (正規化座標)")
            print(f"   - 上下動比率（身長比）: {oscillation_range_ratio:.6f}")
    
    return {
        "value": oscillation_range_ratio if oscillation_range_ratio is not None else oscillation_range,
        "unit": "height_ratio" if oscillation_range_ratio is not None else "normalized_coordinate",
        "min_y": min_y,
        "max_y": max_y,
        "oscillation_range": oscillation_range,
        "oscillation_range_ratio": oscillation_range_ratio if oscillation_range_ratio is not None else 0.0,
        "status": "success"
    }

def detect_landing_frames(pose_data: List[FramePoseData]) -> List[int]:
    """
    着地フレームを検出（簡易版）
    
    足首のY座標が最小値になった瞬間を着地と判定
    """
    landing_frames = []
    
    # 各フレームで左右の足首のY座標の最小値を取得
    ankle_ys = []
    for frame in pose_data:
        if not frame.landmarks_detected or len(frame.keypoints) < 33:
            ankle_ys.append(None)
            continue
        
        left_ankle = frame.keypoints[LANDMARK_INDICES["LEFT_ANKLE"]]
        right_ankle = frame.keypoints[LANDMARK_INDICES["RIGHT_ANKLE"]]
        
        # どちらかが検出されている場合
        if left_ankle.visibility >= 0.5 or right_ankle.visibility >= 0.5:
            min_ankle_y = min(
                left_ankle.y if left_ankle.visibility >= 0.5 else float('inf'),
                right_ankle.y if right_ankle.visibility >= 0.5 else float('inf')
            )
            ankle_ys.append(min_ankle_y)
        else:
            ankle_ys.append(None)
    
    # ローカル最小値を検出（着地の瞬間）
    for i in range(1, len(ankle_ys) - 1):
        if ankle_ys[i] is None:
            continue
        
        # 前後のフレームと比較して最小値かどうか
        if (ankle_ys[i-1] is not None and ankle_ys[i+1] is not None and
            ankle_ys[i] < ankle_ys[i-1] and ankle_ys[i] < ankle_ys[i+1]):
            landing_frames.append(i)
    
    return landing_frames

def calculate_crossover(pose_data: List[FramePoseData]) -> Dict[str, Any]:
    """
    Crossover（着地のクロスオーバー）を計算
    
    体の中心線（NOSEから左右の腰の中点を結ぶ線）と
    着地時の足の位置との角度を計算
    """
    landing_frames = detect_landing_frames(pose_data)
    
    if not landing_frames:
        return {
            "value": 0.0,
            "unit": "degrees",
            "left_crossover": 0.0,
            "right_crossover": 0.0,
            "max_crossover": 0.0,
            "average_crossover": 0.0,
            "left_crossover_angle": 0.0,
            "right_crossover_angle": 0.0,
            "max_crossover_angle": 0.0,
            "average_crossover_angle": 0.0,
            "landing_count": 0,
            "status": "no_data"
        }
    
    crossovers = []
    left_crossovers = []
    right_crossovers = []
    crossover_angles = []
    left_crossover_angles = []
    right_crossover_angles = []
    
    for frame_idx in landing_frames:
        if frame_idx >= len(pose_data):
            continue
        
        frame = pose_data[frame_idx]
        if not frame.landmarks_detected or len(frame.keypoints) < 33:
            continue
        
        nose = frame.keypoints[LANDMARK_INDICES["NOSE"]]
        left_hip = frame.keypoints[LANDMARK_INDICES["LEFT_HIP"]]
        right_hip = frame.keypoints[LANDMARK_INDICES["RIGHT_HIP"]]
        left_ankle = frame.keypoints[LANDMARK_INDICES["LEFT_ANKLE"]]
        right_ankle = frame.keypoints[LANDMARK_INDICES["RIGHT_ANKLE"]]
        
        # 検出確認
        if (nose.visibility < 0.5 or 
            left_hip.visibility < 0.5 or right_hip.visibility < 0.5):
            continue
        
        # 体の中心線のX座標（NOSEと腰の中点の平均）
        hip_center_x = (left_hip.x + right_hip.x) / 2.0
        hip_center_y = (left_hip.y + right_hip.y) / 2.0
        center_line_x = (nose.x + hip_center_x) / 2.0
        
        # 左足のクロスオーバー（距離と角度の両方を計算）
        if left_ankle.visibility >= 0.5:
            # 水平距離（正規化座標）
            left_crossover = left_ankle.x - center_line_x
            left_crossovers.append(left_crossover)
            crossovers.append(abs(left_crossover))
            
            # 角度計算（中心線から足への角度）
            # 垂直距離: 腰の中点から足首までの距離
            vertical_distance = abs(left_ankle.y - hip_center_y)
            if vertical_distance > 0:
                # 水平距離と垂直距離から角度を計算
                angle_rad = math.atan2(abs(left_crossover), vertical_distance)
                angle_deg = math.degrees(angle_rad)
                # 符号を保持（内側が負、外側が正）
                if left_crossover < 0:
                    angle_deg = -angle_deg
                left_crossover_angles.append(angle_deg)
                crossover_angles.append(abs(angle_deg))
        
        # 右足のクロスオーバー（距離と角度の両方を計算）
        if right_ankle.visibility >= 0.5:
            # 水平距離（正規化座標）
            right_crossover = right_ankle.x - center_line_x
            right_crossovers.append(right_crossover)
            crossovers.append(abs(right_crossover))
            
            # 角度計算（中心線から足への角度）
            # 垂直距離: 腰の中点から足首までの距離
            vertical_distance = abs(right_ankle.y - hip_center_y)
            if vertical_distance > 0:
                # 水平距離と垂直距離から角度を計算
                angle_rad = math.atan2(abs(right_crossover), vertical_distance)
                angle_deg = math.degrees(angle_rad)
                # 符号を保持（内側が負、外側が正）
                if right_crossover < 0:
                    angle_deg = -angle_deg
                right_crossover_angles.append(angle_deg)
                crossover_angles.append(abs(angle_deg))
    
    if not crossovers:
        return {
            "value": 0.0,
            "unit": "degrees",
            "left_crossover": 0.0,
            "right_crossover": 0.0,
            "max_crossover": 0.0,
            "average_crossover": 0.0,
            "left_crossover_angle": 0.0,
            "right_crossover_angle": 0.0,
            "max_crossover_angle": 0.0,
            "average_crossover_angle": 0.0,
            "landing_count": len(landing_frames),
            "status": "no_data"
        }
    
    print(f"📐 クロスオーバー計算詳細:")
    print(f"   - 検出着地数: {len(landing_frames)}")
    print(f"   - 左足平均角度: {np.mean(left_crossover_angles) if left_crossover_angles else 0.0:.2f}°")
    print(f"   - 右足平均角度: {np.mean(right_crossover_angles) if right_crossover_angles else 0.0:.2f}°")
    print(f"   - 最大角度: {max(crossover_angles) if crossover_angles else 0.0:.2f}°")
    
    return {
        "value": max(crossover_angles) if crossover_angles else 0.0,
        "unit": "degrees",
        "left_crossover": np.mean(left_crossovers) if left_crossovers else 0.0,
        "right_crossover": np.mean(right_crossovers) if right_crossovers else 0.0,
        "max_crossover": max(crossovers),
        "average_crossover": np.mean(crossovers),
        "left_crossover_angle": np.mean(left_crossover_angles) if left_crossover_angles else 0.0,
        "right_crossover_angle": np.mean(right_crossover_angles) if right_crossover_angles else 0.0,
        "max_crossover_angle": max(crossover_angles) if crossover_angles else 0.0,
        "average_crossover_angle": np.mean(crossover_angles) if crossover_angles else 0.0,
        "landing_count": len(landing_frames),
        "status": "success"
    }

@app.post("/analyze", response_model=BackViewAnalysisResponse)
async def analyze_back_view(request: BackViewAnalysisRequest):
    """
    背後からの撮影動画を解析する
    
    Args:
        request: ポーズデータと動画情報
        
    Returns:
        解析結果（3つの指標）
    """
    try:
        print("=" * 80)
        print("🎯 背後解析リクエスト受信")
        print(f"   📊 フレーム数: {len(request.pose_data)}")
        print(f"   📹 動画情報: {request.video_info}")
        
        # 3つの指標を計算
        print("   🔧 Hip Drop計算中...")
        hip_drop = calculate_hip_drop(request.pose_data)
        print(f"      ✅ Hip Drop完了: 最大角度={hip_drop.get('max_angle_degrees', 0):.2f}°")
        
        print("   🔧 Vertical Oscillation計算中...")
        vertical_oscillation = calculate_vertical_oscillation(request.pose_data)
        print(f"      ✅ Vertical Oscillation完了: 範囲={vertical_oscillation.get('oscillation_range', 0):.4f}")
        
        print("   🔧 Crossover計算中...")
        crossover = calculate_crossover(request.pose_data)
        print(f"      ✅ Crossover完了: 最大距離={crossover.get('max_crossover', 0):.4f}, 最大角度={crossover.get('max_crossover_angle', 0):.2f}°, 着地数={crossover.get('landing_count', 0)}")
        
        # サマリー情報
        summary = {
            "total_frames": len(request.pose_data),
            "analyzed_frames": sum(1 for frame in request.pose_data if frame.landmarks_detected),
            "hip_drop_status": hip_drop.get("status", "unknown"),
            "vertical_oscillation_status": vertical_oscillation.get("status", "unknown"),
            "crossover_status": crossover.get("status", "unknown")
        }
        
        result = BackViewAnalysisResult(
            hip_drop=hip_drop,
            vertical_oscillation=vertical_oscillation,
            crossover=crossover,
            summary=summary
        )
        
        print(f"✅ 背後解析完了:")
        print(f"   📊 Hip Drop: 最大角度={hip_drop.get('max_angle_degrees', 0):.2f}°, 平均角度={hip_drop.get('average_angle_degrees', 0):.2f}°")
        print(f"   📊 Vertical Oscillation: 範囲={vertical_oscillation.get('oscillation_range', 0):.4f}, 身長比={vertical_oscillation.get('oscillation_range_ratio', 0):.4f} ({vertical_oscillation.get('oscillation_range_ratio', 0)*100:.2f}%)")
        print(f"   📊 Crossover: 最大距離={crossover.get('max_crossover', 0):.4f}, 最大角度={crossover.get('max_crossover_angle', 0):.2f}°, 平均角度={crossover.get('average_crossover_angle', 0):.2f}°, 着地数={crossover.get('landing_count', 0)}")
        print("=" * 80)
        
        return BackViewAnalysisResponse(
            status="success",
            message="背後解析が完了しました",
            analysis_result=result
        )
        
    except Exception as e:
        print(f"❌ 背後解析エラー: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"背後解析中にエラーが発生しました: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)

