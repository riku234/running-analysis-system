import os
import json
import time
import asyncio
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
model = genai.GenerativeModel(
    'gemini-flash-latest',
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,  # より創造的で自然な回答
        top_p=0.8,       # 多様性のバランス
        max_output_tokens=1000,  # より詳細な回答を可能に
    ),
    safety_settings=[
        {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'},
    ]
)

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

class AdvancedAdviceRequest(BaseModel):
    video_id: str
    issues_list: List[str]  # Z値判定などによって特定された課題のリスト

class AdvancedAdviceResponse(BaseModel):
    status: str
    message: str
    video_id: str
    advice: str  # フォーマットされた最終アドバイス文字列

class IntegratedAdviceRequest(BaseModel):
    video_id: str
    issues_list: List[str]  # Z値判定などによって特定された課題のリスト

class IntegratedAdviceResponse(BaseModel):
    status: str
    message: str
    video_id: str
    integrated_advice: str  # プロコーチ＋AI統合アドバイス文字列

def get_advice_database():
    """課題の組み合わせと構造化されたアドバイスのデータベース"""
    advice_db = {
        # 単一の課題に対するアドバイス
        "体幹後傾": {
            "description": "走行中に体が後ろに傾いている（後傾している）可能性があります。",
            "action": "おへそから前に引っ張られるようなイメージで、自然な前傾姿勢を意識しましょう。",
            "drill": "補強ドリルとして、壁を使った前傾姿勢の練習（ウォールドリル）が効果的です。"
        },
        "体幹前傾": {
            "description": "走行中に体が前に倒れすぎている可能性があります。",
            "action": "胸を張り、頭を上げて、自然な姿勢で走ることを意識してください。",
            "drill": "背筋を鍛える体幹トレーニングやプランクが効果的です。"
        },
        "上下動大": {
            "description": "上下の動きが大きく、エネルギーを無駄にしている可能性があります。",
            "action": "頭の位置をなるべく変えずに、前に進むことを意識してください。ピッチを少し速めると改善されることがあります。",
            "drill": "縄跳びは、リラックスして地面からの反発をもらう感覚を養うのに役立ちます。"
        },
        "ピッチ低": {
            "description": "歩数（ピッチ）が遅く、効率的でない走り方になっている可能性があります。",
            "action": "1分間に180歩程度を目標に、軽やかで素早い足の回転を意識しましょう。",
            "drill": "メトロノームやアプリを使って、一定のリズムで走る練習が効果的です。"
        },
        "ストライド長": {
            "description": "歩幅が適切でない可能性があります（長すぎるか短すぎる）。",
            "action": "無理に歩幅を広げるのではなく、自然な歩幅で効率よく走ることを心がけましょう。",
            "drill": "短い距離でのスプリント練習や、ラダートレーニングが効果的です。"
        },
        "右大腿角度大": {
            "description": "右足の大腿部の角度が大きく、オーバーストライドになっている可能性があります。",
            "action": "右足の着地位置を体の重心により近づけることを意識しましょう。",
            "drill": "右足を中心とした片足立ちバランス練習や、右脚のもも上げ運動が効果的です。"
        },
        "左大腿角度大": {
            "description": "左足の大腿部の角度が大きく、オーバーストライドになっている可能性があります。",
            "action": "左足の着地位置を体の重心により近づけることを意識しましょう。",
            "drill": "左足を中心とした片足立ちバランス練習や、左脚のもも上げ運動が効果的です。"
        },
        "右下腿角度大": {
            "description": "右足の下腿部の角度が大きく、足先着地になっている可能性があります。",
            "action": "右足全体で着地し、ミッドフット着地を意識しましょう。",
            "drill": "右足でのかかと歩きや、片足での着地練習が効果的です。"
        },
        "左下腿角度大": {
            "description": "左足の下腿部の角度が大きく、足先着地になっている可能性があります。",
            "action": "左足全体で着地し、ミッドフット着地を意識しましょう。",
            "drill": "左足でのかかと歩きや、片足での着地練習が効果的です。"
        },
        
        # 複数の課題を組み合わせたアドバイス
        "大腿角度大_下腿角度大": {
            "description": "足が体の重心よりかなり前で着地しており、ブレーキがかかりやすい走り方になっています。",
            "action": "ストライドを無理に広げるのではなく、今よりも『真下』に着地する意識を持ちましょう。",
            "drill": "その場でのもも上げや、ミニハードルを使ったドリルで、足を素早く引き上げる動きを練習しましょう。"
        },
        "体幹前傾_上下動大": {
            "description": "体が前に倒れすぎて、同時に上下動も大きくなり、エネルギー効率が悪化しています。",
            "action": "まず上体を起こして安定した姿勢を作り、その後に上下動を抑える意識を持ちましょう。",
            "drill": "体幹を鍛える基本姿勢練習と、平地でのゆっくりジョギングで感覚を掴みましょう。"
        },
        "体幹後傾_ピッチ低": {
            "description": "体が後傾し、同時にピッチも遅いため、推進力が十分に得られていません。",
            "action": "まず前傾姿勢を意識し、その姿勢のままピッチを上げる練習をしましょう。",
            "drill": "坂道での軽いジョギングや、音楽に合わせたリズム走が効果的です。"
        },
        "右大腿角度大_左大腿角度大": {
            "description": "両足ともオーバーストライドになっており、全体的に非効率な走り方になっています。",
            "action": "両足とも着地位置を体の真下に近づけ、ピッチ重視の走り方に変更しましょう。",
            "drill": "両足でのもも上げ運動と、短い歩幅での高ピッチ走練習を組み合わせましょう。"
        },
        "右下腿角度大_左下腿角度大": {
            "description": "両足とも足先での着地が多く、ふくらはぎへの負担が大きくなっています。",
            "action": "両足ともミッドフット（足の中央部）での着地を意識し、全体重を足裏で受け止めましょう。",
            "drill": "裸足でのゆっくり走りや、芝生の上での感覚重視の練習が効果的です。"
        },
        
        # 全体的なバランス改善
        "フォーム全般": {
            "description": "ランニングフォーム全般に改善の余地があり、総合的なアプローチが必要です。",
            "action": "基本的な姿勢から見直し、リラックスした状態で効率的な動きを身につけましょう。",
            "drill": "ウォーキングドリル、基本的な体幹トレーニング、ゆっくりとしたジョギングから始めましょう。"
        }
    }
    return advice_db

