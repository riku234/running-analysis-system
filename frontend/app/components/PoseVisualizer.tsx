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

// MediaPipeランドマークのインデックス定義
const LANDMARK_INDICES = {
  left_shoulder: 11,
  right_shoulder: 12,
  left_elbow: 13,
  right_elbow: 14,
  left_wrist: 15,
  right_wrist: 16,
  left_hip: 23,
  right_hip: 24,
  left_knee: 25,
  right_knee: 26,
  left_ankle: 27,
  right_ankle: 28,
  left_foot_index: 31,
  right_foot_index: 32
}

// 関節角度の状態管理
interface JointAngles {
  trunk_angle: number | null
  left_hip_angle: number | null
  right_hip_angle: number | null
  left_knee_angle: number | null
  right_knee_angle: number | null
  left_ankle_angle: number | null
  right_ankle_angle: number | null
  left_elbow_angle: number | null
  right_elbow_angle: number | null
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

// 関節角度計算関数
const calculateAngle = (p1: KeyPoint, p2: KeyPoint, p3: KeyPoint): number | null => {
  try {
    // 入力の妥当性をチェック（信頼度0.5以上のみ有効）
    if (p1.visibility < 0.5 || p2.visibility < 0.5 || p3.visibility < 0.5) {
      return null
    }

    // ベクトル p2->p1 と p2->p3 を作成
    const vector1 = [p1.x - p2.x, p1.y - p2.y]
    const vector2 = [p3.x - p2.x, p3.y - p2.y]

    // ベクトルの長さを計算
    const length1 = Math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
    const length2 = Math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

    // ベクトルの長さが0の場合は無効
    if (length1 === 0 || length2 === 0) {
      return null
    }

    // 内積を利用して角度を計算
    const cosAngle = (vector1[0] * vector2[0] + vector1[1] * vector2[1]) / (length1 * length2)

    // 数値誤差対策：cosの値を[-1, 1]にクリップ
    const clippedCosAngle = Math.max(-1, Math.min(1, cosAngle))

    // ラジアンから度数法に変換
    const angleRad = Math.acos(clippedCosAngle)
    const angleDeg = (angleRad * 180) / Math.PI

    return angleDeg
  } catch (error) {
    return null
  }
}

// 体幹角度計算関数
const calculateTrunkAngle = (keypoints: KeyPoint[]): number | null => {
  try {
    const leftShoulder = keypoints[LANDMARK_INDICES.left_shoulder]
    const rightShoulder = keypoints[LANDMARK_INDICES.right_shoulder]
    const leftHip = keypoints[LANDMARK_INDICES.left_hip]
    const rightHip = keypoints[LANDMARK_INDICES.right_hip]

    // すべてのキーポイントが有効か確認
    if (leftShoulder.visibility < 0.5 || rightShoulder.visibility < 0.5 ||
        leftHip.visibility < 0.5 || rightHip.visibility < 0.5) {
      return null
    }

    // 肩の中心点と腰の中心点を計算
    const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2
    const shoulderCenterY = (leftShoulder.y + rightShoulder.y) / 2
    const hipCenterX = (leftHip.x + rightHip.x) / 2
    const hipCenterY = (leftHip.y + rightHip.y) / 2

    // 体幹ベクトル（腰から肩へ）
    const trunkVector = [shoulderCenterX - hipCenterX, shoulderCenterY - hipCenterY]

    // 垂直ベクトル（上向き）
    const verticalVector = [0, -1]

    // ベクトルの長さを計算
    const trunkLength = Math.sqrt(trunkVector[0] ** 2 + trunkVector[1] ** 2)
    if (trunkLength === 0) {
      return null
    }

    // 角度を計算
    const cosAngle = (trunkVector[0] * verticalVector[0] + trunkVector[1] * verticalVector[1]) / trunkLength
    const clippedCosAngle = Math.max(-1, Math.min(1, cosAngle))

    const angleRad = Math.acos(clippedCosAngle)
    const angleDeg = (angleRad * 180) / Math.PI

    return angleDeg
  } catch (error) {
    return null
  }
}

// 1フレームから全ての関節角度を抽出
const extractJointAnglesFromFrame = (keypoints: KeyPoint[]): JointAngles => {
  const angles: JointAngles = {
    trunk_angle: null,
    left_hip_angle: null,
    right_hip_angle: null,
    left_knee_angle: null,
    right_knee_angle: null,
    left_ankle_angle: null,
    right_ankle_angle: null,
    left_elbow_angle: null,
    right_elbow_angle: null
  }

  try {
    // ① 体幹角度
    angles.trunk_angle = calculateTrunkAngle(keypoints)

    // 肩の中心点を計算（股関節角度用）
    const leftShoulder = keypoints[LANDMARK_INDICES.left_shoulder]
    const rightShoulder = keypoints[LANDMARK_INDICES.right_shoulder]
    
    let shoulderCenter: KeyPoint | null = null
    if (leftShoulder.visibility > 0.5 && rightShoulder.visibility > 0.5) {
      shoulderCenter = {
        x: (leftShoulder.x + rightShoulder.x) / 2,
        y: (leftShoulder.y + rightShoulder.y) / 2,
        z: (leftShoulder.z + rightShoulder.z) / 2,
        visibility: Math.min(leftShoulder.visibility, rightShoulder.visibility)
      }
    }

    // ② 股関節角度（左右）
    if (shoulderCenter) {
      const leftHip = keypoints[LANDMARK_INDICES.left_hip]
      const leftKnee = keypoints[LANDMARK_INDICES.left_knee]
      angles.left_hip_angle = calculateAngle(shoulderCenter, leftHip, leftKnee)

      const rightHip = keypoints[LANDMARK_INDICES.right_hip]
      const rightKnee = keypoints[LANDMARK_INDICES.right_knee]
      angles.right_hip_angle = calculateAngle(shoulderCenter, rightHip, rightKnee)
    }

    // ③ 膝関節角度（左右）
    const leftHip = keypoints[LANDMARK_INDICES.left_hip]
    const leftKnee = keypoints[LANDMARK_INDICES.left_knee]
    const leftAnkle = keypoints[LANDMARK_INDICES.left_ankle]
    angles.left_knee_angle = calculateAngle(leftHip, leftKnee, leftAnkle)

    const rightHip = keypoints[LANDMARK_INDICES.right_hip]
    const rightKnee = keypoints[LANDMARK_INDICES.right_knee]
    const rightAnkle = keypoints[LANDMARK_INDICES.right_ankle]
    angles.right_knee_angle = calculateAngle(rightHip, rightKnee, rightAnkle)

    // ④ 足関節角度（左右）
    const leftFootIndex = keypoints[LANDMARK_INDICES.left_foot_index]
    angles.left_ankle_angle = calculateAngle(leftKnee, leftAnkle, leftFootIndex)

    const rightFootIndex = keypoints[LANDMARK_INDICES.right_foot_index]
    angles.right_ankle_angle = calculateAngle(rightKnee, rightAnkle, rightFootIndex)

    // ⑤ 肘関節角度（左右）
    const leftElbow = keypoints[LANDMARK_INDICES.left_elbow]
    const leftWrist = keypoints[LANDMARK_INDICES.left_wrist]
    angles.left_elbow_angle = calculateAngle(leftShoulder, leftElbow, leftWrist)

    const rightElbow = keypoints[LANDMARK_INDICES.right_elbow]
    const rightWrist = keypoints[LANDMARK_INDICES.right_wrist]
    angles.right_elbow_angle = calculateAngle(rightShoulder, rightElbow, rightWrist)

  } catch (error) {
    console.warn('関節角度の計算でエラーが発生しました:', error)
  }

  return angles
}

export default function PoseVisualizer({ videoUrl, poseData, className = '' }: PoseVisualizerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [currentFrame, setCurrentFrame] = useState(0)
  const [currentJointAngles, setCurrentJointAngles] = useState<JointAngles>({
    trunk_angle: null,
    left_hip_angle: null,
    right_hip_angle: null,
    left_knee_angle: null,
    right_knee_angle: null,
    left_ankle_angle: null,
    right_ankle_angle: null,
    left_elbow_angle: null,
    right_elbow_angle: null
  })
  
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
      
      // リアルタイムで関節角度を計算・更新
      const jointAngles = extractJointAnglesFromFrame(frameData.keypoints)
      setCurrentJointAngles(jointAngles)
      
      // 信頼度を表示（本番環境では非表示）
      if (false) {
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(10, 10, 200, 30)
        ctx.fillStyle = '#000000'
        ctx.font = '14px Arial'
        ctx.fillText(`信頼度: ${(frameData.confidence_score * 100).toFixed(1)}%`, 15, 30)
      }
    } else {
      // 骨格が検出されていない場合は角度をリセット
      setCurrentJointAngles({
        trunk_angle: null,
        left_hip_angle: null,
        right_hip_angle: null,
        left_knee_angle: null,
        right_knee_angle: null,
        left_ankle_angle: null,
        right_ankle_angle: null,
        left_elbow_angle: null,
        right_elbow_angle: null
      })
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
    <div className={`${className}`}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 動画エリア */}
        <div className="lg:col-span-2">
          <div className="relative inline-block w-full">
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              className="w-full rounded-lg shadow-lg"
              onLoadedMetadata={handleVideoResize}
              preload="metadata"
            >
              お使いのブラウザは動画の再生をサポートしていません。
            </video>
            
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none rounded-lg"
              style={{ zIndex: 10 }}
            />
          </div>
        </div>

