from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any

app = FastAPI(
    title="Analysis Service",
    description="特徴量データに基づき、ランニングフォームの課題を判定・分析するサービス",
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

# リクエスト・レスポンスのデータモデル
class FeatureAnalysisRequest(BaseModel):
    """特徴量データを受け取るリクエストモデル"""
    cadence: float                 # ケイデンス (steps/min)
    knee_angle: float             # 平均膝関節角度 (degrees)
    knee_angle_at_landing: float  # 着地時膝角度 (degrees) - knee_angleと同じ値を使用
    stride_length: float          # ストライド長 (meters)
    contact_time: float           # 接地時間 (ms)
    ground_contact_time: float    # 接地時間 (ms) - contact_timeと同じ値を使用

class AnalysisResponse(BaseModel):
    """分析結果レスポンスモデル"""
    status: str
    message: str
    issues: List[str]
    analysis_summary: Dict[str, Any]

def analyze_cadence(cadence: float) -> List[str]:
    """ケイデンス分析"""
    issues = []
    if cadence < 170:
        issues.append("ピッチが遅く、上下動の大きい走りになっている可能性があります。")
    elif cadence > 200:
        issues.append("ピッチが速すぎて、効率的でない短いストライドになっている可能性があります。")
    return issues

def analyze_knee_angle(knee_angle_at_landing: float) -> List[str]:
    """膝角度分析"""
    issues = []
    if knee_angle_at_landing >= 170:
        issues.append("着地時に膝が伸びすぎており、ブレーキ動作と怪我のリスクを高めています。")
    elif knee_angle_at_landing < 140:
        issues.append("着地時の膝の曲がりが大きすぎて、推進力が不足している可能性があります。")
    return issues

def analyze_contact_time(ground_contact_time: float) -> List[str]:
    """接地時間分析"""
    issues = []
    if ground_contact_time > 240:
        issues.append("地面に足がついている時間が長く、エネルギー効率が低下している可能性があります。")
    elif ground_contact_time < 150:
        issues.append("接地時間が短すぎて、十分な推進力を得られていない可能性があります。")
    return issues

def analyze_stride_length(stride_length: float, cadence: float) -> List[str]:
    """ストライド長分析"""
    issues = []
    
    # 標準的なストライド長の範囲（1.0-1.6m）
    if stride_length > 1.6:
        issues.append("ストライド長が長すぎて、オーバーストライドになっている可能性があります。")
    elif stride_length < 0.8:
        issues.append("ストライド長が短すぎて、効率的でない走りになっている可能性があります。")
    
    # ケイデンスとストライド長のバランス
    if cadence > 0 and stride_length > 0:
        speed_estimate = (cadence / 60) * stride_length * 2  # 推定速度 (m/s)
        if speed_estimate > 6.0:  # 6m/s以上（かなり速い）
            if stride_length / (cadence / 60) > 2.5:
                issues.append("高速走行時にストライド長に依存しすぎており、怪我のリスクが高まっています。")
    
    return issues

def calculate_overall_assessment(total_issues: int, features: FeatureAnalysisRequest) -> Dict[str, Any]:
    """総合評価の計算"""
    
    # スコア計算（10点満点）
    base_score = 10
    score_deduction = min(total_issues * 1.5, 8)  # 課題1つにつき1.5点減点、最大8点減点
    overall_score = max(base_score - score_deduction, 2)
    
    # 効率性評価
    efficiency_score = 10
    if features.cadence < 170 or features.cadence > 200:
        efficiency_score -= 2
    if features.ground_contact_time > 240:
        efficiency_score -= 2
    if features.stride_length > 1.6 or features.stride_length < 0.8:
        efficiency_score -= 1.5
    
    efficiency_rating = "A" if efficiency_score >= 8 else "B" if efficiency_score >= 6 else "C" if efficiency_score >= 4 else "D"
    
    # 怪我リスク評価
    injury_risk = "低"
    if features.knee_angle_at_landing >= 170 and features.ground_contact_time > 240:
        injury_risk = "高"
    elif features.knee_angle_at_landing >= 170 or features.ground_contact_time > 240 or features.stride_length > 1.6:
        injury_risk = "中"
    
    return {
        "overall_score": round(overall_score, 1),
        "efficiency_rating": efficiency_rating,
        "injury_risk_level": injury_risk,
        "analyzed_features": {
            "cadence": f"{features.cadence:.1f} steps/min",
            "knee_angle": f"{features.knee_angle_at_landing:.1f}°",
            "contact_time": f"{features.ground_contact_time:.1f} ms",
            "stride_length": f"{features.stride_length:.2f} m"
        },
        "recommendations": generate_recommendations(features, total_issues)
    }

def generate_recommendations(features: FeatureAnalysisRequest, issue_count: int) -> List[str]:
    """改善提案の生成"""
    recommendations = []
    
    if features.cadence < 170:
        recommendations.append("ピッチを向上させるため、短い距離での高頻度ランニングを練習してください。")
    
    if features.knee_angle_at_landing >= 170:
        recommendations.append("着地時の膝の曲げを意識し、足音を小さくする練習をしてください。")
    
    if features.ground_contact_time > 240:
        recommendations.append("地面を軽やかに蹴る意識で、接地時間を短縮してください。")
    
    if features.stride_length > 1.6:
        recommendations.append("歩幅を小さくして、足の回転数を上げることを意識してください。")
    
    if issue_count == 0:
        recommendations.append("現在のフォームは良好です。この調子を維持してください。")
    elif issue_count >= 3:
        recommendations.append("複数の課題があります。まずは1つずつ改善に取り組むことをお勧めします。")
    
    return recommendations

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "analysis"}

