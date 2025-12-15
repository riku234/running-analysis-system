import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import re

# ==========================================
# 1. ルールベースマスタデータ（自動生成版）
# ==========================================

# 自動生成されたマスタデータをインポート
try:
    from .generated_master_data import ADVICE_MASTER_DATA
except ImportError:
    # フォールバック: 生成ファイルが存在しない場合は空の辞書を使用
    print("⚠️  generated_master_data.pyが見つかりません。空のルールセットを使用します。")
    ADVICE_MASTER_DATA = {}

# ==========================================
# 2. データモデル
# ==========================================

class DiagnosisResult(BaseModel):
    issue_id: str
    issue_name: str
    severity: str
    expert_content: Dict[str, Any]
    detected_event: str  # 検出されたイベント種別
    detected_angle: str  # 検出された角度名

# ==========================================
# 3. ルールベース診断エンジン（シンプル版）
# ==========================================

class RuleBasedAdviceEngine:
    def __init__(self, master_data: Dict = ADVICE_MASTER_DATA):
        self.master_data = master_data
    
    def _check_rule(self, rule: Dict[str, Any], z_scores: Dict[str, Dict[str, float]]) -> Optional[DiagnosisResult]:
        """
        単一のルールをチェックして、条件に合致する場合は診断結果を返す
        
        Args:
            rule: 診断ルール（マスタデータから取得）
            z_scores: Z値データ（{event_type: {angle_name: z_score}} 形式）
        
        Returns:
            診断結果（条件に合致する場合）、None（合致しない場合）
        """
        target_event = rule.get("target_event")
        target_metric = rule.get("target_metric")
        operator = rule.get("operator", "lt")
        threshold = float(rule.get("threshold", 0))
        
        # イベント種別のチェック
        events_to_check = []
        if target_event:
            # 特定のイベントのみをチェック
            events_to_check = [target_event]
        else:
            # 全イベントをチェック
            events_to_check = list(z_scores.keys())
        
        # 角度名のマッピング（英語変数名 → 実際のZ値データのキー名）
        # generated_master_data.pyで使われる英語変数名を、実際のZ値データの形式にマッピング
        angle_mapping = {
            # 英語変数名（generated_master_data.py） → 実際のZ値データのキー名（日本語 or 英語）
            "trunk_angle_z": ["体幹角度", "trunk_angle_z"],
            "shank_angle_z": ["右下腿角度", "左下腿角度", "right_shank_angle_z", "left_shank_angle_z"],
            "thigh_angle_z": ["右大腿角度", "左大腿角度", "right_thigh_angle_z", "left_thigh_angle_z"],
            "knee_angle_z": ["右大腿角度", "左大腿角度", "right_knee_angle_z", "left_knee_angle_z"],
            # 日本語名（後方互換性のため）
            "右下腿角度": ["右下腿角度", "左下腿角度", "right_shank_angle_z", "left_shank_angle_z"],
            "左下腿角度": ["右下腿角度", "左下腿角度", "right_shank_angle_z", "left_shank_angle_z"],
            "右大腿角度": ["右大腿角度", "左大腿角度", "right_thigh_angle_z", "left_thigh_angle_z"],
            "左大腿角度": ["右大腿角度", "左大腿角度", "right_thigh_angle_z", "left_thigh_angle_z"],
            "体幹角度": ["体幹角度", "trunk_angle_z"]
        }
        
        # チェック対象の角度名リスト
        # target_metricが英語変数名の場合は、左右両方をチェック
        check_angles = angle_mapping.get(target_metric, [target_metric])
        
        # 各イベントと角度をチェック
        for event_type in events_to_check:
            if event_type not in z_scores:
                continue
            
            event_scores = z_scores[event_type]
            
            for angle_name in check_angles:
                if angle_name not in event_scores:
                    continue
                
                z_score = event_scores[angle_name]
                
                if z_score is None:
                    continue
                
                # 演算子による判定
                is_hit = False
                if operator == "lt" and z_score < threshold:
                    is_hit = True
                elif operator == "gt" and z_score > threshold:
                    is_hit = True
                elif operator == "lte" and z_score <= threshold:
                    is_hit = True
                elif operator == "gte" and z_score >= threshold:
                    is_hit = True
                elif operator == "eq" and abs(z_score - threshold) < 0.01:
                    is_hit = True
                
                if is_hit:
                    return DiagnosisResult(
                        issue_id=rule.get("rule_code", ""),
                        issue_name=rule.get("content", {}).get("name", ""),
                        severity=rule.get("severity", "medium"),
                        expert_content=rule.get("content", {}),
                        detected_event=event_type,
                        detected_angle=angle_name
                    )
        
        return None
    
    def diagnose(self, z_scores: Dict[str, Dict[str, float]]) -> List[DiagnosisResult]:
        """
        Z値データからルールベース診断を実行
        
        Args:
            z_scores: Z値データ（{event_type: {angle_name: z_score}} 形式）
                     angle_nameは日本語（「体幹角度」など）または英語（「trunk_angle_z」など）の両方に対応
        
        Returns:
            診断結果のリスト
        """
        results = []
        processed_issue_ids = set()  # 同じissue_idを重複して追加しないように
        
        # 各ルールをチェック
        for issue_id, data in self.master_data.items():
            if issue_id in processed_issue_ids:
                continue
            
            # generated_master_data.pyの構造に対応
            # 構造: {"rule": {...}, "content": {...}}
            rule_data = {
                "rule_code": issue_id,
                "target_event": data.get("rule", {}).get("target_event"),
                "target_metric": data.get("rule", {}).get("target_metric"),
                "operator": data.get("rule", {}).get("operator"),
                "threshold": data.get("rule", {}).get("threshold"),
                "severity": data.get("rule", {}).get("severity"),
                "content": data.get("content", {})
            }
            
            diagnosis = self._check_rule(rule_data, z_scores)
            if diagnosis:
                results.append(diagnosis)
                processed_issue_ids.add(issue_id)
        
        return results

