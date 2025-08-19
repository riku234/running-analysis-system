'use client'

import { useEffect, useRef, useState } from 'react'

interface KeyPoint {
  x: number
  y: number
  z: number
  visibility: number
}

interface FramePoseData {
  frame_number: number
  timestamp: number
  keypoints: KeyPoint[]
  landmarks_detected: boolean
  confidence_score: number
}

interface PoseAnalysisData {
  status: string
  message: string
  video_info: {
    fps: number
    total_frames: number
    duration_seconds: number
    width: number
    height: number
  }
  pose_data: FramePoseData[]
  summary: {
    total_processed_frames: number
    detected_pose_frames: number
    detection_rate: number
    average_confidence: number
    mediapipe_landmarks_count: number
  }
}

interface PoseVisualizerProps {
  videoUrl: string
  poseData: PoseAnalysisData
  className?: string
}

// MediaPipeの骨格接続定義（33個のランドマーク用）
const POSE_CONNECTIONS = [
  // 顔の輪郭
  [0, 1], [1, 2], [2, 3], [3, 7],
  [0, 4], [4, 5], [5, 6], [6, 8],
  
  // 腕
  [9, 10], // 口
  [11, 12], // 肩
  [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], // 左腕
  [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], // 右腕
  
  // 胴体
  [11, 23], [12, 24], [23, 24], // 胴体
  
  // 脚
  [23, 25], [25, 27], [27, 29], [27, 31], // 左脚
  [24, 26], [26, 28], [28, 30], [28, 32], // 右脚
]

export default function PoseVisualizer({ videoUrl, poseData, className = '' }: PoseVisualizerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [currentFrame, setCurrentFrame] = useState(0)
  
  // 動画の現在時刻から対応するフレームを取得
  const getCurrentFrameData = (): FramePoseData | null => {
    if (!videoRef.current || !poseData.pose_data.length) return null
    
    const currentTime = videoRef.current.currentTime
    const fps = poseData.video_info.fps || 30
    const frameNumber = Math.floor(currentTime * fps)
    
    return poseData.pose_data.find(frame => frame.frame_number === frameNumber) || null
  }
  
  // キーポイントを描画
  const drawKeypoints = (ctx: CanvasRenderingContext2D, keypoints: KeyPoint[], videoWidth: number, videoHeight: number) => {
    ctx.fillStyle = '#ff0000'
    ctx.strokeStyle = '#00ff00'
    ctx.lineWidth = 2
    
    // キーポイントを描画
    keypoints.forEach((point, index) => {
      if (point.visibility > 0.5) { // 信頼度が高いポイントのみ描画
        const x = point.x * videoWidth
        const y = point.y * videoHeight
        
        // ポイントを描画
        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * Math.PI)
        ctx.fill()
        
        // ポイント番号を描画（デバッグ用）
        ctx.fillStyle = '#ffffff'
        ctx.font = '10px Arial'
        ctx.fillText(index.toString(), x + 5, y - 5)
        ctx.fillStyle = '#ff0000'
      }
    })
    
    // 骨格の線を描画
    ctx.strokeStyle = '#00ff00'
    ctx.lineWidth = 2
    
    POSE_CONNECTIONS.forEach(([startIdx, endIdx]) => {
      const startPoint = keypoints[startIdx]
      const endPoint = keypoints[endIdx]
      
      if (startPoint && endPoint && 
          startPoint.visibility > 0.5 && endPoint.visibility > 0.5) {
        const startX = startPoint.x * videoWidth
        const startY = startPoint.y * videoHeight
        const endX = endPoint.x * videoWidth
        const endY = endPoint.y * videoHeight
        
        ctx.beginPath()
        ctx.moveTo(startX, startY)
        ctx.lineTo(endX, endY)
        ctx.stroke()
      }
    })
  }
  
  // Canvas描画の更新
  const updateCanvas = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    
    if (!video || !canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // Canvasサイズを動画サイズに合わせる
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.style.width = video.offsetWidth + 'px'
    canvas.style.height = video.offsetHeight + 'px'
    
    // Canvasをクリア
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 現在のフレームの骨格データを取得
    const frameData = getCurrentFrameData()
    
    if (frameData && frameData.landmarks_detected) {
      drawKeypoints(ctx, frameData.keypoints, canvas.width, canvas.height)
      
      // 信頼度を表示
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(10, 10, 200, 30)
      ctx.fillStyle = '#000000'
      ctx.font = '14px Arial'
      ctx.fillText(`信頼度: ${(frameData.confidence_score * 100).toFixed(1)}%`, 15, 30)
    }
  }
  
  // 動画のリサイズ処理
  const handleVideoResize = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    
    if (video && canvas) {
      canvas.style.width = video.offsetWidth + 'px'
      canvas.style.height = video.offsetHeight + 'px'
      updateCanvas()
    }
  }
  
  useEffect(() => {
    const video = videoRef.current
    
    if (video) {
      const handleTimeUpdate = () => {
        updateCanvas()
        setCurrentFrame(Math.floor(video.currentTime * (poseData.video_info.fps || 30)))
      }
      
      const handleLoadedMetadata = () => {
        handleVideoResize()
      }
      
      video.addEventListener('timeupdate', handleTimeUpdate)
      video.addEventListener('loadedmetadata', handleLoadedMetadata)
      window.addEventListener('resize', handleVideoResize)
      
      return () => {
        video.removeEventListener('timeupdate', handleTimeUpdate)
        video.removeEventListener('loadedmetadata', handleLoadedMetadata)
        window.removeEventListener('resize', handleVideoResize)
      }
    }
  }, [videoUrl])
  
  return (
    <div className={`relative ${className}`}>
      <div className="relative inline-block">
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          className="w-full max-w-4xl rounded-lg shadow-lg"
          onLoadedMetadata={handleVideoResize}
          preload="metadata"
        >
          お使いのブラウザは動画の再生をサポートしていません。
        </video>
        
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 pointer-events-none"
          style={{ zIndex: 10 }}
        />
      </div>

      {/* 解析情報パネル - 開発環境でのみ表示 */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">骨格解析結果（開発環境のみ）</h3>
          
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded p-3">
              <h4 className="font-medium text-gray-700 mb-2">動画情報</h4>
              <div className="text-sm space-y-1">
                <div>解像度: {poseData.video_info.width} × {poseData.video_info.height}</div>
                <div>フレームレート: {poseData.video_info.fps.toFixed(1)} FPS</div>
                <div>総フレーム数: {poseData.video_info.total_frames}</div>
                <div>動画時間: {poseData.video_info.duration_seconds.toFixed(1)}秒</div>
              </div>
            </div>

            <div className="bg-white rounded p-3">
              <h4 className="font-medium text-gray-700 mb-2">検出統計</h4>
              <div className="text-sm space-y-1">
                <div>検出フレーム: {poseData.summary.detected_pose_frames}</div>
                <div>検出率: {(poseData.summary.detection_rate * 100).toFixed(1)}%</div>
                <div>平均信頼度: {(poseData.summary.average_confidence * 100).toFixed(1)}%</div>
                <div>ランドマーク数: {poseData.summary.mediapipe_landmarks_count}</div>
              </div>
            </div>

            <div className="bg-white rounded p-3">
              <h4 className="font-medium text-gray-700 mb-2">現在のフレーム</h4>
              <div className="text-sm space-y-1">
                <div>フレーム番号: {currentFrame}</div>
                <div>時刻: {(currentFrame / (poseData.video_info.fps || 30)).toFixed(2)}秒</div>
                <div>骨格検出: {getCurrentFrameData()?.landmarks_detected ? 'あり' : 'なし'}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 