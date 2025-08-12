from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any
from enum import Enum

app = FastAPI(
    title="Advice Generation Service",
    description="特定された問題点に対して、具体的な改善策とエクササイズを提案するサービス",
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

class ExerciseType(str, Enum):
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    TECHNIQUE = "technique"
    CARDIO = "cardio"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AdviceRequest(BaseModel):
    video_id: str
    analysis_result: Dict[str, Any]

class Exercise(BaseModel):
    exercise_id: str
    name: str
    type: ExerciseType
    description: str
    duration: str
    repetitions: str
    frequency: str
    video_url: str
    equipment_needed: List[str]

class Advice(BaseModel):
    advice_id: str
    issue_id: str
    priority: Priority
    title: str
    description: str
    immediate_tips: List[str]
    long_term_plan: List[str]
    exercises: List[Exercise]
    expected_improvement_timeline: str

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "advice_generation"}

@app.post("/generate")
async def generate_advice(request: AdviceRequest):
    """
    分析結果に基づいて改善アドバイスを生成する
    
    Args:
        request: 動画IDと分析結果
        
    Returns:
        具体的な改善アドバイスとエクササイズプラン
    """
    # TODO: 問題の重要度に基づく優先順位付け
    # TODO: 個人のレベル・体力に応じたカスタマイズ
    # TODO: 段階的な改善プランの作成
    # TODO: エクササイズデータベースからの適切な選択
    # TODO: 改善効果の予測モデル
    # TODO: フォローアップスケジュールの提案
    
    # ダミーのアドバイス生成
    advice_list = [
        Advice(
            advice_id="advice_001",
            issue_id="overstride_001",
            priority=Priority.HIGH,
            title="オーバーストライド改善プログラム",
            description="ストライド長を適正化し、着地衝撃を軽減するための包括的改善プラン",
            immediate_tips=[
                "ケイデンスを180-185 spmに意識的に上げる",
                "メトロノームアプリを使用してリズムを身につける",
                "足音を小さくすることを意識する",
                "重心の真下に足を着地させる意識を持つ"
            ],
            long_term_plan=[
                "週3回のケイデンス特化ランニング（4週間）",
                "ストライド長測定とフィードバック練習",
                "フォーム動画の定期撮影と比較",
                "月1回のフォーム分析と調整"
            ],
            exercises=[
                Exercise(
                    exercise_id="ex_001",
                    name="ハイケイデンス・ドリル",
                    type=ExerciseType.TECHNIQUE,
                    description="メトロノームに合わせて180bpmで短いステップを刻む練習",
                    duration="5分",
                    repetitions="3セット",
                    frequency="週3回",
                    video_url="https://example.com/cadence-drill",
                    equipment_needed=["メトロノームアプリ"]
                ),
                Exercise(
                    exercise_id="ex_002",
                    name="その場かけ足",
                    type=ExerciseType.TECHNIQUE,
                    description="その場で高いケイデンスを維持しながら軽快に足踏み",
                    duration="30秒",
                    repetitions="10セット",
                    frequency="毎日",
                    video_url="https://example.com/marching-drill",
                    equipment_needed=[]
                )
            ],
            expected_improvement_timeline="2-4週間で効果を実感、3ヶ月で習慣化"
        ),
        Advice(
            advice_id="advice_002",
            issue_id="asymmetry_002",
            priority=Priority.MEDIUM,
            title="左右バランス強化プログラム",
            description="左右の動きの非対称性を解消し、効率的で安全なランニングフォームを構築",
            immediate_tips=[
                "片足立ちバランス練習を日常に取り入れる",
                "弱い側の筋力強化を意識する",
                "鏡の前でのランニングフォームチェック",
                "左右交互の動きを意識したウォームアップ"
            ],
            long_term_plan=[
                "週2回の片足強化トレーニング（6週間）",
                "月2回のフォーム分析と左右比較",
                "ランニング前のバランス系ウォームアップ習慣化",
                "3ヶ月後の再評価と調整"
            ],
            exercises=[
                Exercise(
                    exercise_id="ex_003",
                    name="シングルレッグ・デッドリフト",
                    type=ExerciseType.STRENGTH,
                    description="片足で立ちながら反対足を後ろに上げるバランス強化運動",
                    duration="45秒",
                    repetitions="各脚3セット",
                    frequency="週2回",
                    video_url="https://example.com/single-leg-deadlift",
                    equipment_needed=[]
                ),
                Exercise(
                    exercise_id="ex_004",
                    name="ラテラル・ステップアップ",
                    type=ExerciseType.STRENGTH,
                    description="横方向の安定性と左右バランスを強化する運動",
                    duration="1分",
                    repetitions="各側3セット",
                    frequency="週2回",
                    video_url="https://example.com/lateral-step-up",
                    equipment_needed=["ステップ台または階段"]
                )
            ],
            expected_improvement_timeline="4-6週間で左右差の軽減、3ヶ月で著明な改善"
        )
    ]
    
    return {
        "status": "success",
        "video_id": request.video_id,
        "advice_generated_at": "2025-01-26T10:00:00Z",
        "total_advice_items": len(advice_list),
        "advice": advice_list,
        "overall_recommendations": {
            "focus_areas": ["ケイデンス改善", "左右バランス強化", "着地技術向上"],
            "estimated_timeline": "3-6ヶ月での大幅な改善",
            "follow_up_schedule": [
                "2週間後: 初回フォローアップ",
                "1ヶ月後: 中間評価",
                "3ヶ月後: 総合再評価"
            ]
        },
        "metadata": {
            "advice_algorithm_version": "1.5",
            "personalization_level": "standard",
            "evidence_base": "biomechanics_research_2024"
        }
    }

@app.get("/exercises/categories")
async def get_exercise_categories():
    """エクササイズカテゴリと効果を取得"""
    return {
        "strength": {
            "description": "筋力強化によるフォーム安定化",
            "target_issues": ["非対称性", "安定性不足", "推進力不足"],
            "example_exercises": ["シングルレッグ・スクワット", "ヒップブリッジ", "プランク"]
        },
        "flexibility": {
            "description": "柔軟性改善による可動域拡大",
            "target_issues": ["ストライド制限", "姿勢問題", "筋肉の硬さ"],
            "example_exercises": ["ダイナミックストレッチ", "ヒップフレクサーストレッチ", "カーフストレッチ"]
        },
        "technique": {
            "description": "動作パターンの技術的改善",
            "target_issues": ["オーバーストライド", "着地パターン", "腕振り"],
            "example_exercises": ["ケイデンスドリル", "ハイニー", "バウンディング"]
        },
        "cardio": {
            "description": "心肺機能とランニング持久力の向上",
            "target_issues": ["効率性", "疲労による フォーム崩れ"],
            "example_exercises": ["インターバル走", "テンポ走", "LSD"]
        }
    }

@app.get("/tips/immediate")
async def get_immediate_tips():
    """すぐに実践できる改善のコツを取得"""
    return {
        "general": [
            "ランニング前に5分間のダイナミックウォームアップ",
            "毎回のランニング後にフォームを振り返る習慣",
            "週1回は自分のランニング動画を撮影",
            "シューズの摩耗パターンをチェック"
        ],
        "during_run": [
            "「軽やか」「リズミカル」を常に意識",
            "呼吸を整えてリラックス",
            "足音を小さくする意識",
            "笑顔を保つ余裕を持つペース設定"
        ],
        "post_run": [
            "クールダウンとしてのウォーキング",
            "主要筋群の静的ストレッチ（10分）",
            "水分補給と適切な栄養摂取",
            "ランニング日誌への記録"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005) 