@app.post("/analyze")
async def analyze_running_form(request: FeatureAnalysisRequest):
    """
    特徴量データからランニングフォームの課題を分析する
    
    Args:
        request: 特徴量データ（ケイデンス、膝角度、接地時間など）
        
    Returns:
        検出された課題と分析結果
    """
    try:
        # ★★★ デバッグログ: 受け取った特徴量データを出力 ★★★
        print("=" * 60)
        print("🔍 [ANALYSIS SERVICE] 受け取った特徴量データ:")
        print(f"   - ケイデンス: {request.cadence} steps/min")
        print(f"   - 膝角度: {request.knee_angle_at_landing}°")
        print(f"   - 接地時間: {request.ground_contact_time} ms")
        print(f"   - ストライド長: {request.stride_length} m")
        print("=" * 60)
        
        # 各特徴量の分析
        issues = []
        
        # ルールA: ケイデンスの評価
        cadence_issues = analyze_cadence(request.cadence)
        issues.extend(cadence_issues)
        
        # ルールB: 着地時の膝角度の評価
        knee_issues = analyze_knee_angle(request.knee_angle_at_landing)
        issues.extend(knee_issues)
        
        # ルールC: 接地時間の評価
        contact_issues = analyze_contact_time(request.ground_contact_time)
        issues.extend(contact_issues)
        
        # 追加分析: ストライド長の評価
        stride_issues = analyze_stride_length(request.stride_length, request.cadence)
        issues.extend(stride_issues)
        
        # 総合評価の計算
        analysis_summary = calculate_overall_assessment(len(issues), request)
        
        # 結果の作成
        status = "success"
        message = f"{len(issues)}個の課題が検出されました" if issues else "フォームに大きな問題は見つかりませんでした"
        
        # ★★★ デバッグログ: 検出された課題リストを出力 ★★★
        print("🎯 [ANALYSIS SERVICE] 検出された課題リスト:")
        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   課題は検出されませんでした")
        print(f"📊 総合スコア: {analysis_summary.get('overall_score', 'N/A')}")
        print("=" * 60)
        
        return {
            "status": status,
            "message": message,
            "issues": issues,
            "analysis_summary": analysis_summary
        }
        
    except Exception as e:
        print(f"❌ [ANALYSIS SERVICE] エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")

@app.get("/benchmarks")
async def get_running_benchmarks():
    """ランニング指標のベンチマーク値を取得"""
    return {
        "cadence": {
            "optimal_range": {"min": 170, "max": 190},
            "elite_range": {"min": 180, "max": 200},
            "beginner_range": {"min": 150, "max": 170},
            "unit": "steps/min"
        },
        "knee_angle_at_landing": {
            "optimal_range": {"min": 140, "max": 170},
            "warning_threshold": 170,
            "unit": "degrees"
        },
        "ground_contact_time": {
            "optimal_range": {"min": 150, "max": 240},
            "elite_range": {"min": 150, "max": 200},
            "warning_threshold": 240,
            "unit": "milliseconds"
        },
        "stride_length": {
            "optimal_range": {"min": 1.0, "max": 1.6},
            "warning_threshold": 1.6,
            "unit": "meters"
        }
    }

@app.get("/analysis-rules")
async def get_analysis_rules():
    """分析ルールの詳細を取得"""
    return {
        "cadence_rules": {
            "slow_cadence": {
                "threshold": "< 170 steps/min",
                "issue": "ピッチが遅く、上下動の大きい走りになっている可能性があります。"
            },
            "fast_cadence": {
                "threshold": "> 200 steps/min", 
                "issue": "ピッチが速すぎて、効率的でない短いストライドになっている可能性があります。"
            }
        },
        "knee_angle_rules": {
            "extended_knee": {
                "threshold": ">= 170 degrees",
                "issue": "着地時に膝が伸びすぎており、ブレーキ動作と怪我のリスクを高めています。"
            },
            "over_flexed_knee": {
                "threshold": "< 140 degrees",
                "issue": "着地時の膝の曲がりが大きすぎて、推進力が不足している可能性があります。"
            }
        },
        "contact_time_rules": {
            "long_contact": {
                "threshold": "> 240 ms",
                "issue": "地面に足がついている時間が長く、エネルギー効率が低下している可能性があります。"
            },
            "short_contact": {
                "threshold": "< 150 ms",
                "issue": "接地時間が短すぎて、十分な推進力を得られていない可能性があります。"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 