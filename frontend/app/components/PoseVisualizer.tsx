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
  problematicAngles?: string[]  // Z-scoreで問題のある角度名のリスト（例: ["trunk_angle", "left_thigh_angle"]）
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
// 拡張された絶対角度の型定義（仕様3対応）
interface AbsoluteAngles {
  // 既存角度
  trunk_angle: number | null
  left_thigh_angle: number | null
  right_thigh_angle: number | null
  left_lower_leg_angle: number | null
  right_lower_leg_angle: number | null
  // 新規追加角度
  left_upper_arm_angle: number | null
  right_upper_arm_angle: number | null
  left_forearm_angle: number | null
  right_forearm_angle: number | null
  left_foot_angle: number | null
  right_foot_angle: number | null
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

// 角度名から骨格線（ランドマークペア）へのマッピング
const ANGLE_TO_SKELETON_CONNECTIONS: { [key: string]: [number, number][] } = {
  // 英語名
  'trunk_angle': [
    [11, 23],  // 左肩 - 左腰
    [12, 24],  // 右肩 - 右腰
  ],
  'left_thigh_angle': [
    [23, 25],  // 左腰 - 左膝
  ],
  'right_thigh_angle': [
    [24, 26],  // 右腰 - 右膝
  ],
  'left_lower_leg_angle': [
    [25, 27],  // 左膝 - 左足首
  ],
  'right_lower_leg_angle': [
    [26, 28],  // 右膝 - 右足首
  ],
  'left_upper_arm_angle': [
    [11, 13],  // 左肩 - 左肘
  ],
  'right_upper_arm_angle': [
    [12, 14],  // 右肩 - 右肘
  ],
  'left_forearm_angle': [
    [13, 15],  // 左肘 - 左手首
  ],
  'right_forearm_angle': [
    [14, 16],  // 右肘 - 右手首
  ],
  
  // 日本語名（バックエンドから返される形式）
  '体幹角度': [
    [11, 23],  // 左肩 - 左腰
    [12, 24],  // 右肩 - 右腰
  ],
  '左大腿角度': [
    [23, 25],  // 左腰 - 左膝
  ],
  '右大腿角度': [
    [24, 26],  // 右腰 - 右膝
  ],
  '左下腿角度': [
    [25, 27],  // 左膝 - 左足首
  ],
  '右下腿角度': [
    [26, 28],  // 右膝 - 右足首
  ],
  '左上腕角度': [
    [11, 13],  // 左肩 - 左肘
  ],
  '右上腕角度': [
    [12, 14],  // 右肩 - 右肘
  ],
  '左前腕角度': [
    [13, 15],  // 左肘 - 左手首
  ],
  '右前腕角度': [
    [14, 16],  // 右肘 - 右手首
  ],
}

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

    // 体幹ベクトル（腰から肩へ）- 上向きベクトルで0度近辺の値にする
    const trunkVector: [number, number] = [shoulderCenterX - hipCenterX, shoulderCenterY - hipCenterY]

    // 絶対角度計算関数を使用（上向き鉛直軸で計算）
    return calculateAbsoluteAngleWithVertical(trunkVector, true)
  } catch (error) {
    return null
  }
}

// 絶対角度計算関数（atan2ベース、0度前後の値）
const calculateAbsoluteAngleWithVertical = (vector: [number, number], forwardPositive: boolean = true): number | null => {
  try {
    const length = Math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
    if (length === 0) return null

    // atan2を使用してより正確な角度計算
    // 鉛直軸（上向き）からの角度を計算
    // atan2(x, -y) は y軸負方向（上向き）からの角度を計算
    const angleRad = Math.atan2(vector[0], -vector[1])
    
    // 度数法に変換
    let angleDeg = (angleRad * 180) / Math.PI
    
    // forwardPositiveがfalseの場合は符号を反転
    if (!forwardPositive) {
      angleDeg = -angleDeg
    }
    
    return angleDeg
  } catch (error) {
    return null
  }
}

// ベクトルと水平軸のなす角度を計算（足部角度用）
const calculateAbsoluteAngleWithHorizontal = (vector: [number, number]): number | null => {
  try {
    const length = Math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
    if (length === 0) return null

    // atan2を使用して水平軸からの角度を計算
    // x軸正方向（右向き）からの角度を計算
    const angleRad = Math.atan2(vector[1], vector[0])
    
    // 度数法に変換
    let angleDeg = (angleRad * 180) / Math.PI
    
    // -90～+90の範囲に正規化
    if (angleDeg > 90) {
      angleDeg = 180 - angleDeg
    } else if (angleDeg < -90) {
      angleDeg = -180 - angleDeg
    }
    
    return angleDeg
  } catch (error) {
    return null
  }
}

