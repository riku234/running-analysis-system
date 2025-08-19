import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Gemini APIキーの取得と検証
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY環境変数が設定されていません。.envファイルにAPIキーを設定してください。")

# Gemini APIの初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

app = FastAPI(
    title="Advice Generation Service (Gemini-Powered)",
    description="Gemini APIを使用してランニングフォームの改善アドバイスを生成するサービス",
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

class AdviceRequest(BaseModel):
    video_id: str
    issues: List[str]  # 課題リスト（issue_analysisから受け取る）

class AdviceResponse(BaseModel):
    status: str
    message: str
    advice_list: List[Dict[str, Any]]

def create_gemini_prompt(issues: List[str]) -> str:
    """Gemini APIに送信するプロンプトを生成"""
    issues_text = "\n".join([f"- {issue}" for issue in issues])
    
    prompt = f"""あなたは、ランニングフォームを分析する専門家であり、優れたランニングコーチです。

以下のリストにあるランニングフォームの課題点について、具体的で、ポジティブで、実践的なアドバイスを生成してください。

【検出された課題】:
{issues_text}

必ず以下のJSON形式の文字列"のみ"を返してください。説明文や```jsonのようなマークダウンは一切含めないでください。

{{
  "advices": [
    {{
      "title": "（課題を一言でまとめたタイトル）",
      "description": "（なぜそれが課題なのか、どう改善すべきかの詳細な説明。具体的で前向きな表現を使用）",
      "exercise": "（改善に役立つ具体的な練習ドリルやエクササイズ。実践しやすい形で説明）"
    }}
  ]
}}

注意事項:
- 各課題に対して1つずつアドバイスを生成してください
- タイトルは簡潔で分かりやすく
- 説明は初心者にも理解しやすい言葉で
- エクササイズは自宅や公園で実践できる内容で
- JSON形式以外は一切出力しないでください"""
    
    return prompt

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {
        "status": "healthy", 
        "service": "advice_generation",
        "ai_provider": "Google Gemini",
        "version": "2.0.0"
    }

@app.post("/generate", response_model=AdviceResponse)
async def generate_advice(request: AdviceRequest):
    """
    Gemini APIを使用して検出された課題に基づいて改善アドバイスを生成する
    
    Args:
        request: 動画IDと課題リスト
        
    Returns:
        Gemini AIが生成した具体的な改善アドバイス
    """
    try:
        # デバッグログ出力
        print("=" * 80)
        print("🚀 [GEMINI ADVICE SERVICE] リクエスト受信")
        print(f"   📹 動画ID: {request.video_id}")
        print(f"   📝 課題数: {len(request.issues)}")
        
        # 堅牢処理: 課題リストの検証と修正
        valid_issues = [issue.strip() for issue in request.issues if issue and issue.strip()]
        
        if not valid_issues:
            print("   ⚠️  有効な課題が見つかりません。一般的なアドバイスを生成します。")
            valid_issues = ["ランニングフォーム全般の改善"]
        
        print(f"   ✅ 有効な課題数: {len(valid_issues)}")
        for i, issue in enumerate(valid_issues, 1):
            print(f"      {i}. {issue}")
        
        # Geminiプロンプト生成
        prompt = create_gemini_prompt(valid_issues)
        print(f"   🤖 Gemini APIにリクエスト送信中...")
        
        # Gemini APIの呼び出し
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        print(f"   📨 Gemini応答受信 (長さ: {len(ai_response)} 文字)")
        print(f"   📄 生の応答: {ai_response[:200]}...")
        
        # JSON解析
        try:
            # レスポンスからJSON部分を抽出（マークダウンなどを除去）
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                ai_response = ai_response[json_start:json_end].strip()
            elif "```" in ai_response:
                json_start = ai_response.find("```") + 3
                json_end = ai_response.rfind("```")
                ai_response = ai_response[json_start:json_end].strip()
            
            ai_data = json.loads(ai_response)
            
            if "advices" not in ai_data:
                raise ValueError("応答にadvicesキーが含まれていません")
            
            # アドバイスリストの変換
            advice_list = []
            for advice in ai_data["advices"]:
                advice_item = {
                    "issue": valid_issues[len(advice_list)] if len(advice_list) < len(valid_issues) else "その他の改善点",
                    "title": advice.get("title", "ランニングフォーム改善"),
                    "description": advice.get("description", "継続的な練習で改善を目指しましょう。"),
                    "exercise": advice.get("exercise", "日々のランニングで意識して練習してみましょう。")
                }
                advice_list.append(advice_item)
            
            print(f"   ✨ {len(advice_list)}つのアドバイスを生成しました")
            for i, advice in enumerate(advice_list, 1):
                print(f"      {i}. {advice['title']}")
        
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析エラー: {str(e)}")
            print(f"   📄 問題のある応答: {ai_response}")
            
            # フォールバック: 静的アドバイス生成
            advice_list = []
            for issue in valid_issues:
                advice_item = {
                    "issue": issue,
                    "title": "ランニングフォーム改善",
                    "description": f"検出された課題「{issue}」について、継続的な練習と意識改革で改善を目指しましょう。正しいフォームを身につけることで、より効率的で怪我のリスクが少ないランニングが可能になります。",
                    "exercise": "練習ドリル: 毎回のランニング前にフォームチェックを行い、意識的に改善ポイントを練習してみましょう。鏡の前で動きを確認したり、仲間にフォームをチェックしてもらうことも効果的です。"
                }
                advice_list.append(advice_item)
            
            print(f"   🔄 フォールバックで{len(advice_list)}つのアドバイスを生成")
        
        # 堅牢処理: アドバイスがない場合の対応
        if not advice_list:
            advice_list = [{
                "issue": "一般的なアドバイス",
                "title": "ランニングフォーム向上",
                "description": "現在のフォームを基に、継続的な改善を目指しましょう。定期的なフォームチェックと意識的な練習が上達の鍵です。",
                "exercise": "練習ドリル: 週に1回、自分のランニング動画を撮影してフォームをチェックしてみましょう。"
            }]
        
        print(f"   📊 最終的に{len(advice_list)}つのアドバイスを返却")
        print("=" * 80)
        
        return AdviceResponse(
            status="success",
            message=f"Gemini AIが{len(advice_list)}つのアドバイスを生成しました",
            advice_list=advice_list
        )
        
    except Exception as e:
        print(f"❌ [GEMINI ADVICE SERVICE] エラー発生: {str(e)}")
        print(f"   📍 エラー詳細: {type(e).__name__}")
        
        # 緊急フォールバック
        try:
            fallback_advice = [{
                "issue": "システムエラー",
                "title": "ランニング継続サポート",
                "description": "システムに一時的な問題が発生しましたが、あなたのランニングフォームの向上への取り組みは素晴らしいです。基本的なフォーム意識を継続しましょう。",
                "exercise": "練習ドリル: リラックスした姿勢で、自然なリズムを保ちながらランニングを継続してください。"
            }]
            
            return AdviceResponse(
                status="success",
                message="一時的なシステム問題により、基本的なアドバイスを提供しています",
                advice_list=fallback_advice
            )
        except:
            raise HTTPException(
                status_code=500, 
                detail=f"アドバイス生成中にエラーが発生しました: {str(e)}"
            )

@app.get("/model/info")
async def get_model_info():
    """使用しているAIモデルの情報を取得"""
    return {
        "ai_provider": "Google Gemini",
        "model": "gemini-1.5-flash-latest",
        "version": "2.0.0",
        "features": [
            "自然言語によるアドバイス生成",
            "課題に応じた個別対応",
            "実践的なエクササイズ提案",
            "ポジティブで建設的なフィードバック"
        ]
    }

@app.get("/exercises/categories")
async def get_exercise_categories():
    """エクササイズカテゴリと効果を取得（従来互換性のため残存）"""
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
            "target_issues": ["効率性", "疲労によるフォーム崩れ"],
            "example_exercises": ["インターバル走", "テンポ走", "LSD"]
        }
    }

if __name__ == "__main__":
    print("🚀 Gemini-Powered Advice Generation Service を起動中...")
    print(f"🔑 API Key: {'設定済み' if GEMINI_API_KEY else '未設定'}")
    uvicorn.run(app, host="0.0.0.0", port=8005) 