from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import aiofiles
from pathlib import Path
import uuid
import re
from datetime import datetime
import httpx
import asyncio
import logging
import json
from typing import Optional
import sys

# db_utils.pyをインポート
sys.path.append('/app')
from db_utils import (
    create_run_record,
    save_keypoints_data,
    save_events_data,
    save_analysis_results,
    update_run_status
)

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# アップロードディレクトリの設定
UPLOAD_DIRECTORY = Path("uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

# サービスURL設定
POSE_ESTIMATION_URL = "http://pose_estimation:8002/estimate"
FEATURE_EXTRACTION_URL = "http://feature_extraction:8003/extract"
ANALYSIS_URL = "http://analysis:8004/analyze-z-score"
ADVICE_GENERATION_URL = "http://advice_generation:8005/generate"

app = FastAPI(
    title="Video Processing Service",
    description="動画のアップロード、フォーマット変換、フレーム抽出を担当するサービス",
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

# アップロードディレクトリの設定
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def health_check():
    """サービスヘルスチェック"""
    return {"status": "healthy", "service": "video_processing"}

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    prompt_settings: Optional[str] = Form(None)
):
    """
    動画ファイルをアップロードして解析パイプラインを実行する（堅牢版）
    
    Args:
        file: アップロードされた動画ファイル
        prompt_settings: カスタムプロンプト設定（JSON文字列、任意）
        
    Returns:
        解析結果またはエラー情報
    """
    try:
        # ファイル形式の検証
        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
            )
        
        # ファイルサイズの制限（例：500MB）
        file_size = 0
        temp_content = await file.read()
        file_size = len(temp_content)
        
        max_size = 500 * 1024 * 1024  # 500MB
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズが大きすぎます（最大500MB）"
            )
        
        # ファイルを元の位置にリセット
        await file.seek(0)
        
        # 一意のファイル名を生成
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{unique_id}{file_extension}"
        file_path = UPLOAD_DIR / safe_filename
        
        # ファイルを保存
        async with aiofiles.open(file_path, 'wb') as buffer:
            await buffer.write(temp_content)
        
        logger.info(f"ファイルアップロード完了: {safe_filename} ({file_size} bytes)")
        
        # アップロード情報
        upload_data = {
            "file_id": unique_id,
            "original_filename": file.filename,
            "saved_filename": safe_filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "upload_timestamp": datetime.now().isoformat(),
            "file_extension": file_extension
        }
        
        # プロンプト設定の解析と検証
        logger.info(f"🎯 プロンプト設定受信チェック: prompt_settings={prompt_settings}")
        logger.info(f"🎯 プロンプト設定タイプ: {type(prompt_settings)}")
        parsed_prompt_settings = None
        if prompt_settings:
            try:
                parsed_prompt_settings = json.loads(prompt_settings)
                logger.info(f"✅ カスタムプロンプト設定受信成功: {list(parsed_prompt_settings.keys())}")
                logger.info(f"   コーチングスタイル: {parsed_prompt_settings.get('coaching_style', 'デフォルト')}")
                logger.info(f"   詳細レベル: {parsed_prompt_settings.get('advice_detail_level', 'デフォルト')}")
                logger.info(f"   カスタムプロンプト使用: {parsed_prompt_settings.get('use_custom_prompt', False)}")
                if parsed_prompt_settings.get('use_custom_prompt', False):
                    custom_prompt = parsed_prompt_settings.get('custom_prompt', '')
                    logger.info(f"   📝 カスタムプロンプト長: {len(custom_prompt)} 文字")
                    logger.info(f"   📝 カスタムプロンプト概要: {custom_prompt[:100]}...")
            except json.JSONDecodeError as e:
                logger.warning(f"❌ プロンプト設定のJSON解析エラー: {e}")
                parsed_prompt_settings = None
        else:
            logger.info("📝 デフォルトプロンプト設定を使用（prompt_settings is None)")
        
        
        # 全サービス連携処理（堅牢版）
        async with httpx.AsyncClient() as client:
            try:
                # Step 1: 骨格推定
                logger.info("骨格推定サービスを呼び出します")
                pose_request = {
                    "video_path": f"uploads/{safe_filename}",
                    "confidence_threshold": 0.5
                }
                
                pose_response = await client.post(
                    POSE_ESTIMATION_URL,
                    json=pose_request,
                    timeout=300.0  # 5分のタイムアウト
                )
                pose_response.raise_for_status()
                pose_data = pose_response.json()
                logger.info("骨格推定完了")
                
                # Step 2: 特徴量計算
                logger.info("特徴量計算サービスを呼び出します")
                feature_request = {
                    "pose_data": pose_data.get("pose_data", []),
                    "video_info": pose_data.get("video_info", {})
                }
                
                feature_response = await client.post(
                    FEATURE_EXTRACTION_URL,
                    json=feature_request,
                    timeout=120.0  # 2分のタイムアウト
                )
                feature_response.raise_for_status()
                feature_data = feature_response.json()
                logger.info("特徴量計算完了")
                
                # Step 3: Z値分析
                logger.info("Z値分析サービスを呼び出します")
                analysis_request = {
                    "keypoints_data": pose_data.get("pose_data", []),
                    "video_fps": pose_data.get("video_info", {}).get("fps", 30.0)
                }
                
                analysis_response = await client.post(
                    ANALYSIS_URL,
                    json=analysis_request,
                    timeout=120.0  # 2分のタイムアウト（Z値分析は時間がかかる可能性）
                )
                analysis_response.raise_for_status()
                z_score_data = analysis_response.json()
                logger.info("Z値分析完了")
                
                # Z値分析結果から課題を抽出
                issue_data = {
                    "status": "success",
                    "issues": [],
                    "analysis_details": {
                        "total_issues": 0,
                        "analysis_method": "z_score_analysis"
                    }
                }
                
                # 有意な偏差を課題として変換
                if z_score_data.get("analysis_summary", {}).get("significant_deviations"):
                    issues = []
                    for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
                        event_names = {
                            'right_strike': '右足接地',
                            'right_off': '右足離地',
                            'left_strike': '左足接地',
                            'left_off': '左足離地'
                        }
                        event_name = event_names.get(deviation["event"], deviation["event"])
                        severity = "高" if deviation["severity"] == "high" else "中"
                        
                        issue_text = f"{event_name}時の{deviation['angle']}が標準から大きく外れています（Z値: {deviation['z_score']:.2f}, 重要度: {severity}）"
                        issues.append(issue_text)
                    
                    issue_data["issues"] = issues
                    issue_data["analysis_details"]["total_issues"] = len(issues)
                
                # Step 4: アドバイス生成（従来のGemini AI + 新しい高レベルアドバイス）
                try:
                    logger.info("アドバイス生成サービス（Gemini AI）を呼び出します")
                    advice_request = {
                        "video_id": unique_id,
                        "issues": issue_data.get("issues", [])
                    }
                    
                    # カスタムプロンプト設定を追加
                    if parsed_prompt_settings:
                        advice_request["prompt_settings"] = parsed_prompt_settings
                    
                    advice_response = await client.post(
                        ADVICE_GENERATION_URL,
                        json=advice_request,
                        timeout=60.0
                    )
                    advice_response.raise_for_status()
                    advice_data = advice_response.json()
                    logger.info("Gemini AIアドバイス生成完了")
                    
                    # 統合アドバイス生成を追加
                    logger.info("統合アドバイス生成サービスを呼び出します")
                    
                    # Z値分析結果から課題を抽出（統合アドバイス用）
                    high_level_issues = []
                    if z_score_data and z_score_data.get("analysis_summary", {}).get("significant_deviations"):
                        for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
                            # 角度名を簡略化（例: "右大腿角度" -> "右大腿角度大"）
                            angle_mapping = {
                                "右大腿角度": "右大腿角度大",
                                "左大腿角度": "左大腿角度大", 
                                "右下腿角度": "右下腿角度大",
                                "左下腿角度": "左下腿角度大",
                                "体幹角度": "体幹後傾" if deviation["z_score"] < 0 else "体幹前傾"
                            }
                            
                            mapped_issue = angle_mapping.get(deviation["angle"], deviation["angle"])
                            if mapped_issue not in high_level_issues:
                                high_level_issues.append(mapped_issue)
                    
                    integrated_advice_request = {
                        "video_id": unique_id,
                        "issues_list": high_level_issues
                    }
                    
                    # カスタムプロンプト設定を統合アドバイスにも追加
                    if parsed_prompt_settings:
                        integrated_advice_request["prompt_settings"] = parsed_prompt_settings
                    
                    integrated_advice_response = await client.post(
                        f"http://advice_generation:8005/generate-integrated",
                        json=integrated_advice_request,
                        timeout=90.0  # 統合処理のため時間を延長
                    )
                    integrated_advice_response.raise_for_status()
                    integrated_advice_data = integrated_advice_response.json()
                    logger.info("統合アドバイス生成完了")
                    
                    # デバッグログ: 統合アドバイスデータの内容確認
                    logger.info(f"統合アドバイスデータ: {integrated_advice_data}")
                    logger.info(f"抽出された課題: {high_level_issues}")
                    
                    # アドバイスデータに統合アドバイスを追加
                    advice_data["integrated_advice"] = integrated_advice_data.get("integrated_advice", "")
                    advice_data["advanced_advice"] = integrated_advice_data.get("integrated_advice", "")  # 後方互換性
                    advice_data["high_level_issues"] = high_level_issues
                    
                    # デバッグログ: 最終的なadvice_dataの確認
                    logger.info(f"最終advice_dataに統合アドバイス追加: {bool(advice_data.get('integrated_advice'))}")
                    
                except Exception as e:
                    logger.warning(f"アドバイス生成でエラーが発生しましたが、処理を続行します: {e}")
                    # アドバイス生成に失敗した場合は空の結果をセット
                    advice_data = {
                        "status": "error",
                        "message": "アドバイス生成に失敗しました",
                        "video_id": unique_id,
                        "advice_list": [],
                        "summary": {
                            "total_issues": 0,
                            "total_advice": 0,
                            "generation_timestamp": ""
                        }
                    }
                
                # Step 5: 成功レスポンスの返却
                response_data = {
                    "status": "success",
                    "message": "動画アップロード、骨格解析、特徴量計算、課題分析が完了しました",
                    "upload_info": upload_data,
                    "pose_analysis": pose_data,
                    "feature_analysis": feature_data,
                    "issue_analysis": issue_data,
                    "advice_results": advice_data  # 必ずadvice_resultsキーを含める
                }
                
                if advice_data and advice_data.get("status") == "success":
                    response_data["advice_analysis"] = advice_data  # 後方互換性のため
                    response_data["message"] += "、アドバイス生成も完了しました"
                else:
                    response_data["message"] += "、アドバイス生成でエラーが発生しました"
                
                # ★★★ デバッグログ: フロントエンドに返却する最終レスポンスを出力 ★★★
                print("=" * 80)
                print("📤 [VIDEO PROCESSING SERVICE] フロントエンドに返却する最終レスポンス:")
                print(f"   - ステータス: {response_data.get('status')}")
                print(f"   - メッセージ: {response_data.get('message')}")
                print(f"   - アップロード情報: {'✅' if response_data.get('upload_info') else '❌'}")
                print(f"   - 骨格解析データ: {'✅' if response_data.get('pose_analysis') else '❌'}")
                print(f"   - 特徴量データ: {'✅' if response_data.get('feature_analysis') else '❌'}")
                print(f"   - 課題分析データ: {'✅' if response_data.get('issue_analysis') else '❌'}")
                print(f"   - アドバイスデータ: {'✅' if response_data.get('advice_analysis') else '❌'}")
                
                if response_data.get('issue_analysis'):
                    issues = response_data['issue_analysis'].get('issues', [])
                    print(f"   - 検出された課題数: {len(issues)}")
                    for i, issue in enumerate(issues[:3], 1):  # 最初の3つだけ表示
                        print(f"     {i}. {issue[:50]}...")
                
                if response_data.get('advice_analysis'):
                    advice_list = response_data['advice_analysis'].get('advice_list', [])
                    print(f"   - 生成されたアドバイス数: {len(advice_list)}")
                    for i, advice in enumerate(advice_list[:3], 1):  # 最初の3つだけ表示
                        print(f"     {i}. {advice.get('title', 'N/A')}")
                
                print("=" * 80)
                
                # ======================================================================
                # データベースへの保存処理
                # ======================================================================
                try:
                    logger.info("💾 データベースへの保存を開始します...")
                    
                    # 1. ユーザーIDの設定（デフォルトユーザー）
                    user_id = "default_user"  # 実際のユーザー認証機能があれば、そこから取得
                    
                    # 2. 走行記録の作成
                    video_info = pose_data.get("video_info", {})
                    run_id = create_run_record(
                        video_id=unique_id,
                        user_id=user_id,
                        video_path=str(file_path),
                        original_filename=file.filename,
                        video_fps=video_info.get("fps"),
                        video_duration=video_info.get("duration"),
                        total_frames=video_info.get("total_frames")
                    )
                    
                    if run_id:
                        logger.info(f"✅ 走行記録を作成しました: run_id={run_id}")
                        
                        # 3. キーポイントデータの保存
                        pose_data_list = pose_data.get("pose_data", [])
                        if pose_data_list:
                            success = save_keypoints_data(run_id, pose_data_list)
                            if success:
                                logger.info(f"✅ キーポイントデータを保存しました")
                        
                        # 4. イベントデータの保存（もし存在すれば）
                        events = issue_data.get("events_detected", [])
                        if events:
                            success = save_events_data(run_id, events)
                            if success:
                                logger.info(f"✅ イベントデータを保存しました")
                        
                        # 5. 解析結果の保存
                        # Z値スコアを抽出
                        results_to_save = {}
                        z_scores = issue_data.get("z_scores", {})
                        for event_type, scores in z_scores.items():
                            for angle_name, z_value in scores.items():
                                metric_name = f"Z値_{event_type}_{angle_name}"
                                results_to_save[metric_name] = z_value
                        
                        # イベント角度も保存
                        event_angles = issue_data.get("event_angles", {})
                        for event_type, angles in event_angles.items():
                            for angle_name, angle_value in angles.items():
                                metric_name = f"角度_{event_type}_{angle_name}"
                                results_to_save[metric_name] = angle_value
                        
                        if results_to_save:
                            success = save_analysis_results(run_id, results_to_save)
                            if success:
                                logger.info(f"✅ 解析結果を保存しました")
                        
                        # 6. ステータスを完了に更新
                        update_run_status(run_id, 'completed')
                        logger.info("✅ 全てのデータをデータベースに保存しました")
                        
                        # レスポンスにrun_idを追加
                        response_data["run_id"] = run_id
                    else:
                        logger.warning("⚠️  データベースへの保存に失敗しましたが、処理は続行します")
                        
                except Exception as db_error:
                    logger.error(f"❌ データベース保存エラー: {db_error}")
                    logger.error("データベースへの保存に失敗しましたが、処理結果は返却します")
                    # データベースエラーが発生しても、解析結果は返却する
                
                # ======================================================================
                
                print("=" * 80)
                
                return response_data
                
            except httpx.RequestError as exc:
                # ネットワークエラー（接続失敗、タイムアウトなど）
                logger.error(f"サービス接続エラー: {exc}")
                raise HTTPException(
                    status_code=503,
                    detail=f"解析サービスに接続できません。しばらく待ってから再度お試しください。"
                )
                
            except httpx.HTTPStatusError as exc:
                # HTTPエラーレスポンス（4xx, 5xx）
                logger.error(f"サービスエラー: {exc.response.status_code} - {exc.response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"解析中にサーバーエラーが発生しました。管理者にお問い合わせください。"
                )
                
            except Exception as exc:
                # その他の予期しないエラー
                logger.error(f"予期しないエラー: {exc}")
                raise HTTPException(
                    status_code=500,
                    detail="予期しないサーバーエラーが発生しました。管理者にお問い合わせください。"
                )
        
    except HTTPException:
        # 既にHTTPExceptionの場合はそのまま再発生
        raise
        
    except Exception as exc:
        # ファイル操作やその他の例外
        logger.error(f"アップロード処理でエラー: {exc}")
        raise HTTPException(
            status_code=500,
            detail="ファイルのアップロード処理中にエラーが発生しました。"
        )

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    """
    動画ファイルを受け取り、前処理を実行する
    
    Args:
        file: アップロードされた動画ファイル
        
    Returns:
        処理結果とフレーム抽出情報
    """
    # TODO: 動画ファイルの形式チェック
    # TODO: 動画フォーマット変換（mp4, avi → 標準形式）
    # TODO: フレーム抽出（1秒間に30フレーム等）
    # TODO: フレームの前処理（リサイズ、正規化）
    # TODO: 処理済みファイルの保存
    
    # ダミーレスポンス
    return {
        "status": "success",
        "message": "動画処理が完了しました",
        "video_id": "dummy_video_123",
        "original_filename": file.filename,
        "processed_frames_count": 300,
        "frame_rate": 30,
        "duration_seconds": 10.0,
        "resolution": {"width": 1920, "height": 1080}
    }

