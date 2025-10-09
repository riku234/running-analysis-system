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
            
            # Sora-2 API呼び出し（正しいAPI仕様に基づく）
            video = self.client.videos.create(
                model="sora-2",
                prompt=prompt,
                # サイズと秒数はパラメータとして渡す（必要に応じて）
            )
            
            # デバッグ: レスポンス構造を出力
            print(f"📊 動画生成開始: {video}")
            print(f"📊 Video ID: {video.id if hasattr(video, 'id') else 'N/A'}")
            print(f"📊 Status: {video.status if hasattr(video, 'status') else 'N/A'}")
            print(f"📊 Progress: {video.progress if hasattr(video, 'progress') else 'N/A'}")
            
            # レスポンス例:
            # {
            #   "id": "video_68d7512d...",
            #   "object": "video",
            #   "created_at": 1758941485,
            #   "status": "queued",  # または "processing", "completed", "failed"
            #   "model": "sora-2-pro",
            #   "progress": 0,
            #   "seconds": "8",
            #   "size": "1280x720"
            # }
            
            # ステータスをチェック
            if hasattr(video, 'status'):
                status = video.status
                
                # 非同期処理の場合: queued または processing
                if status in ['queued', 'processing']:
                    print(f"🔄 動画生成中... (status: {status})")
                    
                    # ポーリングで完了を待つ
                    video_id = video.id
                    max_wait_time = 180  # 最大3分
                    poll_interval = 5     # 5秒ごとにチェック
                    elapsed_time = 0
                    
                    while elapsed_time < max_wait_time:
                        await asyncio.sleep(poll_interval)
                        elapsed_time += poll_interval
                        
                        # ステータスを再取得
                        video = self.client.videos.retrieve(video_id)
                        print(f"🔄 ポーリング ({elapsed_time}s): status={video.status}, progress={video.progress if hasattr(video, 'progress') else 'N/A'}")
                        
                        if video.status == 'completed':
                            break
                        elif video.status == 'failed':
                            error_msg = video.error if hasattr(video, 'error') else "動画生成に失敗しました"
                            print(f"❌ 動画生成失敗: {error_msg}")
                            return {
                                "status": "failed",
                                "video_url": None,
                                "error": error_msg
                            }
                    
                    if video.status != 'completed':
                        print(f"⏱️  タイムアウト: {max_wait_time}秒以内に完了しませんでした")
                        return {
                            "status": "failed",
                            "video_url": None,
                            "error": f"タイムアウト（{max_wait_time}秒）"
                        }
                
                # 完了した場合（ポーリングループ後の処理）
                if video.status == 'completed':
                    print(f"✅ 動画生成完了: video_id={video_id}")
                    
                    # 動画コンテンツをダウンロード
                    try:
                        print(f"📥 動画コンテンツ確認中...")
                        # content = self.client.videos.download_content(video_id)
                        # HttpxBinaryResponseContentはストリームなので、ここではIDだけ返す
                        
                        print(f"✅ 動画生成完了、video_idを返却")
                        print(f"📊 Video ID: {video_id}")
                        
                        # 動画IDを返す（フロントエンドでダウンロードエンドポイントを叩く）
                        return {
                            "status": "completed",
                            "video_url": f"/api/video-generation/download/{video_id}",
                            "video_id": video_id,
                            "error": None
                        }
                    
                    except Exception as download_error:
                        print(f"❌ 動画ダウンロードエラー: {download_error}")
                        return {
                            "status": "failed",
                            "video_url": None,
                            "error": f"動画ダウンロード失敗: {str(download_error)}"
                        }
            
            # ステータスが不明な場合
            print(f"⚠️  予期しないレスポンス構造")
            return {
                "status": "failed",
                "video_url": None,
                "error": "予期しないレスポンス構造"
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

