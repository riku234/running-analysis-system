'use client'

import { useRef, useEffect, useState } from 'react'

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

interface PoseData {
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
  poseData: PoseData
  className?: string
}

// MediaPipe Poseのランドマーク接続定義
const POSE_CONNECTIONS = [
  // 顔
  [0, 1], [1, 2], [2, 3], [3, 7],
  [0, 4], [4, 5], [5, 6], [6, 8],
  // 胴体
  [9, 10],
  [11, 12], [11, 13], [13, 15],
  [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  // 左腕
  [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19],
  // 右腕  
  [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20],
  // 左脚
  [23, 25], [25, 27], [27, 29], [29, 31], [27, 31],
  // 右脚
  [24, 26], [26, 28], [28, 30], [30, 32], [28, 32]
]

export default function PoseVisualizer({ videoUrl, poseData, className = '' }: PoseVisualizerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime)
      drawPoseOnCanvas()
    }

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
    }
  }, [poseData])

  const drawPoseOnCanvas = () => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video || !poseData.pose_data) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // キャンバスをクリア
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 現在の時間に対応するフレームを見つける
    const fps = poseData.video_info.fps
    const currentFrame = Math.floor(currentTime * fps)
    const frameData = poseData.pose_data.find(frame => frame.frame_number === currentFrame)

    if (!frameData || !frameData.landmarks_detected) return

    // キャンバスのサイズ
    const canvasWidth = canvas.width
    const canvasHeight = canvas.height

    // キーポイントを描画
    const keypoints = frameData.keypoints
    ctx.fillStyle = 'rgba(0, 255, 0, 0.8)'
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.8)'
    ctx.lineWidth = 2

    // 接続線を描画
    POSE_CONNECTIONS.forEach(([startIdx, endIdx]) => {
      if (startIdx < keypoints.length && endIdx < keypoints.length) {
        const startPoint = keypoints[startIdx]
        const endPoint = keypoints[endIdx]

        // 可視性チェック（両方のポイントが信頼できる場合のみ描画）
        if (startPoint.visibility > 0.5 && endPoint.visibility > 0.5) {
          ctx.beginPath()
          ctx.moveTo(startPoint.x * canvasWidth, startPoint.y * canvasHeight)
          ctx.lineTo(endPoint.x * canvasWidth, endPoint.y * canvasHeight)
          ctx.stroke()
        }
      }
    })

    // キーポイントを描画
    keypoints.forEach((point, index) => {
      if (point.visibility > 0.5) {
        const x = point.x * canvasWidth
        const y = point.y * canvasHeight

        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * Math.PI)
        ctx.fill()

        // 重要なキーポイントに番号を表示
        if ([0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28].includes(index)) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
          ctx.font = '10px Arial'
          ctx.fillText(index.toString(), x + 6, y - 6)
          ctx.fillStyle = 'rgba(0, 255, 0, 0.8)'
        }
      }
    })

    // 信頼度スコアを表示
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
    ctx.fillRect(10, 10, 200, 30)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
    ctx.font = '14px Arial'
    ctx.fillText(`信頼度: ${(frameData.confidence_score * 100).toFixed(1)}%`, 15, 30)
  }

  const handleVideoResize = () => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return

    // ビデオのサイズに合わせてキャンバスのサイズを調整
    canvas.width = video.offsetWidth
    canvas.height = video.offsetHeight
    drawPoseOnCanvas()
  }

  useEffect(() => {
    handleVideoResize()
    window.addEventListener('resize', handleVideoResize)
    return () => window.removeEventListener('resize', handleVideoResize)
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

      {/* 解析情報パネル */}
      <div className="mt-4 bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">骨格解析結果</h3>
        
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
              <div>再生時間: {currentTime.toFixed(1)}秒</div>
              <div>フレーム番号: {Math.floor(currentTime * poseData.video_info.fps)}</div>
              <div>状態: {isPlaying ? '再生中' : '一時停止'}</div>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <h4 className="font-medium text-gray-700 mb-2">操作説明</h4>
          <div className="text-sm text-gray-600 space-y-1">
            <div>• 動画を再生すると、リアルタイムで骨格が重ね合わせ表示されます</div>
            <div>• 緑色の点が検出されたキーポイント、線がスケルトンを表します</div>
            <div>• 数字は重要なキーポイントのインデックスを示しています</div>
            <div>• 信頼度が低いキーポイントは表示されません</div>
          </div>
        </div>
      </div>
    </div>
  )
} 