@app.get("/status/{video_id}")
async def get_processing_status(video_id: str):
    """
    動画処理の進捗状況を取得する
    
    Args:
        video_id: 処理中の動画ID
        
    Returns:
        処理進捗情報
    """
    # TODO: 実際の処理状況をデータベースから取得
    
    return {
        "video_id": video_id,
        "status": "completed",
        "progress_percent": 100,
        "current_step": "frame_extraction",
        "estimated_remaining_time": 0
    }

@app.get("/stream/{filename}")
async def stream_video(filename: str):
    """
    保存された動画ファイルをストリーミング配信する
    
    Args:
        filename: ストリーミングする動画ファイル名 (UUIDも可)
        
    Returns:
        動画ファイルのレスポンス
    """
    file_path = UPLOAD_DIR / filename
    
    # ファイルが存在しない場合、UUIDでの検索を試行
    if not file_path.exists():
        # UUIDパターンを検出（8-4-4-4-12形式）
        uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        
        if re.match(uuid_pattern, filename.replace('.mp4', '').replace('.mov', '')):
            # UUIDが含まれている場合、そのUUIDを含むファイルを検索
            uuid_part = re.search(uuid_pattern, filename).group(0)
            
            for file in UPLOAD_DIR.glob(f"*{uuid_part}*"):
                if file.is_file() and file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                    file_path = file
                    logger.info(f"UUIDによるファイル検索成功: {filename} -> {file_path.name}")
                    break
    
    if not file_path.exists():
        logger.error(f"動画ファイルが見つかりません: {filename}")
        raise HTTPException(
            status_code=404,
            detail="指定された動画ファイルが見つかりません"
        )
    
    # ファイルが動画形式かチェック
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
    if file_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="指定されたファイルは動画形式ではありません"
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename
    )