// 新仕様：体幹絶対角度計算
const calculateAbsoluteTrunkAngle = (keypoints: KeyPoint[]): number | null => {
  try {
    const leftShoulder = keypoints[LANDMARK_INDICES.left_shoulder]
    const rightShoulder = keypoints[LANDMARK_INDICES.right_shoulder]
    const leftHip = keypoints[LANDMARK_INDICES.left_hip]
    const rightHip = keypoints[LANDMARK_INDICES.right_hip]
    
    if ([leftShoulder, rightShoulder, leftHip, rightHip].some(kp => kp.visibility < 0.5)) {
      return null
    }
    
    // 肩の中心点と股関節の中心点を計算
    const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2
    const shoulderCenterY = (leftShoulder.y + rightShoulder.y) / 2
    const hipCenterX = (leftHip.x + rightHip.x) / 2
    const hipCenterY = (leftHip.y + rightHip.y) / 2
    
    // 体幹ベクトル（股関節中点→肩中点）- 上向きベクトルで0度近辺の値にする
    const trunkVector: [number, number] = [shoulderCenterX - hipCenterX, shoulderCenterY - hipCenterY]
    
    // 修正済み符号規則: 前傾=負値、後傾=正値
    return calculateAbsoluteAngleWithVertical(trunkVector, false)
  } catch (error) {
    return null
  }
}

// 修正済み：大腿絶対角度計算
const calculateAbsoluteThighAngle = (hip: KeyPoint, knee: KeyPoint): number | null => {
  try {
    if (hip.visibility < 0.5 || knee.visibility < 0.5) {
      return null
    }
    
    // 大腿ベクトル（膝→股関節）
    const thighVector: [number, number] = [hip.x - knee.x, hip.y - knee.y]
    
    // 修正済み符号規則: 膝が後方で正値、前方で負値
    return calculateAbsoluteAngleWithVertical(thighVector, true)
  } catch (error) {
    return null
  }
}

// 修正済み：下腿絶対角度計算
const calculateAbsoluteLowerLegAngle = (knee: KeyPoint, ankle: KeyPoint): number | null => {
  try {
    if (knee.visibility < 0.5 || ankle.visibility < 0.5) {
      return null
    }
    
    // 下腿ベクトル（足首→膝）
    const lowerLegVector: [number, number] = [knee.x - ankle.x, knee.y - ankle.y]
    
    // 修正済み符号規則: 足首が後方で正値、前方で負値
    return calculateAbsoluteAngleWithVertical(lowerLegVector, true)
  } catch (error) {
    return null
  }
}

// 修正済み：上腕絶対角度計算（肘基準鉛直軸）
const calculateAbsoluteUpperArmAngle = (shoulder: KeyPoint, elbow: KeyPoint): number | null => {
  try {
    if (shoulder.visibility < 0.5 || elbow.visibility < 0.5) {
      return null
    }
    
    // 上腕ベクトル（肘→肩）- 肘を基準とした方向
    const upperArmVector: [number, number] = [shoulder.x - elbow.x, shoulder.y - elbow.y]
    
    // 肘を通る鉛直軸との角度: 軸の右側で負値、左側で正値
    return calculateAbsoluteAngleWithVertical(upperArmVector, false)
  } catch (error) {
    return null
  }
}

const calculateAngleBetweenVectors = (vector1: [number, number], vector2: [number, number]): number | null => {
  try {
    // ベクトルの長さを計算
    const length1 = Math.sqrt(vector1[0] * vector1[0] + vector1[1] * vector1[1])
    const length2 = Math.sqrt(vector2[0] * vector2[0] + vector2[1] * vector2[1])
    
    if (length1 === 0 || length2 === 0) return null
    
    // 正規化
    const unitVector1: [number, number] = [vector1[0] / length1, vector1[1] / length1]
    const unitVector2: [number, number] = [vector2[0] / length2, vector2[1] / length2]
    
    // 内積を計算
    const dotProduct = unitVector1[0] * unitVector2[0] + unitVector1[1] * unitVector2[1]
    
    // 数値誤差を防ぐためにclipする
    const clippedDotProduct = Math.max(-1, Math.min(1, dotProduct))
    
    // 角度を計算
    const angleRad = Math.acos(clippedDotProduct)
    const angleDeg = (angleRad * 180) / Math.PI
    
    return angleDeg
  } catch (error) {
    return null
  }
}

