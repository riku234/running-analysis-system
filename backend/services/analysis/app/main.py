import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional

app = FastAPI(
    title="Analysis Service - Advanced Angular Analysis",
    description="5つの主要関節角度パラメータに基づく統計的ランニングフォーム分析サービス",
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

# =============================================================================
# 標準動作モデルの定義 (5パラメータ限定)
# =============================================================================
# TODO: このセクションは、将来的に完成した標準動作モデルのデータに差し替える必要があります。
# 現在は実装とテストのためのダミーデータを使用しています。
DUMMY_STANDARD_MODEL = {
    "trunk_angle":  {"mean": 15.0, "std_dev": 2.0},   # 体幹前傾角度
    "hip_angle":    {"mean": 140.0, "std_dev": 5.0},  # 股関節角度
    "knee_angle":   {"mean": 160.0, "std_dev": 6.0},  # 膝関節角度
    "ankle_angle":  {"mean": 85.0, "std_dev": 4.0},   # 足関節角度
    "elbow_angle":  {"mean": 95.0, "std_dev": 10.0},  # 肘関節角度
}

# =============================================================================
# リクエスト・レスポンスのデータモデル
# =============================================================================
class AngleData(BaseModel):
    """角度データ（平均、最小、最大）"""
    avg: float
    min: float
    max: float

class FeatureAnalysisRequest(BaseModel):
    """特徴量データを受け取るリクエストモデル（新5パラメータ対応）"""
    trunk_angle: Optional[AngleData] = None
    left_hip_angle: Optional[AngleData] = None
    right_hip_angle: Optional[AngleData] = None
    left_knee_angle: Optional[AngleData] = None
    right_knee_angle: Optional[AngleData] = None
    left_ankle_angle: Optional[AngleData] = None
    right_ankle_angle: Optional[AngleData] = None
    left_elbow_angle: Optional[AngleData] = None
    right_elbow_angle: Optional[AngleData] = None

class AnalysisIssue(BaseModel):
    """分析で検出された課題"""
    parameter: str
    priority_score: float
    message: str
    user_value: float
    standard_value: float
    deviation: float

class AdvancedAnalysisResponse(BaseModel):
    """高度な分析結果レスポンスモデル"""
    status: str
    message: str
    issues: List[AnalysisIssue]
    analysis_details: Dict[str, Any]

# =============================================================================
# 統計的分析ロジック
# =============================================================================
def calculate_priority_score(user_avg: float, standard_model: Dict[str, float], deviation: float) -> float:
    """
    優先度スコアを計算する
    
    Args:
        user_avg: ユーザーの平均値
        standard_model: 標準モデル（mean, std_dev）
        deviation: 標準値からの差
    
    Returns:
        weighted_variability: 重み付け変動度スコア
    """
    try:
        mean = standard_model["mean"]
        std_dev = standard_model["std_dev"]
        threshold = std_dev * 1.5
        
        # 変動係数を計算（ゼロ除算回避）
        if mean == 0:
            cv = 1.0  # デフォルト値
        else:
            cv = std_dev / mean
        
        # 重み付け変動度を計算（ゼロ除算回避）
        if cv == 0:
            weighted_variability = abs(deviation) * 1000  # 高いスコア
        else:
            weighted_variability = (abs(user_avg) + threshold) / cv
        
        return round(weighted_variability, 1)
        
    except Exception:
        return 0.0

def analyze_single_parameter(parameter_name: str, side: str, user_data: AngleData, standard_model: Dict[str, float]) -> Optional[AnalysisIssue]:
    """
    単一パラメータの分析を行う
    
    Args:
        parameter_name: パラメータ名（trunk_angle, hip_angle など）
        side: 左右識別（"left", "right", または ""）
        user_data: ユーザーの角度データ
        standard_model: 標準モデル
    
    Returns:
        AnalysisIssue または None（課題が検出されなかった場合）
    """
    try:
        user_avg = user_data.avg
        standard_mean = standard_model["mean"]
        standard_std = standard_model["std_dev"]
        
        # 差分と閾値の計算
        deviation = user_avg - standard_mean
        threshold = standard_std * 1.5
        
        # 課題判定
        if abs(deviation) > threshold:
            # フルパラメータ名の構築
            full_param_name = f"{side}_{parameter_name}" if side else parameter_name
            
            # 優先度スコアの計算
            priority_score = calculate_priority_score(user_avg, standard_model, deviation)
            
            # 日本語メッセージの生成
            angle_name_jp = {
                "trunk_angle": "体幹角度",
                "hip_angle": "股関節角度",
                "knee_angle": "膝関節角度", 
                "ankle_angle": "足関節角度",
                "elbow_angle": "肘関節角度"
            }.get(parameter_name, parameter_name)
            
            side_jp = {
                "left": "（左）",
                "right": "（右）",
                "": ""
            }.get(side, "")
            
            direction = "大きく" if deviation > 0 else "小さく"
            
            message = f"{angle_name_jp}{side_jp}が理想よりも約{abs(deviation):.1f}度{direction}なっており、改善の必要があります。"
            
            return AnalysisIssue(
                parameter=full_param_name,
                priority_score=priority_score,
                message=message,
                user_value=round(user_avg, 1),
                standard_value=round(standard_mean, 1),
                deviation=round(deviation, 1)
            )
        
        return None
        
    except Exception as e:
        print(f"❌ パラメータ分析エラー ({parameter_name}, {side}): {str(e)}")
        return None

def perform_comprehensive_analysis(request: FeatureAnalysisRequest) -> List[AnalysisIssue]:
    """
    5つのパラメータ×左右の包括的な分析を実行
    
    Args:
        request: 特徴量データ
    
    Returns:
        優先度順にソートされた課題リスト
    """
    issues = []
    
    # 体幹角度の分析（左右なし）
    if request.trunk_angle is not None:
        issue = analyze_single_parameter("trunk_angle", "", request.trunk_angle, DUMMY_STANDARD_MODEL["trunk_angle"])
        if issue:
            issues.append(issue)
    
    # 左右のパラメータ分析
    sides = ["left", "right"]
    parameters = [
        ("hip_angle", [request.left_hip_angle, request.right_hip_angle]),
        ("knee_angle", [request.left_knee_angle, request.right_knee_angle]),
        ("ankle_angle", [request.left_ankle_angle, request.right_ankle_angle]),
        ("elbow_angle", [request.left_elbow_angle, request.right_elbow_angle])
    ]
    
    for param_name, param_data_list in parameters:
        for i, side in enumerate(sides):
            user_data = param_data_list[i]
            if user_data is not None:
                standard_model = DUMMY_STANDARD_MODEL[param_name]
                issue = analyze_single_parameter(param_name, side, user_data, standard_model)
                if issue:
                    issues.append(issue)
    
    # 優先度スコアでソート（降順）
    issues.sort(key=lambda x: x.priority_score, reverse=True)
    
    return issues

# =============================================================================
# API エンドポイント
# =============================================================================
@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {
        "status": "healthy", 
        "service": "analysis",
        "version": "2.0.0",
        "description": "Advanced Angular Analysis Service"
    }

@app.post("/analyze", response_model=AdvancedAnalysisResponse)
async def analyze_running_form(request: FeatureAnalysisRequest):
    """
    5つの主要角度パラメータからランニングフォームの課題を統計的に分析する
    
    Args:
        request: 角度特徴量データ（体幹、股関節、膝、足首、肘）
        
    Returns:
        優先度順にソートされた課題と詳細分析結果
    """
    try:
        # ★★★ デバッグログ: 受け取った角度データを出力 ★★★
        print("=" * 80)
        print("🔍 [ADVANCED ANALYSIS SERVICE] 受け取った角度データ:")
        
        if request.trunk_angle:
            print(f"   - 体幹角度: {request.trunk_angle.avg:.1f}° (範囲: {request.trunk_angle.min:.1f}°-{request.trunk_angle.max:.1f}°)")
        
        for side in ["left", "right"]:
            side_jp = "左" if side == "left" else "右"
            angles = {
                "股関節": getattr(request, f"{side}_hip_angle"),
                "膝": getattr(request, f"{side}_knee_angle"),
                "足首": getattr(request, f"{side}_ankle_angle"),
                "肘": getattr(request, f"{side}_elbow_angle")
            }
            
            for name_jp, angle_data in angles.items():
                if angle_data:
                    print(f"   - {side_jp}{name_jp}角度: {angle_data.avg:.1f}° (範囲: {angle_data.min:.1f}°-{angle_data.max:.1f}°)")
        
        print("=" * 80)
        
        # 包括的分析の実行
        issues = perform_comprehensive_analysis(request)
        
        # 結果メッセージの生成
        if not issues:
            status = "success"
            message = "分析した関節角度は全て理想的な範囲内にあります。優れたランニングフォームです！"
        else:
            status = "success"
            message = f"{len(issues)}個の改善ポイントが検出されました。優先度順に表示しています。"
        
        # 分析詳細の計算
        total_analyzed = sum([
            1 if request.trunk_angle else 0,
            1 if request.left_hip_angle else 0,
            1 if request.right_hip_angle else 0,
            1 if request.left_knee_angle else 0,
            1 if request.right_knee_angle else 0,
            1 if request.left_ankle_angle else 0,
            1 if request.right_ankle_angle else 0,
            1 if request.left_elbow_angle else 0,
            1 if request.right_elbow_angle else 0
        ])
        
        analysis_details = {
            "total_parameters_analyzed": total_analyzed,
            "issues_detected": len(issues),
            "highest_priority_score": round(issues[0].priority_score, 1) if issues else 0.0,
            "analysis_method": "Statistical Deviation Analysis with Dummy Standard Model",
            "standard_model_version": "dummy_v1.0",
            "evaluation_summary": {
                "excellent": len(issues) == 0,
                "good": 0 < len(issues) <= 2,
                "needs_improvement": 2 < len(issues) <= 4,
                "significant_issues": len(issues) > 4
            }
        }
        
        # ★★★ デバッグログ: 検出された課題を優先度順に出力 ★★★
        print("🎯 [ADVANCED ANALYSIS SERVICE] 検出された課題（優先度順）:")
        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue.parameter} (スコア: {issue.priority_score})")
                print(f"      {issue.message}")
                print(f"      ユーザー値: {issue.user_value}°, 標準値: {issue.standard_value}°, 差: {issue.deviation:+.1f}°")
        else:
            print("   課題は検出されませんでした - 優秀なフォームです！")
        
        print(f"📊 分析パラメータ数: {total_analyzed}")
        print("=" * 80)
        
        return AdvancedAnalysisResponse(
            status=status,
            message=message,
            issues=issues,
            analysis_details=analysis_details
        )
        
    except Exception as e:
        print(f"❌ [ADVANCED ANALYSIS SERVICE] エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail=f"高度分析中にエラーが発生しました: {str(e)}")

@app.get("/standard-model")
async def get_standard_model():
    """現在使用中の標準動作モデルを取得"""
    return {
        "model_type": "dummy",
        "version": "1.0",
        "description": "実装・テスト用のダミー標準動作モデル",
        "warning": "このモデルは将来的に実際の標準データに差し替えられる予定です",
        "parameters": DUMMY_STANDARD_MODEL,
        "notes": "mean: 平均値, std_dev: 標準偏差（単位: 度）"
    }

@app.get("/analysis-parameters")
async def get_analysis_parameters():
    """分析パラメータの詳細情報を取得"""
    return {
        "supported_parameters": [
            {
                "name": "trunk_angle",
                "description": "体幹前傾角度",
                "sides": ["none"],
                "unit": "degrees"
            },
            {
                "name": "hip_angle", 
                "description": "股関節角度",
                "sides": ["left", "right"],
                "unit": "degrees"
        },
            {
                "name": "knee_angle",
                "description": "膝関節角度", 
                "sides": ["left", "right"],
                "unit": "degrees"
        },
            {
                "name": "ankle_angle",
                "description": "足関節角度",
                "sides": ["left", "right"], 
                "unit": "degrees"
            },
            {
                "name": "elbow_angle",
                "description": "肘関節角度",
                "sides": ["left", "right"],
                "unit": "degrees"
        }
        ],
        "analysis_method": {
            "threshold_calculation": "標準偏差 × 1.5",
            "priority_scoring": "重み付け変動度 = (ユーザー値 + 閾値) / 変動係数",
            "sorting": "優先度スコア降順"
        }
    }

if __name__ == "__main__":
    print("🚀 Advanced Angular Analysis Service v2.0.0 を起動中...")
    print("📐 5つの主要関節角度パラメータによる統計的分析")
    print("⚠️  ダミー標準モデルを使用中（将来差し替え予定）")
    uvicorn.run(app, host="0.0.0.0", port=8004) 