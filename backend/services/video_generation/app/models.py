"""
Pydantic models for Video Generation Service
"""
from pydantic import BaseModel
from typing import Optional

class VideoGenerationRequest(BaseModel):
    """動画生成リクエスト"""
    run_id: int
    drill_text: str
    size: Optional[str] = "1280x720"
    seconds: Optional[str] = "4"

class VideoGenerationResponse(BaseModel):
    """動画生成レスポンス"""
    status: str
    message: str
    video_url: Optional[str] = None
    error: Optional[str] = None

class VideoStatusResponse(BaseModel):
    """動画ステータスレスポンス"""
    status: str
    video_url: Optional[str] = None
    generation_status: Optional[str] = None
    error_message: Optional[str] = None