# ==========================================
# 4. Gemini連携機能
# ==========================================

async def generate_integrated_advice(
    z_scores: Dict[str, Dict[str, float]], 
    gemini_model: Any
) -> Dict[str, Any]:
    """
    ルールベース診断 + Gemini生成のハイブリッド方式でアドバイスを生成（シンプル版）
    
    Args:
        z_scores: Z値データ（{event_type: {angle_name: z_score}} 形式）
        gemini_model: Gemini APIモデルインスタンス
    
    Returns:
        統合アドバイスデータ
    """
    engine = RuleBasedAdviceEngine()
    diagnosed_issues = engine.diagnose(z_scores)
    
    if not diagnosed_issues:
        return {
            "status": "success",
            "ai_advice": {
                "title": "良好なフォームです",
                "message": "特筆すべき統計的な乖離は見当たりません。現在の素晴らしいフォームを維持してください。",
                "key_points": ["バランス良好"]
            },
            "raw_issues": []
        }
    
    # 専門家の見解をコンテキストとして構築
    issues_context = ""
    for idx, issue in enumerate(diagnosed_issues):
        c = issue.expert_content
        # drillアクセスの安全性向上
        drill = c.get('drill', {})
        if isinstance(drill, dict):
            drill_name = drill.get('name', '')
        else:
            drill_name = str(drill) if drill else ''
        
        issues_context += f"[課題{idx+1}:{c.get('name', '')}] 現象:{c.get('observation', '')} 原因:{c.get('cause', '')} 改善策:{c.get('action', '')} ドリル:{drill_name}\n"
    
    system_prompt = f"""
あなたはプロのランニングコーチです。以下の解析結果（専門家の見解）を元に、ランナーへのアドバイスを作成してください。

【検出課題】

{issues_context}

【重要な指示】

1. 専門家の見解（現象・原因・改善策・ドリル）をそのまま反映すること。
2. 不要な励ましの文章（「素晴らしい分析結果が出ましたね！」「一緒に一つずつクリアしていきましょう」など）は一切使用しないこと。
3. 装飾的な表現や前置きの文章は一切使用しないこと。
4. 簡潔で実践的なアドバイスにすること。
5. 専門家の見解を読みやすく整理した形式で出力すること。
6. JSON形式のみで出力すること。
7. マークダウン記法（#, *, -, **など）は一切使用しないこと。

【出力形式】

messageフィールドには、検出された各課題について、以下の形式で出力してください：

【課題名】
【現象】: （専門家の見解の現象をそのまま）
【原因】: （専門家の見解の原因をそのまま）
【改善策】: （専門家の見解の改善策をそのまま）
【ドリル】: （専門家の見解のドリル名をそのまま）

複数の課題がある場合は、課題ごとに上記の形式で出力してください。

【JSON形式】

{{
    "title": "フォーム改善アドバイス",
    "message": "上記の形式で専門家の見解を整理した内容",
    "key_points": ["課題名1", "課題名2", "課題名3"]
}}
"""
    
    try:
        # Gemini API呼び出し（非同期処理、リトライロジック付き）
        max_retries = 3
        response = None
        text = None
        
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: gemini_model.generate_content(system_prompt)
                )
                
                text = response.text
                print(f"📄 Gemini生レスポンス (長さ: {len(text)} 文字): {text[:300]}...")
                break  # 成功したらループを抜ける
                
            except Exception as api_error:
                error_str = str(api_error)
                print(f"⚠️  Gemini API呼び出しエラー (試行 {attempt + 1}/{max_retries}): {error_str[:200]}")
                
                # 429エラー（クォータ超過）の場合はリトライしない
                if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                    print(f"❌ クォータ制限に達しました。フォールバックアドバイスを使用します。")
                    raise api_error  # 例外を再発生させて、フォールバック処理に進む
                
                # その他のエラーの場合はリトライ
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2秒, 4秒, 6秒の間隔
                    print(f"⏳ {wait_time}秒待機後にリトライします...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 最大リトライ回数に達しました。フォールバックアドバイスを使用します。")
                    raise api_error  # 例外を再発生させて、フォールバック処理に進む
        
        # JSON抽出（より柔軟に）
        # 1. マークダウンコードブロックを削除
        cleaned = re.sub(r'```json\s*', '', text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()
        
        # 2. JSONオブジェクトを抽出（{...}の部分のみ）
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)
        
        # 3. 不完全な文字列を修正（最後の引用符が欠けている場合など）
        # 不完全な文字列を検出して修正
        if cleaned.count('"') % 2 != 0:
            # 引用符が奇数個の場合、最後に追加
            cleaned = cleaned.rstrip() + '"'
        
        # JSON解析
        advice_data = json.loads(cleaned)
        print(f"✅ JSON解析成功: {advice_data.get('title', 'N/A')}")
        
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON解析エラー: {e}")
        print(f"📄 問題のあるレスポンス: {text[:500] if 'text' in locals() else 'N/A'}...")
        # フォールバック: 専門家の見解から直接アドバイスを生成（読みやすい形式）
        issue_names = [i.issue_name for i in diagnosed_issues]
        
        # 専門家の見解を統合したメッセージを生成（読みやすい形式）
        message_parts = []
        for idx, issue in enumerate(diagnosed_issues, 1):
            if idx > 1:
                message_parts.append("\n\n")
            message_parts.append(f"【{issue.issue_name}】\n")
            message_parts.append(f"【現象】: {issue.expert_content.get('observation', '')}\n")
            message_parts.append(f"【原因】: {issue.expert_content.get('cause', '')}\n")
            message_parts.append(f"【改善策】: {issue.expert_content.get('action', '')}\n")
            drill = issue.expert_content.get('drill', {})
            drill_name = drill.get('name', '') if isinstance(drill, dict) else str(drill)
            if drill_name:
                message_parts.append(f"【ドリル】: {drill_name}")
        
        advice_data = {
            "title": "フォーム改善アドバイス",
            "message": "".join(message_parts),
            "key_points": issue_names[:5]  # 最大5つまで
        }
        print(f"🔄 フォールバックアドバイスを使用: {advice_data.get('title')}")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        import traceback
        traceback.print_exc()
        # フォールバック: 専門家の見解から直接アドバイスを生成（読みやすい形式）
        issue_names = [i.issue_name for i in diagnosed_issues]
        
        # 専門家の見解を統合したメッセージを生成（読みやすい形式）
        message_parts = []
        for idx, issue in enumerate(diagnosed_issues, 1):
            if idx > 1:
                message_parts.append("\n\n")
            message_parts.append(f"【{issue.issue_name}】\n")
            message_parts.append(f"【現象】: {issue.expert_content.get('observation', '')}\n")
            message_parts.append(f"【原因】: {issue.expert_content.get('cause', '')}\n")
            message_parts.append(f"【改善策】: {issue.expert_content.get('action', '')}\n")
            drill = issue.expert_content.get('drill', {})
            drill_name = drill.get('name', '') if isinstance(drill, dict) else str(drill)
            if drill_name:
                message_parts.append(f"【ドリル】: {drill_name}")
        
        advice_data = {
            "title": "フォーム改善アドバイス",
            "message": "".join(message_parts),
            "key_points": issue_names[:5]  # 最大5つまで
        }
        print(f"🔄 フォールバックアドバイスを使用: {advice_data.get('title')}")
    
    return {
        "status": "success",
        "ai_advice": advice_data,
        "raw_issues": [
            {
                "name": i.issue_name, 
                "drill": i.expert_content.get("drill", {}),
                "severity": i.severity,
                "event": i.detected_event,
                "angle": i.detected_angle
            } 
            for i in diagnosed_issues
        ]
    }