// 修正済み：前腕絶対角度計算（画像定義準拠・直接角度版・符号調整）
const calculateAbsoluteForearmAngle = (elbow: KeyPoint, wrist: KeyPoint, side: 'left' | 'right'): number | null => {
  try {
    if (elbow.visibility < 0.5 || wrist.visibility < 0.5) {
      return null
    }
    
    // 前腕ベクトル（肘→手首）- 前腕の自然な方向
    const forearmVector: [number, number] = [wrist.x - elbow.x, wrist.y - elbow.y]
    
    // 鉛直軸（下向き）との角度を直接計算
    const verticalDownVector: [number, number] = [0, 1]  // 鉛直下向き
    
    // 2つのベクトル間の角度を計算
    const rawAngle = calculateAngleBetweenVectors(forearmVector, verticalDownVector)
    
    if (rawAngle === null) return null
    
    // 左右の符号調整（大腿・下腿角度と同じパターンに合わせる）
    if (side === 'left') {
      return rawAngle   // 左側は正の値
    } else {
      return -rawAngle  // 右側は負の値
    }
  } catch (error) {
    return null
  }
}

// 新規追加：足部絶対角度計算
const calculateAbsoluteFootAngle = (ankle: KeyPoint, toe: KeyPoint): number | null => {
  try {
    if (ankle.visibility < 0.5 || toe.visibility < 0.5) {
      return null
    }
    
    // 足部ベクトル（足首→つま先）
    const footVector: [number, number] = [toe.x - ankle.x, toe.y - ankle.y]
    
    // 水平軸との角度計算: 上=正値、下=負値
    return calculateAbsoluteAngleWithHorizontal(footVector)
  } catch (error) {
    return null
  }
}

// 1フレームから拡張された絶対角度を抽出（仕様3対応）
const extractAbsoluteAnglesFromFrame = (keypoints: KeyPoint[]): AbsoluteAngles => {
  const angles: AbsoluteAngles = {
    // 既存角度
    trunk_angle: null,
    left_thigh_angle: null,
    right_thigh_angle: null,
    left_lower_leg_angle: null,
    right_lower_leg_angle: null,
    // 新規追加角度
    left_upper_arm_angle: null,
    right_upper_arm_angle: null,
    left_forearm_angle: null,
    right_forearm_angle: null,
    left_foot_angle: null,
    right_foot_angle: null
  }

  try {
    // ① 体幹角度
    angles.trunk_angle = calculateAbsoluteTrunkAngle(keypoints)

    // ② 大腿角度（左右）
    const leftHip = keypoints[LANDMARK_INDICES.left_hip]
    const leftKnee = keypoints[LANDMARK_INDICES.left_knee]
    angles.left_thigh_angle = calculateAbsoluteThighAngle(leftHip, leftKnee)

    const rightHip = keypoints[LANDMARK_INDICES.right_hip]
    const rightKnee = keypoints[LANDMARK_INDICES.right_knee]
    angles.right_thigh_angle = calculateAbsoluteThighAngle(rightHip, rightKnee)

    // ③ 下腿角度（左右）
    const leftAnkle = keypoints[LANDMARK_INDICES.left_ankle]
    angles.left_lower_leg_angle = calculateAbsoluteLowerLegAngle(leftKnee, leftAnkle)

    const rightAnkle = keypoints[LANDMARK_INDICES.right_ankle]
    angles.right_lower_leg_angle = calculateAbsoluteLowerLegAngle(rightKnee, rightAnkle)

    // ④ 上腕角度（左右）- 新規追加
    const leftShoulder = keypoints[LANDMARK_INDICES.left_shoulder]
    const leftElbow = keypoints[LANDMARK_INDICES.left_elbow]
    angles.left_upper_arm_angle = calculateAbsoluteUpperArmAngle(leftShoulder, leftElbow)

    const rightShoulder = keypoints[LANDMARK_INDICES.right_shoulder]
    const rightElbow = keypoints[LANDMARK_INDICES.right_elbow]
    angles.right_upper_arm_angle = calculateAbsoluteUpperArmAngle(rightShoulder, rightElbow)

    // ⑤ 前腕角度（左右）- 新規追加（符号調整対応）
    const leftWrist = keypoints[LANDMARK_INDICES.left_wrist]
    angles.left_forearm_angle = calculateAbsoluteForearmAngle(leftElbow, leftWrist, 'left')

    const rightWrist = keypoints[LANDMARK_INDICES.right_wrist]
    angles.right_forearm_angle = calculateAbsoluteForearmAngle(rightElbow, rightWrist, 'right')

    // ⑥ 足部角度（左右）- 新規追加
    const leftToe = keypoints[LANDMARK_INDICES.left_foot_index]
    angles.left_foot_angle = calculateAbsoluteFootAngle(leftAnkle, leftToe)

    const rightToe = keypoints[LANDMARK_INDICES.right_foot_index]
    angles.right_foot_angle = calculateAbsoluteFootAngle(rightAnkle, rightToe)

  } catch (error) {
    console.warn('拡張絶対角度の計算でエラーが発生しました:', error)
  }

  return angles
}

