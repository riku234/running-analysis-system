"""
Video Generation Service - FastAPI Application
トレーニング動画を生成するサービス
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import os
from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoStatusResponse
)
from .sora_client import SoraVideoClient

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# パスワード設定
VIDEO_GENERATION_PASSWORD = os.getenv("VIDEO_GENERATION_PASSWORD", "")

# ブルートフォース対策: IPアドレスごとの試行回数を記録
failed_attempts = defaultdict(lambda: {"count": 0, "last_attempt": None})
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

app = FastAPI(
    title="Video Generation Service",
    description="OpenAI Sora-2を使用してトレーニング動画を生成するサービス",
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

# 動画生成結果を一時的に保存（実運用ではRedisやDBを使用）
video_cache: Dict[int, dict] = {}

def verify_password(password: str, client_ip: str) -> tuple[bool, str]:
    """
    パスワードを検証する
    
    Args:
        password: 入力されたパスワード
        client_ip: クライアントのIPアドレス
    
    Returns:
        (検証結果, エラーメッセージ)
    """
    # ロックアウトチェック
    if client_ip in failed_attempts:
        attempt_info = failed_attempts[client_ip]
        if attempt_info["count"] >= MAX_ATTEMPTS:
            if attempt_info["last_attempt"]:
                time_since_last = datetime.now() - attempt_info["last_attempt"]
                if time_since_last < LOCKOUT_DURATION:
                    remaining = LOCKOUT_DURATION - time_since_last
                    return False, f"試行回数が上限に達しました。{int(remaining.total_seconds() / 60)}分後に再試行してください。"
                else:
                    # ロックアウト期間が過ぎたのでリセット
                    failed_attempts[client_ip] = {"count": 0, "last_attempt": None}
    
    # パスワードチェック
    if not VIDEO_GENERATION_PASSWORD:
        logger.warning("⚠️  VIDEO_GENERATION_PASSWORD が設定されていません")
        return False, "動画生成機能は現在利用できません"
    
    if password == VIDEO_GENERATION_PASSWORD:
        # 成功したので試行回数をリセット
        if client_ip in failed_attempts:
            del failed_attempts[client_ip]
        return True, ""
    else:
        # 失敗を記録
        failed_attempts[client_ip]["count"] += 1
        failed_attempts[client_ip]["last_attempt"] = datetime.now()
        remaining_attempts = MAX_ATTEMPTS - failed_attempts[client_ip]["count"]
        
        if remaining_attempts > 0:
            return False, f"パスワードが正しくありません（残り{remaining_attempts}回）"
        else:
            return False, f"試行回数が上限に達しました。{int(LOCKOUT_DURATION.total_seconds() / 60)}分後に再試行してください。"

@app.on_event("startup")
async def startup_event():
    """サービス起動時の処理"""
    logger.info("🎬 Video Generation Service 起動中...")
    logger.info("=" * 80)
    
    # OpenAI APIクライアントの初期化テスト
    try:
        sora_client = SoraVideoClient()
        logger.info("✅ OpenAI Sora-2 APIクライアント初期化成功")
    except Exception as e:
        logger.error(f"❌ OpenAI APIクライアント初期化エラー: {e}")
    
    logger.info("=" * 80)
    logger.info("🚀 Video Generation Service 起動完了")

@app.get("/")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "service": "video_generation",
        "message": "Video Generation Service is running"
    }

@app.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    トレーニング動画を生成する
    
    Args:
        request: 動画生成リクエスト（run_id, drill_text, password）
        background_tasks: バックグラウンドタスク
        req: FastAPI Request オブジェクト（IPアドレス取得用）
    
    Returns:
        VideoGenerationResponse: 動画生成結果
    """
    try:
        logger.info("=" * 80)
        logger.info("🎬 動画生成リクエスト受信")
        logger.info(f"   Run ID: {request.run_id}")
        logger.info(f"   ドリルテキスト: {request.drill_text[:100]}...")
        logger.info(f"   解像度: {request.size}")
        logger.info(f"   長さ: {request.seconds}秒")
        
        # パスワード検証
        client_ip = req.client.host
        is_valid, error_message = verify_password(request.password, client_ip)
        
        if not is_valid:
            logger.warning(f"❌ パスワード検証失敗: {client_ip} - {error_message}")
            raise HTTPException(
                status_code=401,
                detail=error_message
            )
        
        logger.info(f"✅ パスワード検証成功: {client_ip}")
        
        # Sora-2クライアントを初期化
        sora_client = SoraVideoClient()
        
        # 動画を生成（同期処理）
        logger.info("🎥 Sora-2 API呼び出し中...")
        result = await sora_client.generate_training_video(request.drill_text)
        
        # 結果をキャッシュに保存
        video_cache[request.run_id] = result
        
        if result["status"] == "completed":
            logger.info("✅ 動画生成成功")
            logger.info(f"   動画URL: {result['video_url']}")
            
            return VideoGenerationResponse(
                status="success",
                message="動画生成が完了しました",
                video_url=result["video_url"],
                error=None
            )
        else:
            logger.error(f"❌ 動画生成失敗: {result['error']}")
            
            return VideoGenerationResponse(
                status="failed",
                message="動画生成に失敗しました",
                video_url=None,
                error=result["error"]
            )
    
    except Exception as e:
        logger.error(f"❌ 動画生成エラー: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"動画生成エラー: {str(e)}"
        )

