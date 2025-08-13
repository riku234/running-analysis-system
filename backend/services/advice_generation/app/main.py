from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any

# 新しい特徴量ベースの課題に対応するアドバイス知識ベース
ADVICE_DATABASE = {
    "ピッチが遅く、上下動の大きい走りになっている可能性があります。": {
        "title": "ケイデンス（ピッチ）の改善",
        "description": "歩数を意識的に増やすことで、一歩あたりの負担を減らし、より効率的な走りに近づきます。目標は1分あたり180歩です。",
        "exercise": "練習ドリル: メトロノームアプリを180bpmに設定し、そのリズムに合わせて走る練習を取り入れてみましょう。"
    },
    "着地時に膝が伸びすぎており、ブレーキ動作と怪我のリスクを高めています。": {
        "title": "着地衝撃の緩和",
        "description": "着地は体の真下を意識し、膝を少し曲げた状態で接地することで、衝撃を和らげスムーズな体重移動が可能になります。",
        "exercise": "練習ドリル: その場で足踏みをする際に、音を立てずに静かに着地する練習を繰り返してみましょう。"
    },
    "地面に足がついている時間が長く、エネルギー効率が低下している可能性があります。": {
        "title": "接地時間の短縮",
        "description": "地面を「押す」のではなく「弾く」ようなイメージを持つと、接地時間を短縮できます。足が地面に触れたらすぐに引き上げることを意識してください。",
        "exercise": "練習ドリル: 短い縄跳びをリズミカルに行うと、素早い足の切り替えしと弾むような接地感覚を養うのに役立ちます。"
    }
}

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

# 新しいアドバイス形式では使用しないため削除

class AdviceRequest(BaseModel):
    video_id: str
    issues: List[str]  # 課題リスト（issue_analysisから受け取る）

class AdviceResponse(BaseModel):
    status: str
    message: str
    advice_list: List[Dict[str, Any]]

# 古いクラス定義を削除（新しいアドバイス形式では不要）

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "advice_generation"}

@app.post("/generate", response_model=AdviceResponse)
async def generate_advice(request: AdviceRequest):
    """
    検出された課題に基づいて改善アドバイスを生成する
    
    Args:
        request: 動画IDと課題リスト
        
    Returns:
        具体的な改善アドバイス
    """
    try:
        advice_list = []
        
        # 各課題に対してアドバイスデータベースから対応するアドバイスを取得
        for issue in request.issues:
            if issue in ADVICE_DATABASE:
                advice_data = ADVICE_DATABASE[issue]
                advice_item = {
                    "issue": issue,
                    "title": advice_data["title"],
                    "description": advice_data["description"],
                    "exercise": advice_data["exercise"]
                }
                advice_list.append(advice_item)
        
        # 課題が見つからない場合は一般的なアドバイスを提供
        if not advice_list:
            advice_list = [{
                "issue": "一般的なアドバイス",
                "title": "ランニングフォーム向上",
                "description": "現在のフォームは良好です。継続的な練習で更なる向上を目指しましょう。",
                "exercise": "練習ドリル: 週に1回、自分のランニング動画を撮影してフォームをチェックしてみましょう。"
            }]
        
        return AdviceResponse(
            status="success",
            message=f"{len(advice_list)}つのアドバイスを生成しました",
            advice_list=advice_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アドバイス生成中にエラーが発生しました: {str(e)}")

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