export default function PoseVisualizer({ videoUrl, poseData, className = '', problematicAngles = [] }: PoseVisualizerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [currentFrame, setCurrentFrame] = useState(0)
  const [isGrayscale, setIsGrayscale] = useState(false) // グレースケール状態
  const [currentAbsoluteAngles, setCurrentAbsoluteAngles] = useState<AbsoluteAngles>({
    // 既存角度
    trunk_angle: null,
    left_thigh_angle: null,
    right_thigh_angle: null,
    left_lower_leg_angle: null,
    right_lower_leg_angle: null,
    // 新規追加角度
    left_upper_arm_angle: null,
    right_upper_arm_angle: null,
    left_forearm_angle: null,
    right_forearm_angle: null,
    left_foot_angle: null,
    right_foot_angle: null
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
    // 問題のある骨格線のセットを作成
    const problematicConnections = new Set<string>()
    
    problematicAngles.forEach(angleName => {
      const connections = ANGLE_TO_SKELETON_CONNECTIONS[angleName]
      if (connections) {
        connections.forEach(([start, end]) => {
          // 両方向のキーを追加（順序に関係なく一致させる）
          problematicConnections.add(`${start}-${end}`)
          problematicConnections.add(`${end}-${start}`)
        })
      }
    })
    
    // デバッグログ（問題部位がある場合のみ）
    if (problematicAngles.length > 0) {
      console.log('🔴 問題のある角度:', problematicAngles)
      console.log('🔴 赤く表示する骨格線:', Array.from(problematicConnections))
    }
    
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
    POSE_CONNECTIONS.forEach(([startIdx, endIdx]) => {
      const startPoint = keypoints[startIdx]
      const endPoint = keypoints[endIdx]
      
      if (startPoint && endPoint && 
          startPoint.visibility > 0.5 && endPoint.visibility > 0.5) {
        const startX = startPoint.x * videoWidth
        const startY = startPoint.y * videoHeight
        const endX = endPoint.x * videoWidth
        const endY = endPoint.y * videoHeight
        
        // この接続が問題部位かどうか確認
        const connectionKey = `${startIdx}-${endIdx}`
        const isProblematic = problematicConnections.has(connectionKey)
        
        // 問題部位は赤く太く、それ以外は緑
        ctx.strokeStyle = isProblematic ? '#ff0000' : '#00ff00'
        ctx.lineWidth = isProblematic ? 4 : 2
        
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
      
      // リアルタイムで絶対角度を計算・更新
      const absoluteAngles = extractAbsoluteAnglesFromFrame(frameData.keypoints)
      setCurrentAbsoluteAngles(absoluteAngles)
      
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
      setCurrentAbsoluteAngles({
        // 既存角度
        trunk_angle: null,
        left_thigh_angle: null,
        right_thigh_angle: null,
        left_lower_leg_angle: null,
        right_lower_leg_angle: null,
        // 新規追加角度
        left_upper_arm_angle: null,
        right_upper_arm_angle: null,
        left_forearm_angle: null,
        right_forearm_angle: null,
        left_foot_angle: null,
        right_foot_angle: null
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
      {/* グレースケールトグルボタン */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-600">
          キーポイントを目立たせるには、グレースケール表示がおすすめです
        </div>
        <button
          onClick={() => setIsGrayscale(!isGrayscale)}
          className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors duration-200"
        >
          {isGrayscale ? (
            <>
              <span className="text-gray-600">⚫</span>
              <span className="text-sm font-medium">グレースケール</span>
            </>
          ) : (
            <>
              <span className="text-blue-600">🎨</span>
              <span className="text-sm font-medium">カラー</span>
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 動画エリア */}
        <div className="lg:col-span-2">
          <div className="relative inline-block w-full">
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              className={`w-full rounded-lg shadow-lg ${isGrayscale ? 'grayscale-video' : ''}`}
              style={{
                filter: isGrayscale ? 'grayscale(100%)' : 'none',
                transition: 'filter 0.3s ease'
              }}
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

                {/* リアルタイム関節角度表示エリア - 開発環境でのみ表示 */}
                {false && (
          <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800 border-b pb-2">
              リアルタイム関節角度
            </h3>
            
            <div className="space-y-4">
              {/* 角度表示 */}
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <h4 className="font-bold text-blue-800 mb-2">リアルタイム角度</h4>
                
                {/* 体幹角度 */}
                <div className="bg-green-50 rounded-lg p-3 mb-2">
                  <h5 className="font-medium text-green-800 mb-1">体幹角度</h5>
                  <div className="text-lg font-bold text-green-600">
                    {currentAbsoluteAngles.trunk_angle !== null ? 
                      `${currentAbsoluteAngles.trunk_angle.toFixed(1)}°` : 
                      '計算中...'}
                  </div>
                </div>

                {/* 大腿角度 */}
                <div className="bg-purple-50 rounded-lg p-3 mb-2">
                  <h5 className="font-medium text-purple-800 mb-1">大腿角度</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">左:</span>
                      <div className="font-bold text-purple-600">
                        {currentAbsoluteAngles.left_thigh_angle !== null ? 
                          `${currentAbsoluteAngles.left_thigh_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">右:</span>
                      <div className="font-bold text-purple-600">
                        {currentAbsoluteAngles.right_thigh_angle !== null ? 
                          `${currentAbsoluteAngles.right_thigh_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 下腿角度 */}
                <div className="bg-indigo-50 rounded-lg p-3 mb-2">
                  <h5 className="font-medium text-indigo-800 mb-1">下腿角度</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">左:</span>
                      <div className="font-bold text-indigo-600">
                        {currentAbsoluteAngles.left_lower_leg_angle !== null ? 
                          `${currentAbsoluteAngles.left_lower_leg_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">右:</span>
                      <div className="font-bold text-indigo-600">
                        {currentAbsoluteAngles.right_lower_leg_angle !== null ? 
                          `${currentAbsoluteAngles.right_lower_leg_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 上腕角度 - 新規追加 */}
                <div className="bg-orange-50 rounded-lg p-3 mb-2">
                  <h5 className="font-medium text-orange-800 mb-1">上腕角度</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">左:</span>
                      <div className="font-bold text-orange-600">
                        {currentAbsoluteAngles.left_upper_arm_angle !== null ? 
                          `${currentAbsoluteAngles.left_upper_arm_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">右:</span>
                      <div className="font-bold text-orange-600">
                        {currentAbsoluteAngles.right_upper_arm_angle !== null ? 
                          `${currentAbsoluteAngles.right_upper_arm_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 前腕角度 - 新規追加 */}
                <div className="bg-yellow-50 rounded-lg p-3 mb-2">
                  <h5 className="font-medium text-yellow-800 mb-1">前腕角度</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">左:</span>
                      <div className="font-bold text-yellow-600">
                        {currentAbsoluteAngles.left_forearm_angle !== null ? 
                          `${currentAbsoluteAngles.left_forearm_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">右:</span>
                      <div className="font-bold text-yellow-600">
                        {currentAbsoluteAngles.right_forearm_angle !== null ? 
                          `${currentAbsoluteAngles.right_forearm_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 足部角度 - 新規追加 */}
                <div className="bg-pink-50 rounded-lg p-3">
                  <h5 className="font-medium text-pink-800 mb-1">足部角度</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">左:</span>
                      <div className="font-bold text-pink-600">
                        {currentAbsoluteAngles.left_foot_angle !== null ? 
                          `${currentAbsoluteAngles.left_foot_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">右:</span>
                      <div className="font-bold text-pink-600">
                        {currentAbsoluteAngles.right_foot_angle !== null ? 
                          `${currentAbsoluteAngles.right_foot_angle.toFixed(1)}°` : 
                          '--'}
                      </div>
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
        )}
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