@app.get("/status/{run_id}", response_model=VideoStatusResponse)
async def get_video_status(run_id: int):
    """
    動画生成のステータスを取得
    
    Args:
        run_id: 走行ID
    
    Returns:
        VideoStatusResponse: 動画ステータス
    """
    logger.info(f"📊 動画ステータス確認: Run ID {run_id}")
    
    # キャッシュから結果を取得
    if run_id in video_cache:
        result = video_cache[run_id]
        
        return VideoStatusResponse(
            status="success",
            video_url=result.get("video_url"),
            generation_status=result.get("status"),
            error_message=result.get("error")
        )
    else:
        return VideoStatusResponse(
            status="not_found",
            video_url=None,
            generation_status="not_generated",
            error_message=None
        )

@app.delete("/cache/{run_id}")
async def clear_cache(run_id: int):
    """
    キャッシュをクリア（メモリ節約用）
    
    Args:
        run_id: 走行ID
    
    Returns:
        クリア結果
    """
    if run_id in video_cache:
        del video_cache[run_id]
        logger.info(f"🗑️  キャッシュクリア: Run ID {run_id}")
        return {"status": "success", "message": "キャッシュをクリアしました"}
    else:
        return {"status": "not_found", "message": "キャッシュが見つかりませんでした"}

@app.get("/download/{video_id}")
async def download_video(video_id: str):
    """
    OpenAIから動画をダウンロードして返す
    
    Args:
        video_id: OpenAI video ID
    
    Returns:
        動画ファイル (MP4)
    """
    from fastapi.responses import StreamingResponse
    
    try:
        logger.info(f"📥 動画ダウンロードリクエスト: {video_id}")
        
        # Sora-2クライアントを初期化
        sora_client = SoraVideoClient()
        
        # 動画コンテンツをダウンロード（ストリーム）
        content_stream = sora_client.client.videos.download_content(video_id)
        
        # HttpxBinaryResponseContentから全てのバイトを読み込む
        if hasattr(content_stream, 'read'):
            content_bytes = content_stream.read()
        elif hasattr(content_stream, '__iter__'):
            content_bytes = b''.join(content_stream)
        else:
            # 直接バイト列の場合
            content_bytes = bytes(content_stream)
        
        logger.info(f"✅ 動画ダウンロード成功: {len(content_bytes)} bytes")
        
        # BytesIOラッパーで返す
        from io import BytesIO
        return StreamingResponse(
            BytesIO(content_bytes),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename=training_video_{video_id}.mp4"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ 動画ダウンロードエラー: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"動画ダウンロードエラー: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