        {/* リアルタイム関節角度表示エリア */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800 border-b pb-2">
              リアルタイム関節角度
            </h3>
            
            <div className="space-y-4">
              {/* 体幹角度 */}
              <div className="bg-blue-50 rounded-lg p-3">
                <h4 className="font-medium text-blue-800 mb-2">体幹角度</h4>
                <div className="text-lg font-bold text-blue-600">
                  {currentJointAngles.trunk_angle !== null ? 
                    `${currentJointAngles.trunk_angle.toFixed(1)}°` : 
                    '計算中...'}
                </div>
              </div>

              {/* 股関節角度 */}
              <div className="bg-green-50 rounded-lg p-3">
                <h4 className="font-medium text-green-800 mb-2">股関節角度</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">左:</span>
                    <div className="font-bold text-green-600">
                      {currentJointAngles.left_hip_angle !== null ? 
                        `${currentJointAngles.left_hip_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">右:</span>
                    <div className="font-bold text-green-600">
                      {currentJointAngles.right_hip_angle !== null ? 
                        `${currentJointAngles.right_hip_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                </div>
              </div>

              {/* 膝関節角度 */}
              <div className="bg-purple-50 rounded-lg p-3">
                <h4 className="font-medium text-purple-800 mb-2">膝関節角度</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">左:</span>
                    <div className="font-bold text-purple-600">
                      {currentJointAngles.left_knee_angle !== null ? 
                        `${currentJointAngles.left_knee_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">右:</span>
                    <div className="font-bold text-purple-600">
                      {currentJointAngles.right_knee_angle !== null ? 
                        `${currentJointAngles.right_knee_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                </div>
              </div>

              {/* 足関節角度 */}
              <div className="bg-orange-50 rounded-lg p-3">
                <h4 className="font-medium text-orange-800 mb-2">足関節角度</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">左:</span>
                    <div className="font-bold text-orange-600">
                      {currentJointAngles.left_ankle_angle !== null ? 
                        `${currentJointAngles.left_ankle_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">右:</span>
                    <div className="font-bold text-orange-600">
                      {currentJointAngles.right_ankle_angle !== null ? 
                        `${currentJointAngles.right_ankle_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                </div>
              </div>

              {/* 肘関節角度 */}
              <div className="bg-cyan-50 rounded-lg p-3">
                <h4 className="font-medium text-cyan-800 mb-2">肘関節角度</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">左:</span>
                    <div className="font-bold text-cyan-600">
                      {currentJointAngles.left_elbow_angle !== null ? 
                        `${currentJointAngles.left_elbow_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">右:</span>
                    <div className="font-bold text-cyan-600">
                      {currentJointAngles.right_elbow_angle !== null ? 
                        `${currentJointAngles.right_elbow_angle.toFixed(1)}°` : 
                        '--'}
                    </div>
                  </div>
                </div>
              </div>

              {/* フレーム情報 */}
              <div className="bg-gray-50 rounded-lg p-3 mt-4">
                <h4 className="font-medium text-gray-600 mb-2">フレーム情報</h4>
                <div className="text-sm space-y-1">
                  <div>フレーム: {currentFrame}</div>
                  <div>時刻: {(currentFrame / (poseData.video_info.fps || 30)).toFixed(2)}秒</div>
                  <div>
                    骨格検出: {getCurrentFrameData()?.landmarks_detected ? 
                      <span className="text-green-600 font-medium">検出中</span> : 
                      <span className="text-red-600 font-medium">未検出</span>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 解析情報パネル - 開発環境でのみ表示 */}
      {false && process.env.NODE_ENV === 'development' && (
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