async def generate_detailed_advice_for_issue(issue: str, main_finding: str = None) -> dict:
    """
    個別の課題に対してGemini AIを使って詳細なアドバイスを生成する
    
    Args:
        issue: 個別の課題（例: "左下腿角度大"）
        main_finding: 根本的な課題（例: "オーバーストライド"）
        
    Returns:
        詳細なアドバイス辞書
    """
    try:
        # main_findingが指定されている場合は、より具体的なプロンプトを作成
        if main_finding:
            prompt = f"""
あなたは専門コーチです。{main_finding}の原因である「{issue}」について、プレーンテキストのみで説明してください。

重要：装飾記号は一切使用禁止です。通常の文章のみで回答してください。

説明: {issue}が{main_finding}を引き起こす理由をエネルギー効率の観点から80文字程度で説明してください。

エクササイズ: {issue}を改善する具体的な練習方法を60文字程度で提案してください。

形式例：
説明: 下腿角度が大きいと接地時にブレーキがかかり、推進力が減少してエネルギー効率が悪化します。
エクササイズ: 壁ドリルで足の引き上げを練習し、重心の真下で着地する感覚を習得しましょう。

このような通常の文章形式で回答してください。ハッシュ、アスタリスク、ハイフンなどの記号は絶対に使わないでください。
"""
        else:
            # フォールバック: 従来のプロンプト
            prompt = f"""
あなたは専門コーチです。{issue}について、プレーンテキストのみで説明してください。

重要：装飾記号は一切使用禁止です。通常の文章のみで回答してください。

説明: {issue}がランニング効率に与える影響を80文字程度で説明してください。

エクササイズ: {issue}を改善する具体的な練習方法を60文字程度で提案してください。

形式例：
説明: 下腿角度が大きいと接地時にブレーキがかかり、推進力が減少してエネルギー効率が悪化します。
エクササイズ: 壁ドリルで足の引き上げを練習し、重心の真下で着地する感覚を習得しましょう。

このような通常の文章形式で回答してください。ハッシュ、アスタリスク、ハイフンなどの記号は絶対に使わないでください。
"""

        # Gemini APIを呼び出し（レート制限対応）
        print(f"   📡 Gemini API呼び出し中... (model変数: {type(model)})")
        print(f"   📋 プロンプト: {prompt[:100]}...")
        
        # レート制限対応: 複数回リトライ
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                print(f"   📨 Gemini応答受信: {type(response)}")
                break
            except Exception as api_error:
                if "429" in str(api_error) or "quota" in str(api_error).lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10  # 10秒, 20秒, 30秒の間隔
                        print(f"   ⏳ レート制限検出、{wait_time}秒待機後にリトライ ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ 最大リトライ回数に達しました。フォールバックを使用します。")
                        raise api_error
                else:
                    raise api_error
        
        if response and hasattr(response, 'text') and response.text:
            advice_text = response.text.strip()
            print(f"   📄 Gemini個別解説レスポンス ({issue}): {advice_text[:200]}...")  # デバッグ用
            print(f"   🔍 完全なレスポンス: {repr(advice_text)}")  # 完全なレスポンスをデバッグ
            
            # マークダウン記法を徹底的に除去
            import re
            cleaned_text = advice_text
            
            # ヘッダー記法を除去（##### も含む）
            cleaned_text = re.sub(r'#{1,6}\s*', '', cleaned_text)
            
            # 強調記法を除去
            cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_text)  # **太字**
            cleaned_text = re.sub(r'\*(.*?)\*', r'\1', cleaned_text)      # *イタリック*
            
            # 区切り線を除去
            cleaned_text = re.sub(r'^-{3,}$', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^_{3,}$', '', cleaned_text, flags=re.MULTILINE)
            
            # リスト記法を除去
            cleaned_text = re.sub(r'^\s*[-*+]\s+', '', cleaned_text, flags=re.MULTILINE)
            
            # 番号付きリストを除去
            cleaned_text = re.sub(r'^\s*\d+\.\s+', '', cleaned_text, flags=re.MULTILINE)
            
            # 表記法を除去
            cleaned_text = re.sub(r'\|', '', cleaned_text)
            cleaned_text = re.sub(r':---', '', cleaned_text)
            
            # 引用記法を除去
            cleaned_text = re.sub(r'^>\s*', '', cleaned_text, flags=re.MULTILINE)
            
            # インラインコードを除去
            cleaned_text = re.sub(r'`([^`]+)`', r'\1', cleaned_text)
            
            # 改行を整理
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # レスポンスを解析して構造化
            lines = advice_text.split('\n')
            explanation = ""
            exercise = ""
            
            # 改良されたレスポンス解析
            explanation = ""
            exercise = ""
            
            # 段落ベースでの解析（クリーンなテキストを使用）
            paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
            
            # キーワードベースの分類
            explanation_lines = []
            exercise_lines = []
            current_section = "explanation"
            
            for paragraph in paragraphs:
                # セクション判定
                if any(keyword in paragraph for keyword in ['エクササイズ', '練習', 'ドリル', '運動', 'トレーニング']):
                    current_section = "exercise"
                elif any(keyword in paragraph for keyword in ['説明', '影響', '問題', '原因', '効果']):
                    current_section = "explanation"
                
                # セクション別に分類
                if current_section == "exercise":
                    exercise_lines.append(paragraph)
                else:
                    explanation_lines.append(paragraph)
            
            # 結果をまとめる
            explanation = ' '.join(explanation_lines).strip()
            exercise = ' '.join(exercise_lines).strip()
            
            # クリーンアップ
            explanation = explanation.replace('説明:', '').replace('説明：', '').strip()
            exercise = exercise.replace('エクササイズ:', '').replace('エクササイズ：', '').strip()
            
            # 最低限の品質保証（cleanedTextを使用）
            if len(explanation) < 20:  # 説明が短すぎる場合
                explanation = cleaned_text[:len(cleaned_text)//2] if cleaned_text else "この課題は走行効率に影響を与える可能性があります。"
            if len(exercise) < 15:  # エクササイズが短すぎる場合
                exercise = cleaned_text[len(cleaned_text)//2:] if cleaned_text else "基本的なフォーム練習を継続してください。"
            
            # 最終的なマークダウン除去（念のため）
            def clean_markdown_text(text):
                if not text:
                    return text
                # ヘッダー記法を除去
                text = text.replace('###', '').replace('##', '').replace('#', '')
                # 強調記法を除去
                text = text.replace('**', '').replace('*', '')
                # 区切り線を除去
                text = text.replace('---', '').replace('___', '')
                # リスト記法を除去
                text = text.replace('- ', '').replace('* ', '').replace('+ ', '')
                # 番号付きリストを除去
                import re
                text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
                # 表記法を除去
                text = text.replace('|', '')
                # 改行を整理
                text = text.replace('\n\n\n', '\n\n')
                return text.strip()
            
            explanation = clean_markdown_text(explanation)
            exercise = clean_markdown_text(exercise)
            
            print(f"   🎯 最終結果 - 説明: '{explanation[:100]}...' エクササイズ: '{exercise[:100]}...'")
            
            return {
                "issue": issue,
                "explanation": explanation or "この課題は走行効率に影響を与える可能性があります。",
                "exercise": exercise or "基本的なフォーム練習を継続してください。"
            }
        else:
            # フォールバック
            return {
                "issue": issue,
                "explanation": "この課題は走行効率に影響を与える可能性があります。",
                "exercise": "基本的なフォーム練習を継続してください。"
            }
            
    except Exception as e:
        import traceback
        print(f"   ⚠️  個別アドバイス生成エラー ({issue}): {str(e)}")
        print(f"   📍 エラー詳細: {type(e).__name__}")
        print(f"   📍 トレースバック:")
        traceback.print_exc()
        return {
            "issue": issue,
            "explanation": "この課題は走行効率に影響を与える可能性があります。",
            "exercise": "基本的なフォーム練習を継続してください。"
        }

def generate_advanced_advice(issues_list: List[str]) -> str:
    """
    複数の課題を考慮した高レベルなアドバイスを生成する
    
    Args:
        issues_list: Z値判定などによって特定された課題のリスト
        
    Returns:
        フォーマットされた最終アドバイス文字列
    """
    advice_db = get_advice_database()
    
    if not issues_list:
        # 課題がない場合は一般的なアドバイスを返す
        selected_advice = advice_db["フォーム全般"]
    else:
        # 課題の組み合わせを確認
        issues_key = "_".join(sorted(issues_list))
        
        # 複合的な課題が存在するかチェック
        if issues_key in advice_db:
            selected_advice = advice_db[issues_key]
        else:
            # 複合的な課題がない場合、優先度順で単一課題を選択
            priority_order = [
                "大腿角度大_下腿角度大", "体幹前傾_上下動大", "体幹後傾_ピッチ低",
                "右大腿角度大_左大腿角度大", "右下腿角度大_左下腿角度大",
                "体幹後傾", "体幹前傾", "上下動大", "ピッチ低", "ストライド長",
                "右大腿角度大", "左大腿角度大", "右下腿角度大", "左下腿角度大"
            ]
            
            selected_advice = None
            for priority_issue in priority_order:
                if priority_issue in issues_list and priority_issue in advice_db:
                    selected_advice = advice_db[priority_issue]
                    break
            
            # どの優先課題も見つからない場合は最初の課題を使用
            if not selected_advice and issues_list:
                first_issue = issues_list[0]
                if first_issue in advice_db:
                    selected_advice = advice_db[first_issue]
                else:
                    selected_advice = advice_db["フォーム全般"]
            
            # それでも見つからない場合は一般的なアドバイス
            if not selected_advice:
                selected_advice = advice_db["フォーム全般"]
    
    # フォーマットされたアドバイス文字列を生成
    formatted_advice = f"""--- 🏃‍♂️ ランニングフォーム改善アドバイス ---

【📊 現状のフォームについて】
{selected_advice['description']}

【🎯 改善のためのアクション】
{selected_advice['action']}

【💪 おすすめの補強ドリル】
{selected_advice['drill']}

【💡 ワンポイントアドバイス】
改善は一度に全てを変えようとせず、一つずつ段階的に取り組むことが大切です。まずは意識を変えることから始めて、徐々に体に覚えさせていきましょう。
"""
    
    return formatted_advice

def identify_main_finding(issues_list: List[str]) -> str:
    """
    課題リストから根本的な問題を特定する
    
    Args:
        issues_list: 検出された課題のリスト
        
    Returns:
        根本課題の名称
    """
    # 大腿角度大や下腿角度大が複数ある場合はオーバーストライド
    thigh_calf_issues = [issue for issue in issues_list if "大腿角度大" in issue or "下腿角度大" in issue]
    if len(thigh_calf_issues) >= 2:
        return "オーバーストライド"
    
    # 体幹関連の問題がある場合
    trunk_issues = [issue for issue in issues_list if "体幹" in issue]
    if trunk_issues:
        if "体幹後傾" in trunk_issues:
            return "体幹後傾フォーム"
        elif "体幹前傾" in trunk_issues:
            return "体幹前傾フォーム"
        else:
            return "体幹姿勢の問題"
    
    # 上下動やピッチの問題
    if "上下動大" in issues_list:
        return "エネルギー効率の低下"
    
    if "ピッチ低" in issues_list:
        return "ピッチ不足"
    
    # その他の場合は一般的な表現
    if issues_list:
        return "ランニングフォームの効率性"
    else:
        return "フォーム全般"

async def generate_integrated_advice(issues_list: List[str]) -> str:
    """
    プロコーチアドバイス（データベース）とGemini AI詳細アドバイスを統合する
    
    Args:
        issues_list: Z値判定などによって特定された課題のリスト
        
    Returns:
        統合された最終アドバイス文字列
    """
    try:
        print(f"   🔄 統合アドバイス生成開始 - 課題数: {len(issues_list)}")
        
        # 1. 根本課題（main_finding）を特定
        main_finding = identify_main_finding(issues_list)
        print(f"   🎯 根本課題特定: {main_finding}")
        
        # 2. プロコーチアドバイスを生成
        coach_advice = generate_advanced_advice(issues_list)
        print(f"   ✅ プロコーチアドバイス生成完了")
        
        # 3. 個別課題の詳細アドバイスをAIで生成（根本課題を関連付け）
        detailed_advices = []
        for issue in issues_list:
            if issue and issue.strip():
                print(f"   🤖 AI詳細アドバイス生成中: {issue.strip()}")
                try:
                    # Gemini APIを使用してより詳細なアドバイスを生成
                    detailed_advice = await generate_detailed_advice_for_issue(issue.strip(), main_finding)
                    detailed_advices.append(detailed_advice)
                    print(f"   ✅ AI詳細アドバイス生成完了: {issue.strip()}")
                except Exception as ai_error:
                    print(f"   ⚠️ AI詳細アドバイス生成失敗: {ai_error}, フォールバック使用")
                    # AIアドバイス生成に失敗した場合はフォールバック
                    detailed_advice = {
                        "issue": issue.strip(),
                        "explanation": "この課題は走行効率に影響を与える可能性があります。",
                        "exercise": "基本的なフォーム練習を継続してください。"
                    }
                    detailed_advices.append(detailed_advice)
        
        print(f"   ✅ 個別詳細アドバイス生成完了 - {len(detailed_advices)}件")
        
        # 4. 統合されたアドバイスを組み立て
        integrated_text = f"""{coach_advice}

【個別課題の詳細解説】"""
        
        for i, advice in enumerate(detailed_advices, 1):
            issue_name = advice['issue']
            explanation = advice['explanation']
            exercise = advice['exercise']
            
            # マークダウンを最終的に除去
            def final_clean_markdown(text):
                if not text:
                    return text
                import re
                
                # ヘッダー記法を徹底的に除去
                text = re.sub(r'#{1,6}\s*', '', text)
                
                # 強調記法を除去（太字・イタリック）
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **太字**
                text = re.sub(r'\*(.*?)\*', r'\1', text)      # *イタリック*
                text = re.sub(r'__(.*?)__', r'\1', text)      # __太字__
                text = re.sub(r'_(.*?)_', r'\1', text)        # _イタリック_
                
                # 区切り線を除去
                text = re.sub(r'^-{3,}.*$', '', text, flags=re.MULTILINE)
                text = re.sub(r'^_{3,}.*$', '', text, flags=re.MULTILINE)
                text = re.sub(r'^\*{3,}.*$', '', text, flags=re.MULTILINE)
                
                # リスト記法を除去
                text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
                
                # 番号付きリストを除去
                text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
                
                # 表記法を徹底的に除去
                text = re.sub(r'\|.*?\|', '', text)  # |テーブル|
                text = re.sub(r'\|', '', text)
                text = re.sub(r':---:?', '', text)
                text = re.sub(r'---:', '', text)
                
                # 引用記法を除去
                text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
                
                # インラインコードを除去
                text = re.sub(r'`([^`]+)`', r'\1', text)
                
                # コードブロックを除去
                text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
                
                # 残りの記号を除去
                text = re.sub(r'[#*_`~]', '', text)
                
                # 改行を整理
                text = re.sub(r'\n{3,}', '\n\n', text)
                
                return text.strip()
            
            explanation = final_clean_markdown(explanation)
            exercise = final_clean_markdown(exercise)
            
            # テキスト重複の防止: exerciseが「推奨」で始まる場合は「推奨エクササイズ: 」を追加しない
            if exercise.strip().startswith('推奨'):
                exercise_display = f"   {exercise}"
            else:
                exercise_display = f"   推奨エクササイズ: {exercise}"
            
            integrated_text += f"""

{i}. {issue_name}
   詳細: {explanation}
{exercise_display}"""
        
        integrated_text += """

【総合的な改善のポイント】
改善は段階的に取り組むことが重要です。まずは全体的なフォーム意識から始めて、個別の課題に順次対処していくことで、より効果的なランニングフォームを身につけることができます。"""
        
        # 最終的に統合テキスト全体からマークダウンを除去
        import re
        def complete_markdown_removal(text):
            if not text:
                return text
                
            # ヘッダー記法を除去
            text = re.sub(r'#{1,6}\s*', '', text)
            
            # 強調記法を除去
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **太字**
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # *イタリック*
            text = re.sub(r'__(.*?)__', r'\1', text)      # __太字__
            text = re.sub(r'_(.*?)_', r'\1', text)        # _イタリック_
            
            # 区切り線を除去
            text = re.sub(r'^-{3,}.*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^_{3,}.*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\*{3,}.*$', '', text, flags=re.MULTILINE)
            
            # リスト記法を除去
            text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
            
            # 番号付きリストを除去
            text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
            
            # 表記法を徹底的に除去
            text = re.sub(r'\|.*?\|.*?\|', '', text)  # |列1|列2|列3|形式
            text = re.sub(r'\|.*?\|', '', text)       # |列1|列2|形式
            text = re.sub(r'\|[^|\n]*', '', text)     # |で始まる行
            text = re.sub(r'[^|\n]*\|', '', text)     # |で終わる行
            text = re.sub(r'\|', '', text)            # 残った|
            text = re.sub(r':---:?', '', text)
            text = re.sub(r'---:', '', text)
            
            # コードブロックを除去
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            
            # 残りの記号を除去
            text = re.sub(r'[#*_`~]', '', text)
            
            # 改行を整理
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
        
        integrated_text = complete_markdown_removal(integrated_text)
        
        print(f"   🎯 統合アドバイス生成完了 (長さ: {len(integrated_text)} 文字)")
        return integrated_text
        
    except Exception as e:
        print(f"   ❌ 統合アドバイス生成エラー: {str(e)}")
        # フォールバック: プロコーチアドバイスのみ返却
        return generate_advanced_advice(issues_list)

def create_gemini_prompt(issues: List[str]) -> str:
    """Gemini APIに送信するプロンプトを生成"""
    issues_text = "\n".join([f"- {issue}" for issue in issues])
    
    prompt = f"""あなたは、スポーツ科学に基づくランニングフォーム分析の専門家であり、世界トップクラスのランニングコーチです。

ランニングフォーム分析において以下の課題が検出されました。各課題について、詳細で実践的なアドバイスを生成してください。

【検出された課題】:
{issues_text}

【重要】マークダウン記法は一切使用せず、以下の要求に従って、必ずJSON形式の文字列"のみ"を返してください。```jsonなどのマークダウンは一切含めないでください。

{{
  "advices": [
    {{
      "title": "（課題名に基づいた改善タイトル）",
      "description": "（課題の具体的影響と改善必要性を80-120文字で詳細に説明。なぜ問題なのか、放置した場合のリスク、改善メリットを含める。プレーンテキストのみ）",
      "exercise": "（改善のための具体的なエクササイズ・練習方法を60-80文字で説明。実施方法、回数、頻度を含める。プレーンテキストのみ）"
    }}
  ]
}}

要求事項:
- 各課題に対して1つのアドバイスを生成
- 角度の問題（左下腿角度大など）では、バイオメカニクス的な影響を説明
- 説明部分は走行効率、怪我リスク、エネルギー消費への影響を含める
- エクササイズは初心者でも実践できる具体的な方法を提示
- 医学的・科学的根拠に基づいた内容で
- ポジティブで励ましの要素を含める
- マークダウン記法（#, *, -, **など）は絶対に使用しない
- JSON形式以外は一切出力しない"""
    
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
        
        # Gemini APIの呼び出し（レート制限対応）
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                ai_response = response.text.strip()
                break
            except Exception as api_error:
                if "429" in str(api_error) or "quota" in str(api_error).lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5秒, 10秒, 15秒の間隔
                        print(f"   ⏳ レート制限検出、{wait_time}秒待機後にリトライ ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ 最大リトライ回数に達しました。フォールバックを使用します。")
                        # フォールバック処理を開始
                        ai_response = ""
                        break
                else:
                    raise api_error
        
        if not response or not hasattr(response, 'text') or not response.text:
            ai_response = ""
        
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
        "model": "gemini-flash-latest",
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

@app.post("/generate-advanced", response_model=AdvancedAdviceResponse)
async def generate_advanced_advice_endpoint(request: AdvancedAdviceRequest):
    """
    プロのコーチレベルの高度なアドバイスを生成する
    
    Args:
        request: 動画IDと課題リスト
        
    Returns:
        複数の課題を組み合わせた構造化された高レベルアドバイス
    """
    try:
        # デバッグログ出力
        print("=" * 80)
        print("🎯 [ADVANCED ADVICE SERVICE] 高レベルアドバイスリクエスト受信")
        print(f"   📹 動画ID: {request.video_id}")
        print(f"   📝 課題数: {len(request.issues_list)}")
        
        # 課題リストの検証と前処理
        valid_issues = [issue.strip() for issue in request.issues_list if issue and issue.strip()]
        
        print(f"   ✅ 有効な課題数: {len(valid_issues)}")
        for i, issue in enumerate(valid_issues, 1):
            print(f"      {i}. {issue}")
        
        # 高レベルアドバイス生成
        print(f"   🧠 高レベルアドバイス生成中...")
        advanced_advice = generate_advanced_advice(valid_issues)
        
        print(f"   📨 高レベルアドバイス生成完了 (長さ: {len(advanced_advice)} 文字)")
        print(f"   📄 アドバイス概要: {advanced_advice[:100]}...")
        print("=" * 80)
        
        return AdvancedAdviceResponse(
            status="success",
            message=f"プロレベルの構造化アドバイスを生成しました",
            video_id=request.video_id,
            advice=advanced_advice
        )
        
    except Exception as e:
        print(f"❌ [ADVANCED ADVICE SERVICE] エラー発生: {str(e)}")
        print(f"   📍 エラー詳細: {type(e).__name__}")
        
        # フォールバックアドバイス
        try:
            fallback_advice = generate_advanced_advice([])  # 一般的なアドバイスを生成
            
            return AdvancedAdviceResponse(
                status="success",
                message="システム問題により一般的なアドバイスを提供しています",
                video_id=request.video_id,
                advice=fallback_advice
            )
        except:
            raise HTTPException(
                status_code=500, 
                       detail=f"高レベルアドバイス生成中にエラーが発生しました: {str(e)}"
                   )

@app.post("/generate-integrated", response_model=IntegratedAdviceResponse)
async def generate_integrated_advice_endpoint(request: IntegratedAdviceRequest):
    """
    プロコーチアドバイス（データベース）とGemini AI詳細アドバイスを統合する
    
    Args:
        request: 動画IDと課題リスト
        
    Returns:
        プロコーチ＋AI統合アドバイス
    """
    try:
        print("=" * 80)
        print("🎯 [INTEGRATED ADVICE SERVICE] 統合アドバイスリクエスト受信")
        print(f"   📹 動画ID: {request.video_id}")
        print(f"   📝 課題数: {len(request.issues_list)}")
        
        valid_issues = [issue.strip() for issue in request.issues_list if issue and issue.strip()]
        
        print(f"   ✅ 有効な課題数: {len(valid_issues)}")
        for i, issue in enumerate(valid_issues, 1):
            print(f"      {i}. {issue}")
        
        print(f"   🧠 統合アドバイス生成中...")
        integrated_advice = await generate_integrated_advice(valid_issues)
        
        print(f"   📨 統合アドバイス生成完了 (長さ: {len(integrated_advice)} 文字)")
        print(f"   📄 アドバイス概要: {integrated_advice[:100]}...")
        print("=" * 80)
        
        return IntegratedAdviceResponse(
            status="success",
            message=f"プロコーチ＋AI統合アドバイスを生成しました",
            video_id=request.video_id,
            integrated_advice=integrated_advice
        )
        
    except Exception as e:
        print(f"❌ [INTEGRATED ADVICE SERVICE] エラー発生: {str(e)}")
        print(f"   📍 エラー詳細: {type(e).__name__}")
        
        try:
            fallback_advice = generate_advanced_advice([])
            
            return IntegratedAdviceResponse(
                status="success",
                message="システム問題により基本的なアドバイスを提供しています",
                video_id=request.video_id,
                integrated_advice=fallback_advice
            )
        except:
            raise HTTPException(
                status_code=500, 
                detail=f"統合アドバイス生成中にエラーが発生しました: {str(e)}"
            )

if __name__ == "__main__":
    print("🚀 Gemini-Powered Advice Generation Service を起動中...")
    print(f"🔑 API Key: {'設定済み' if GEMINI_API_KEY else '未設定'}")
    uvicorn.run(app, host="0.0.0.0", port=8005) 