@app.get("/result/{video_id}")
async def get_result(video_id: str):
    """
    指定されたvideo_idの解析結果を取得する
    """
    try:
        # 保存されたファイルを探す
        for file_path in UPLOAD_DIRECTORY.glob(f"*{video_id}*"):
            if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                # 動画ファイルが存在する場合、解析を実行
                logger.info(f"動画ファイルが見つかりました: {file_path}")
                
                # 完全な解析パイプラインを実行（upload_videoと同じロジック）
                logger.info("完全な解析パイプラインを開始します")
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    # Step 1: 骨格推定
                    logger.info("骨格推定を実行中...")
                    pose_request = {
                        "video_path": str(file_path),
                        "confidence_threshold": 0.5
                    }
                    pose_response = await client.post(POSE_ESTIMATION_URL, json=pose_request)
                    pose_response.raise_for_status()
                    pose_data = pose_response.json()
                    
                    # Step 2: 特徴量抽出
                    logger.info("特徴量抽出を実行中...")
                    feature_request = {
                        "pose_data": pose_data["pose_data"],
                        "video_info": pose_data["video_info"]
                    }
                    feature_response = await client.post(FEATURE_EXTRACTION_URL, json=feature_request)
                    feature_response.raise_for_status()
                    feature_data = feature_response.json()
                    
                    # Step 3: Z値分析（新しい統計ベース分析）
                    logger.info("Z値分析を実行中...")
                    logger.info(f"📊 pose_data keys: {list(pose_data.keys())}")
                    logger.info(f"📊 pose_data['pose_data'] length: {len(pose_data.get('pose_data', []))}")
                    z_score_request = {
                        "keypoints_data": pose_data["pose_data"],
                        "video_fps": pose_data["video_info"]["fps"]
                    }
                    logger.info(f"📊 Z値分析リクエスト - keypoints_data length: {len(z_score_request['keypoints_data'])}, fps: {z_score_request['video_fps']}")
                    z_score_response = await client.post(ANALYSIS_URL, json=z_score_request)
                    z_score_response.raise_for_status()
                    z_score_data = z_score_response.json()
                    
                    # 課題分析データを準備
                    issue_data = {
                        "status": "success",
                        "message": f"フォーム分析完了：{len(z_score_data.get('analysis_summary', {}).get('significant_deviations', []))}つの改善点を検出しました",
                        "issues": [],
                        "analysis_details": {
                            "analyzed_metrics": {},
                            "total_issues": 0,
                            "overall_assessment": f"{len(z_score_data.get('analysis_summary', {}).get('significant_deviations', []))}つの改善点が見つかりました",
                            "analysis_method": "z_score_analysis"
                        }
                    }
                    
                    # Z値分析結果から課題を抽出
                    if z_score_data.get("analysis_summary", {}).get("significant_deviations"):
                        issues = []
                        for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
                            event_names = {
                                'right_strike': '右足接地',
                                'right_off': '右足離地',
                                'left_strike': '左足接地',
                                'left_off': '左足離地'
                            }
                            event_name = event_names.get(deviation["event"], deviation["event"])
                            severity = "高" if deviation["severity"] == "high" else "中"
                            issue_text = f"{event_name}時の{deviation['angle']}が標準から大きく外れています（Z値: {deviation['z_score']:.2f}, 重要度: {severity}）"
                            issues.append(issue_text)
                        
                        issue_data["issues"] = issues
                        issue_data["analysis_details"]["total_issues"] = len(issues)
                    
                    # Step 4: アドバイス生成
                    advice_results = None
                    advice_analysis = None
                    
                    try:
                        logger.info("アドバイス生成サービス（Gemini AI）を呼び出します")
                        advice_request = {
                            "video_id": video_id,
                            "issues": issue_data.get("issues", [])
                        }
                        
                        advice_response = await client.post(ADVICE_GENERATION_URL, json=advice_request, timeout=60.0)
                        advice_response.raise_for_status()
                        advice_results = advice_response.json()
                        logger.info("Gemini AIアドバイス生成完了")
                        
                        # 統合アドバイス生成
                        logger.info("統合アドバイス生成サービスを呼び出します")
                        high_level_issues = []
                        if z_score_data and z_score_data.get("analysis_summary", {}).get("significant_deviations"):
                            for deviation in z_score_data["analysis_summary"]["significant_deviations"]:
                                if deviation["severity"] == "high":
                                    high_level_issues.append(f"{deviation['angle']}の{deviation['event']}異常")
                        
                        integrated_advice_request = {
                            "video_id": video_id,
                            "issues_list": high_level_issues or ["フォーム改善"]
                        }
                        
                        integrated_advice_response = await client.post(
                            f"{ADVICE_GENERATION_URL.replace('/generate', '/generate-integrated')}", 
                            json=integrated_advice_request, 
                            timeout=60.0
                        )
                        integrated_advice_response.raise_for_status()
                        advice_analysis = integrated_advice_response.json()
                        logger.info("統合アドバイス生成完了")
                        
                    except Exception as e:
                        logger.error(f"アドバイス生成でエラー: {e}")
                        # アドバイス生成に失敗しても、他のデータは返す
                
                # 完全な結果を構築
                result = {
                    "status": "success",
                    "message": "動画アップロード、骨格解析、特徴量計算が完了しました",
                    "upload_info": {
                        "file_id": video_id,
                        "original_filename": file_path.name,
                        "saved_filename": file_path.name,
                        "file_size": file_path.stat().st_size,
                        "content_type": "video/mov",  # 動的に設定可能
                        "upload_timestamp": datetime.utcnow().isoformat(),
                        "file_extension": file_path.suffix
                    },
                    "pose_analysis": pose_data,
                    "feature_analysis": feature_data,
                    "z_score_analysis": z_score_data,
                    "issue_analysis": issue_data
                }
                
                # アドバイスデータがあれば追加
                if advice_results:
                    result["advice_results"] = advice_results
                    
                if advice_analysis:
                    result["advice_analysis"] = advice_analysis
                
                logger.info("完全な解析パイプライン完了")
                return result
        
        # ファイルが見つからない場合
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found for ID: {video_id}"
        )
        
    except Exception as e:
        logger.error(f"結果取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"結果取得中にエラーが発生しました: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 