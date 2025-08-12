from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any
from enum import Enum

app = FastAPI(
    title="Analysis Service",
    description="抽出された特徴量に基づき、ランニングフォームの問題点を特定・分析するサービス",
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

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnalysisRequest(BaseModel):
    video_id: str
    biomechanical_features: List[Dict[str, Any]]

class Issue(BaseModel):
    issue_id: str
    category: str
    title: str
    description: str
    severity: SeverityLevel
    affected_metrics: List[str]
    confidence_score: float

class AnalysisResult(BaseModel):
    overall_score: float
    efficiency_rating: str
    injury_risk_level: SeverityLevel
    identified_issues: List[Issue]
    strengths: List[str]
    form_comparison: Dict[str, Any]

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "analysis"}

@app.post("/analyze")
async def analyze_running_form(request: AnalysisRequest):
    """
    生体力学的特徴量からランニングフォームを分析する
    
    Args:
        request: 動画IDと特徴量データのリスト
        
    Returns:
        ランニングフォーム分析結果
    """
    # TODO: 各特徴量の正常範囲との比較
    # TODO: 左右非対称性の検出
    # TODO: オーバーストライドの検出
    # TODO: 過度な上下動の検出
    # TODO: 不適切な着地パターンの識別
    # TODO: エネルギー効率の評価
    # TODO: 怪我リスクの評価
    # TODO: ランニング経済性の計算
    # TODO: 個人の体型・レベルに応じた補正
    
    # ダミーの分析結果
    identified_issues = [
        Issue(
            issue_id="overstride_001",
            category="stride_mechanics",
            title="オーバーストライド",
            description="ストライド長が理想値よりも長く、着地時の衝撃が大きくなっています。",
            severity=SeverityLevel.MEDIUM,
            affected_metrics=["stride_length", "ground_contact_time"],
            confidence_score=0.85
        ),
        Issue(
            issue_id="asymmetry_002", 
            category="symmetry",
            title="左右非対称性",
            description="左右の膝関節角度に5度以上の差があり、フォームの非対称性が見られます。",
            severity=SeverityLevel.LOW,
            affected_metrics=["left_knee_angle", "right_knee_angle"],
            confidence_score=0.92
        ),
        Issue(
            issue_id="vertical_osc_003",
            category="efficiency",
            title="過度な上下動",
            description="垂直方向の振動が理想値を超えており、エネルギー効率が低下しています。",
            severity=SeverityLevel.MEDIUM,
            affected_metrics=["vertical_oscillation"],
            confidence_score=0.78
        )
    ]
    
    analysis_result = AnalysisResult(
        overall_score=7.2,
        efficiency_rating="B+",
        injury_risk_level=SeverityLevel.MEDIUM,
        identified_issues=identified_issues,
        strengths=[
            "適切なケイデンス（180 spm）",
            "良好な体幹姿勢",
            "安定した腕振りリズム"
        ],
        form_comparison={
            "elite_runner_similarity": 0.72,
            "recreational_runner_percentile": 85,
            "age_group_ranking": "上位15%"
        }
    )
    
    return {
        "status": "success",
        "video_id": request.video_id,
        "analysis_timestamp": "2025-01-26T10:00:00Z",
        "result": analysis_result,
        "metadata": {
            "analysis_algorithm_version": "2.1",
            "reference_database": "elite_runners_2024",
            "processing_time_ms": 245,
            "total_issues_found": len(identified_issues)
        }
    }

@app.get("/benchmarks")
async def get_running_benchmarks():
    """ランニング指標のベンチマーク値を取得"""
    return {
        "cadence": {
            "elite": {"min": 180, "max": 190, "optimal": 185},
            "recreational": {"min": 160, "max": 180, "optimal": 170},
            "beginner": {"min": 150, "max": 170, "optimal": 160}
        },
        "stride_length": {
            "formula": "height * 0.43 - 0.65",
            "range_percentage": {"min": 85, "max": 115}
        },
        "ground_contact_time": {
            "elite": {"min": 0.15, "max": 0.20},
            "recreational": {"min": 0.20, "max": 0.30},
            "unit": "seconds"
        },
        "vertical_oscillation": {
            "excellent": {"max": 0.06},
            "good": {"min": 0.06, "max": 0.08},
            "fair": {"min": 0.08, "max": 0.10},
            "poor": {"min": 0.10},
            "unit": "meters"
        }
    }

@app.get("/risk-factors")
async def get_injury_risk_factors():
    """怪我リスク要因の定義を取得"""
    return {
        "high_risk": [
            "過度なオーバーストライド（理想値の120%以上）",
            "極端な非対称性（左右差10%以上）",
            "踵着地と長い接地時間の組み合わせ",
            "異常に高い垂直振動（0.12m以上）"
        ],
        "moderate_risk": [
            "軽度のオーバーストライド（理想値の110-120%）",
            "中程度の非対称性（左右差5-10%）",
            "低いケイデンス（150 spm未満）",
            "過度な前傾姿勢（8度以上）"
        ],
        "protective_factors": [
            "適切なケイデンス（170-190 spm）",
            "中足部着地",
            "良好な左右対称性（左右差5%未満）",
            "安定した体幹姿勢"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 