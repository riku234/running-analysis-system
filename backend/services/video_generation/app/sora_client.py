"""
OpenAI Sora-2 APIクライアント
"""
import os
import asyncio
from typing import Optional
from openai import OpenAI

class SoraVideoClient:
    """OpenAI Sora-2 APIを使用して動画を生成するクライアント"""
    
    def __init__(self):
        """
        OpenAI APIクライアントを初期化
        APIキーは環境変数 OPENAI_API_KEY から取得
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
        print("✅ OpenAI Sora-2 APIクライアント初期化完了")
    
    async def generate_video(
        self, 
        prompt: str, 
        size: str = "1280x720",
        seconds: str = "4"
    ) -> dict:
        """
        Sora-2 APIを使用して動画を生成
        
        Args:
            prompt: 動画の内容を記述するテキスト
            size: 解像度（例: "1280x720", "1920x1080"）
            seconds: 動画の長さ。指定可能な値は "4" のみ
        
        Returns:
            {
                "status": "completed" | "failed",
                "video_url": "https://..." | None,
                "error": None | str
            }
        
        使用例:
            client = SoraVideoClient()
            result = await client.generate_video(
                prompt="プランクのトレーニング動画: 体幹を鍛える基本エクササイズ",
                size="1280x720",
                seconds="4"
            )
        """
        try:
            print(f"🎬 Sora-2 動画生成開始...")
            print(f"   プロンプト: {prompt[:100]}...")
            print(f"   解像度: {size}")
            print(f"   長さ: {seconds}秒")
            
            # Sora-2 API呼び出し
            # Note: 実際のAPIエンドポイントは OpenAI のドキュメントに従って調整が必要
            response = self.client.videos.generate(
                model="sora-2",
                prompt=prompt,
                size=size,
                seconds=seconds
            )
            
            # レスポンスから動画URLを取得
            # 実際のレスポンス構造に応じて調整
            video_url = None
            if hasattr(response, 'url'):
                video_url = response.url
            elif hasattr(response, 'video_url'):
                video_url = response.video_url
            elif hasattr(response, 'data') and len(response.data) > 0:
                video_url = response.data[0].url
            
            if video_url:
                print(f"✅ 動画生成成功: {video_url}")
                return {
                    "status": "completed",
                    "video_url": video_url,
                    "error": None
                }
            else:
                print(f"⚠️  動画URLが取得できませんでした")
                return {
                    "status": "failed",
                    "video_url": None,
                    "error": "動画URLが取得できませんでした"
                }
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Sora-2 動画生成エラー: {error_msg}")
            
            return {
                "status": "failed",
                "video_url": None,
                "error": error_msg
            }
    
    async def generate_training_video(self, drill_text: str) -> dict:
        """
        トレーニングドリルテキストから動画を生成
        
        Args:
            drill_text: おすすめの補強ドリルのテキスト
        
        Returns:
            動画生成結果
        """
        # トレーニング動画用のプロンプトを構築
        prompt = f"""
トレーニング動画を生成してください。

エクササイズ内容:
{drill_text}

要件:
- 動作を明確に示す
- 正しいフォームを見せる
- 初心者でも分かりやすい
- プロフェッショナルな品質
"""
        
        return await self.generate_video(
            prompt=prompt.strip(),
            size="1280x720",  # HD解像度
            seconds="4"       # 4秒固定
        )

