from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import aiofiles
from pathlib import Path
import uuid
from datetime import datetime
import httpx
import asyncio

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
async def upload_video(file: UploadFile = File(...)):
    """
    動画ファイルをアップロードして一時保存する
    
    Args:
        file: アップロードされた動画ファイル
        
    Returns:
        アップロード結果とファイル情報
    """
    # ファイル形式の検証
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
        )
    
    # ユニークなファイル名を生成
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{unique_id}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # ファイルを非同期で保存
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # ファイルサイズを取得
        file_size = len(content)
        
        # 基本的なアップロード情報
        upload_data = {
            "file_id": unique_id,
            "original_filename": file.filename,
            "saved_filename": safe_filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "upload_timestamp": datetime.now().isoformat(),
            "file_extension": file_extension
        }
        
        # Pose Estimation Serviceに解析リクエスト
        try:
            async with httpx.AsyncClient() as client:
                pose_request = {
                    "video_path": f"uploads/{safe_filename}",
                    "confidence_threshold": 0.5
                }
                
                response = await client.post(
                    "http://pose_estimation:8003/estimate",
                    json=pose_request,
                    timeout=300.0  # 5分のタイムアウト
                )
                
                if response.status_code == 200:
                    pose_data = response.json()
                    
                    return {
                        "status": "success",
                        "message": "動画アップロードと骨格解析が完了しました",
                        "upload_info": upload_data,
                        "pose_analysis": pose_data
                    }
                else:
                    # 骨格解析が失敗した場合はアップロード情報のみ返す
                    return {
                        "status": "partial_success",
                        "message": "動画アップロードは成功しましたが、骨格解析に失敗しました",
                        "upload_info": upload_data,
                        "pose_analysis": None,
                        "error": f"Pose estimation service returned {response.status_code}"
                    }
                    
        except httpx.RequestError as e:
            # ネットワークエラーの場合はアップロード情報のみ返す
            return {
                "status": "partial_success", 
                "message": "動画アップロードは成功しましたが、骨格解析サービスに接続できませんでした",
                "upload_info": upload_data,
                "pose_analysis": None,
                "error": str(e)
            }
        except Exception as e:
            # その他のエラーの場合
            return {
                "status": "partial_success",
                "message": "動画アップロードは成功しましたが、骨格解析中にエラーが発生しました", 
                "upload_info": upload_data,
                "pose_analysis": None,
                "error": str(e)
            }
        
    except Exception as e:
        # エラーが発生した場合、既に保存されたファイルを削除
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"ファイルの保存中にエラーが発生しました: {str(e)}"
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
        filename: ストリーミングする動画ファイル名
        
    Returns:
        動画ファイルのレスポンス
    """
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 