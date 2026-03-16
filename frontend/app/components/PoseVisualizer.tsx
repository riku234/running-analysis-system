'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

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

interface ZScoreAnalysis {
  events_detected?: {
    left_strikes?: number[]
    right_strikes?: number[]
    left_offs?: number[]
    right_offs?: number[]
  }
  selected_cycle?: {
    start_frame: number
    end_frame: number
    duration: number
  }
}

interface PoseVisualizerProps {
  videoUrl: string
  poseData: PoseAnalysisData
  className?: string
  problematicAngles?: string[]  // Z-scoreで問題のある角度名のリスト（例: ["trunk_angle", "left_thigh_angle"]）
  showSkeleton?: boolean  // 骨格を表示するかどうか（デフォルト: true）
  zScoreAnalysis?: ZScoreAnalysis  // Z-score分析結果（ランニング周期検出用）
}

// MediaPipeランドマークのインデックス定義（33個）
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

// 24関節点のインデックス定義（s-motion形式）
const KEYPOINT_INDICES_24 = {
  right_hand: 0,
  right_wrist: 1,
  right_elbow: 2,
  right_shoulder: 3,
  left_hand: 4,
  left_wrist: 5,
  left_elbow: 6,
  left_shoulder: 7,
  right_toe: 8,
  right_ball: 9,
  right_heel: 10,
  right_ankle: 11,
  right_knee: 12,
  right_hip: 13,
  left_toe: 14,
  left_ball: 15,
  left_heel: 16,
  left_ankle: 17,
  left_knee: 18,
  left_hip: 19,
  head_top: 20,
  ear: 21,
  body_center: 22,
  pelvis: 23  // 骨盤中心（以前「首/Neck」とラベルされていたが実際はZ座標が腰レベル）
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

// 24関節点の骨格接続定義（s-motion形式）
// インデックス: 0-3(右腕), 4-7(左腕), 8-13(右脚), 14-19(左脚), 20-23(頭部・体幹)
const POSE_CONNECTIONS_24 = [
  // 右腕: 0(手) - 1(手首) - 2(肘) - 3(肩)
  [0, 1], [1, 2], [2, 3],
  // 左腕: 4(手) - 5(手首) - 6(肘) - 7(肩)
  [4, 5], [5, 6], [6, 7],
  // 右脚: 8(爪先) - 9(母指球) - 10(踵) - 11(足首) - 12(膝) - 13(股関節)
  [8, 9], [9, 10], [10, 11], [11, 12], [12, 13],
  // 左脚: 14(爪先) - 15(母指球) - 16(踵) - 17(足首) - 18(膝) - 19(股関節)
  [14, 15], [15, 16], [16, 17], [17, 18], [18, 19],
  // 肩エリア: 3(右肩) - 22(肩中点) - 7(左肩)
  [3, 22], [7, 22],
  // 背骨（体幹）: 22(肩中点) - 23(骨盤中心)
  [22, 23],
  // 骨盤エリア: 13(右股関節) - 23(骨盤中心) - 19(左股関節)
  [13, 23], [19, 23],
  // 頭部: 20(頭頂) - 21(耳) - 22(肩中点)
  [20, 21], [21, 22],
  // 胴体の側面: 3(右肩) - 13(右股関節), 7(左肩) - 19(左股関節)
  [3, 13], [7, 19]
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

interface StandardModelKeypoints {
  status: string
  total_frames: number
  frames: {
    [frameNumber: string]: {
      keypoints: KeyPoint[]
      angles: any
    }
  }
  is_cycle: boolean
  keypoint_count?: number  // 24または33（省略時は33とみなす）
  note: string
}

// ============================================================================
// 標準モデル比較機能の有効/無効フラグ
// ============================================================================
// 一旦無効化されていますが、コードは保持されています。
// 再有効化する場合は、以下のフラグを true に変更してください。
// 
// 再有効化手順:
// 1. このフラグを true に変更: const ENABLE_STANDARD_MODEL_COMPARISON = true
// 2. フロントエンドを再ビルド: docker compose build frontend
// 3. フロントエンドを再起動: docker compose up -d frontend
// ============================================================================
const ENABLE_STANDARD_MODEL_COMPARISON = true

export default function PoseVisualizer({ videoUrl, poseData, className = '', problematicAngles = [], showSkeleton = true, zScoreAnalysis }: PoseVisualizerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null) // 上段の動画用（骨格表示なし）
  const standardModelCanvasRef = useRef<HTMLCanvasElement>(null) // 下段左：標準モデル用
  const userCycleCanvasRef = useRef<HTMLCanvasElement>(null) // 下段右：ユーザー1周期用
  // 描画スケール固定用（初期フレームの体幹長から決定）
  const standardModelScaleRef = useRef<number | null>(null)
  const userCycleScaleRef = useRef<number | null>(null)
  const [currentFrame, setCurrentFrame] = useState(0)
  const [isGrayscale, setIsGrayscale] = useState(false) // グレースケール状態
  const [standardModelKeypoints, setStandardModelKeypoints] = useState<StandardModelKeypoints | null>(null)
  const [standardModelFrameIndex, setStandardModelFrameIndex] = useState(0)
  const [userCycleFrameIndex, setUserCycleFrameIndex] = useState(0) // ユーザー1周期のフレームインデックス
  const [userCycleFrames, setUserCycleFrames] = useState<FramePoseData[]>([]) // ユーザーの1周期のフレームデータ
  
  // 棒人間再生コントロール用
  const [isStandardModelPaused, setIsStandardModelPaused] = useState(false)
  const [isUserCyclePaused, setIsUserCyclePaused] = useState(false)
  
  // ペース同期用：着地タイミングの記録
  const [leftStrikeTime, setLeftStrikeTime] = useState<number | null>(null) // 左足着地のタイミング（秒）
  const [rightStrikeTime, setRightStrikeTime] = useState<number | null>(null) // 右足着地のタイミング（秒）
  const [isManualSyncEnabled, setIsManualSyncEnabled] = useState(false) // 手動同期が有効かどうか
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
  
  // 体幹長に基づいてスケールを固定し、巨大化や縮小を防ぐ
  // keypoints: 0〜1正規化座標のMediaPipeランドマーク
  // scaleState.current に一度だけ決定したスケールを保持する
  const getScaledKeypointsWithFixedTorso = (
    keypoints: KeyPoint[],
    scaleState: { current: number | null }
  ): KeyPoint[] => {
    if (!keypoints || keypoints.length === 0) return keypoints

    // 24関節点か33ランドマークかを判定
    const is24Keypoints = keypoints.length === 24
    
    // 適切なインデックスを選択
    const leftHipIdx = is24Keypoints ? KEYPOINT_INDICES_24.left_hip : LANDMARK_INDICES.left_hip
    const rightHipIdx = is24Keypoints ? KEYPOINT_INDICES_24.right_hip : LANDMARK_INDICES.right_hip
    const leftShoulderIdx = is24Keypoints ? KEYPOINT_INDICES_24.left_shoulder : LANDMARK_INDICES.left_shoulder
    const rightShoulderIdx = is24Keypoints ? KEYPOINT_INDICES_24.right_shoulder : LANDMARK_INDICES.right_shoulder

    const leftHip = keypoints[leftHipIdx]
    const rightHip = keypoints[rightHipIdx]
    const leftShoulder = keypoints[leftShoulderIdx]
    const rightShoulder = keypoints[rightShoulderIdx]

    // 体幹がきちんと取れていない場合はスケール固定を行わない
    if (!leftHip || !rightHip || !leftShoulder || !rightShoulder) return keypoints

    const hipCenterX = (leftHip.x + rightHip.x) / 2
    const hipCenterY = (leftHip.y + rightHip.y) / 2
    const shoulderCenterY = (leftShoulder.y + rightShoulder.y) / 2
    const torsoLength = Math.abs(hipCenterY - shoulderCenterY)

    // 体幹長の妥当性チェック（異常に小さい値や大きすぎる値を除外）
    const MIN_TORSO_LENGTH = 0.05  // 最小体幹長（画面の5%）
    const MAX_TORSO_LENGTH = 0.8   // 最大体幹長（画面の80%）
    
    if (!Number.isFinite(torsoLength) || torsoLength <= 0 || 
        torsoLength < MIN_TORSO_LENGTH || torsoLength > MAX_TORSO_LENGTH) {
      // スケールが既に決定されている場合は、そのまま使用
      if (scaleState.current != null) {
        console.warn('⚠️ 体幹長が異常値ですが、既存のスケールを使用します:', {
          torsoLength,
          currentScale: scaleState.current
        })
      } else {
        // スケールが未決定の場合は、スケール固定を行わない
        console.warn('⚠️ 体幹長が異常値のため、スケール固定をスキップします:', {
          torsoLength,
          min: MIN_TORSO_LENGTH,
          max: MAX_TORSO_LENGTH
        })
        return keypoints
      }
    }

    // キャンバス高さに対して体幹長が約18%になるようにスケールを固定
    const TARGET_TORSO_LENGTH_NORMALIZED = 0.18

    if (scaleState.current == null) {
      const rawScale = TARGET_TORSO_LENGTH_NORMALIZED / torsoLength
      // 極端な拡大・縮小を防ぐためにスケールに上下限を設ける（より厳しく）
      // 0.5〜2.0の範囲に制限（以前は0.3〜3.0だったが、巨大化を防ぐため厳しく）
      const clampedScale = Math.min(2.0, Math.max(0.5, rawScale))
      scaleState.current = clampedScale
      console.log('🎚 体幹長ベースの描画スケール決定:', {
        torsoLength: torsoLength.toFixed(4),
        rawScale: rawScale.toFixed(4),
        clampedScale: clampedScale.toFixed(4),
        note: 'スケールは0.5〜2.0の範囲に制限されています'
      })
    }

    const scale = scaleState.current ?? 1

    // 体幹の中心（腰の中心）を基準にスケーリング
    return keypoints.map((kp, index) => {
      if (!kp) return kp
      // visibility が極端に低い点はそのままにしておく
      if (kp.visibility !== undefined && kp.visibility < 0.05) return kp

      const dx = kp.x - hipCenterX
      const dy = kp.y - hipCenterY

      const scaledX = hipCenterX + dx * scale
      const scaledY = hipCenterY + dy * scale

      return {
        ...kp,
        x: scaledX,
        y: scaledY
      }
    })
  }
  
  // キーポイントを腰中心でキャンバス中央に固定し「その場走り」にする
  // 各フレームの腰中心をキャンバス中央に移動し、全関節の相対位置は保持する
  const centerKeypointsInPlace = (keypoints: KeyPoint[]): KeyPoint[] => {
    if (!keypoints || keypoints.length === 0) return keypoints

    // 24関節点か33ランドマークかを判定
    const is24Keypoints = keypoints.length === 24

    const leftHipIdx = is24Keypoints ? KEYPOINT_INDICES_24.left_hip : LANDMARK_INDICES.left_hip
    const rightHipIdx = is24Keypoints ? KEYPOINT_INDICES_24.right_hip : LANDMARK_INDICES.right_hip

    const leftHip = keypoints[leftHipIdx]
    const rightHip = keypoints[rightHipIdx]

    if (!leftHip || !rightHip) return keypoints

    const hipCenterX = (leftHip.x + rightHip.x) / 2
    const hipCenterY = (leftHip.y + rightHip.y) / 2
    const targetCenterX = 0.5  // キャンバス水平中央
    const targetCenterY = 0.45 // キャンバスやや上（腰は体の中間より少し上）
    const offsetX = targetCenterX - hipCenterX
    const offsetY = targetCenterY - hipCenterY

    return keypoints.map(kp => {
      if (!kp) return kp
      return {
        ...kp,
        x: kp.x + offsetX,
        y: kp.y + offsetY
      }
    })
  }

  // 動画の現在時刻から対応するフレームを取得
  const getCurrentFrameData = (): FramePoseData | null => {
    if (!videoRef.current || !poseData.pose_data.length) return null
    
    const currentTime = videoRef.current.currentTime
    const fps = poseData.video_info.fps || 30
    const frameNumber = Math.floor(currentTime * fps)
    
    return poseData.pose_data.find(frame => frame.frame_number === frameNumber) || null
  }
  
  // キーポイントを描画（ユーザーの骨格と標準モデルの骨格）
  const drawKeypoints = useCallback((ctx: CanvasRenderingContext2D, keypoints: KeyPoint[], videoWidth: number, videoHeight: number, xOffset: number = 0, color: { point: string; line: string } = { point: '#ff0000', line: '#00ff00' }, fixXPosition: boolean = false, use24Keypoints: boolean = false, highlightProblematic: boolean = true, uniformScale: boolean = false, jointPointRadius: number = -1): void => {
    if (!keypoints || keypoints.length === 0) {
      return
    }
    
    // 24関節点か33ランドマークかを判定（キーポイント数または引数で判定）
    const is24Keypoints = use24Keypoints || keypoints.length === 24
    
    // 使用する接続関係を選択
    const connections = is24Keypoints ? POSE_CONNECTIONS_24 : POSE_CONNECTIONS
    
    // 問題のある骨格線のセットを作成（highlightProblematicがfalseまたは24関節点の場合はスキップ）
    const problematicConnections = new Set<string>()
    const problematicPointIndices = new Set<number>()
    if (highlightProblematic && !is24Keypoints) {
      problematicAngles.forEach(angleName => {
        const angleConnections = ANGLE_TO_SKELETON_CONNECTIONS[angleName]
        if (angleConnections) {
          angleConnections.forEach(([start, end]) => {
            // 両方向のキーを追加（順序に関係なく一致させる）
            problematicConnections.add(`${start}-${end}`)
            problematicConnections.add(`${end}-${start}`)
            // 問題のある関節点のインデックスも記録
            problematicPointIndices.add(start)
            problematicPointIndices.add(end)
          })
        }
      })
    }
    
    // 均等スケーリング: キャンバスのアスペクト比に関係なく正しい比率で描画
    // uniformScale=true の場合、XとYを同じスケールで描画し、余白部分は中央に配置
    let scaleW = videoWidth
    let scaleH = videoHeight
    let drawOffsetX = 0
    let drawOffsetY = 0
    if (uniformScale) {
      const uniformSize = Math.min(videoWidth, videoHeight)
      scaleW = uniformSize
      scaleH = uniformSize
      drawOffsetX = (videoWidth - uniformSize) / 2
      drawOffsetY = (videoHeight - uniformSize) / 2
    }
    
    // 可視性の閾値を下げる（より多くのキーポイントを表示）
    const VISIBILITY_THRESHOLD_LOW = 0.2  // 低可視性でも表示
    const VISIBILITY_THRESHOLD_HIGH = 0.5  // 高可視性（通常表示）
    
    // 座標変換ヘルパー
    const toScreenX = (nx: number) => nx * scaleW + drawOffsetX + xOffset
    const toScreenY = (ny: number) => ny * scaleH + drawOffsetY
    
    // キーポイントを描画（可視性に応じてサイズと透明度を調整）
    // jointPointRadius: -1=デフォルト, 0=描画しない, 正数=指定サイズ
    if (jointPointRadius !== 0) {
      keypoints.forEach((point, index) => {
        if (!point) return
        
        // 可視性が低い場合でも表示（薄く表示）
        if (point.visibility > VISIBILITY_THRESHOLD_LOW) {
          // X座標を固定する場合（その場で走らせる）
          const x = fixXPosition 
            ? (videoWidth / 2) + xOffset  // X座標を中央に固定
            : toScreenX(point.x)
          const y = toScreenY(point.y)
          
          // 問題のある関節点かどうか確認
          const isProblematicPoint = problematicPointIndices.has(index)
          
          // 可視性に応じてポイントサイズと透明度を調整
          let pointSize: number
          if (jointPointRadius > 0) {
            // 明示的にサイズ指定（標準モデル等で小さくしたい場合）
            pointSize = isProblematicPoint ? jointPointRadius + 1 : jointPointRadius
          } else {
            // デフォルト: 問題部位は大きく、可視性で調整
            pointSize = isProblematicPoint ? 6 : (point.visibility > VISIBILITY_THRESHOLD_HIGH ? 5 : 3)
          }
          const alpha = Math.min(1.0, point.visibility * 1.5) // 可視性を強調
          
          ctx.save()
          ctx.globalAlpha = alpha
          ctx.fillStyle = isProblematicPoint ? '#ff0000' : color.point
          
          // ポイントを描画
          ctx.beginPath()
          ctx.arc(x, y, pointSize, 0, 2 * Math.PI)
          ctx.fill()
          ctx.restore()
        }
      })
    }
    
    // 骨格の線を描画（より柔軟な条件）
    connections.forEach(([startIdx, endIdx]) => {
      // インデックスの範囲チェック
      if (startIdx >= keypoints.length || endIdx >= keypoints.length) {
        return
      }
      
      const startPoint = keypoints[startIdx]
      const endPoint = keypoints[endIdx]
      
      // 両方のキーポイントが存在し、可視性が閾値以上の場合
      if (startPoint && endPoint && 
          startPoint.visibility > VISIBILITY_THRESHOLD_LOW && 
          endPoint.visibility > VISIBILITY_THRESHOLD_LOW) {
        
        // X座標を固定する場合（その場で走らせる）
        const startX = fixXPosition 
          ? (videoWidth / 2) + xOffset  // X座標を中央に固定
          : toScreenX(startPoint.x)
        const startY = toScreenY(startPoint.y)
        const endX = fixXPosition 
          ? (videoWidth / 2) + xOffset  // X座標を中央に固定
          : toScreenX(endPoint.x)
        const endY = toScreenY(endPoint.y)
        
        // この接続が問題部位かどうか確認（24関節点の場合は常にfalse）
        const connectionKey = `${startIdx}-${endIdx}`
        const isProblematic = !is24Keypoints && problematicConnections.has(connectionKey)
        
        // 可視性に応じて線の太さと透明度を調整
        const minVisibility = Math.min(startPoint.visibility, endPoint.visibility)
        const lineWidth = isProblematic ? 4 : (minVisibility > VISIBILITY_THRESHOLD_HIGH ? 2.5 : 1.5)
        const lineAlpha = Math.min(1.0, minVisibility * 1.3) // 可視性を強調
        
        ctx.save()
        ctx.globalAlpha = lineAlpha
        ctx.strokeStyle = isProblematic ? '#ff0000' : color.line
        ctx.lineWidth = lineWidth
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'
        
        ctx.beginPath()
        ctx.moveTo(startX, startY)
        ctx.lineTo(endX, endY)
        ctx.stroke()
        ctx.restore()
      }
    })
  }, [problematicAngles])
  
  // 標準モデルの棒人間を描画（左キャンバス用）
  const drawStandardModelSkeleton = useCallback(() => {
    const canvas = standardModelCanvasRef.current
    if (!canvas || !standardModelKeypoints) {
      console.log('⚠️ 標準モデル描画スキップ:', { hasCanvas: !!canvas, hasKeypoints: !!standardModelKeypoints })
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // キャンバスサイズを設定（親要素のサイズを取得）
    const parent = canvas.parentElement
    if (!parent) return
    
    const width = parent.clientWidth || 640
    const height = parent.clientHeight || 360
    
    canvas.width = width
    canvas.height = height
    
    const frameKey = standardModelFrameIndex.toString()
    const frameData = standardModelKeypoints.frames[frameKey]
    if (!frameData) {
      console.log('⚠️ 標準モデルフレームデータが見つかりません:', { frameKey, availableFrames: Object.keys(standardModelKeypoints.frames).slice(0, 5) })
      return
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 標準モデルを描画（黒色・問題箇所ハイライトなし）- 体幹長ベースの固定スケール + その場走り
    const scaledKeypoints = getScaledKeypointsWithFixedTorso(frameData.keypoints, standardModelScaleRef)
    const centeredKeypoints = centerKeypointsInPlace(scaledKeypoints)
    // 24関節点かどうかを判定（keypoint_countまたはキーポイント数で判定）
    const is24Keypoints = standardModelKeypoints.keypoint_count === 24 || centeredKeypoints.length === 24
    drawKeypoints(ctx, centeredKeypoints, canvas.width, canvas.height, 0, {
      point: '#000000',
      line: '#000000'
    }, false, is24Keypoints, false, true, 0)  // uniformScale=true, jointPointRadius=0: 関節丸印なし
    
    // ログを減らす（毎フレーム出力すると多すぎるため、10フレームごとに出力）
    if (standardModelFrameIndex % 10 === 0) {
      console.log('✅ 標準モデル描画完了:', { frameIndex: standardModelFrameIndex, frameKey, width, height })
    }
  }, [standardModelFrameIndex, standardModelKeypoints, drawKeypoints])
  
  // ユーザー1周期の棒人間を描画（右キャンバス用）
  const drawUserCycleSkeleton = useCallback(() => {
    const canvas = userCycleCanvasRef.current
    if (!canvas || !userCycleFrames.length) {
      console.log('⚠️ ユーザー1周期描画スキップ:', { hasCanvas: !!canvas, cycleFramesCount: userCycleFrames.length })
      return
    }
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // キャンバスサイズを設定（親要素のサイズを取得）
    const parent = canvas.parentElement
    if (!parent) return
    
    const width = parent.clientWidth || 640
    const height = parent.clientHeight || 360
    
    canvas.width = width
    canvas.height = height
    
    const frameData = userCycleFrames[userCycleFrameIndex]
    if (!frameData || !frameData.keypoints) {
      console.log('⚠️ ユーザー1周期フレームデータが見つかりません:', { frameIndex: userCycleFrameIndex, totalFrames: userCycleFrames.length })
      return
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // ユーザー1周期を描画（黒色ベース、問題箇所のみ赤色）- 体幹長ベースの固定スケール + その場走り
    const scaledKeypoints = getScaledKeypointsWithFixedTorso(frameData.keypoints, userCycleScaleRef)
    const centeredKeypoints = centerKeypointsInPlace(scaledKeypoints)
    drawKeypoints(ctx, centeredKeypoints, canvas.width, canvas.height, 0, {
      point: '#000000',
      line: '#000000'
    })
    
    // ログを減らす（毎フレーム出力すると多すぎるため、10フレームごとに出力）
    if (userCycleFrameIndex % 10 === 0) {
      console.log('✅ ユーザー1周期描画完了:', { frameIndex: userCycleFrameIndex, totalFrames: userCycleFrames.length, width, height })
    }
  }, [userCycleFrameIndex, userCycleFrames, drawKeypoints])
  
  // Canvas描画の更新
  const updateCanvas = useCallback(() => {
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
      // 骨格表示が有効な場合のみ描画
      if (showSkeleton) {
        // ユーザーの骨格を描画（黒色ベース、問題箇所のみ赤色）
        drawKeypoints(ctx, frameData.keypoints, canvas.width, canvas.height, 0, { point: '#000000', line: '#000000' })
      }
    }
    
    // 標準モデルの骨格を左にオフセットして描画（無効化中、コードは保持）
    if (ENABLE_STANDARD_MODEL_COMPARISON && standardModelKeypoints && standardModelFrameIndex >= 0) {
      const frameKey = String(standardModelFrameIndex)
      const standardModelFrame = standardModelKeypoints.frames[frameKey]
      
      if (standardModelFrame && standardModelFrame.keypoints) {
        // ユーザーの骨格の中心位置を計算（基準点として使用）
        let userCenterX = canvas.width * 0.5  // デフォルト：画面中央
        if (frameData && frameData.landmarks_detected && frameData.keypoints) {
          // 腰の中心位置を計算（左腰と右腰の中点）
          const leftHip = frameData.keypoints[23]  // 左腰
          const rightHip = frameData.keypoints[24]  // 右腰
          if (leftHip && rightHip && leftHip.visibility > 0.5 && rightHip.visibility > 0.5) {
            userCenterX = ((leftHip.x + rightHip.x) / 2) * canvas.width
          }
        }
        
        // 標準モデルをユーザーの左側（後ろ）に配置
        // ユーザーの中心から左に、画面幅の20%分オフセット
        const xOffset = userCenterX - canvas.width * 0.2
        
        // デバッグログは最初の数回だけ表示（大量のログを防ぐため）
        if (standardModelFrameIndex === 0 || standardModelFrameIndex % 10 === 0) {
          console.log('🔵 標準モデル描画実行:', { 
            xOffset, 
            userCenterX,
            keypointsCount: standardModelFrame.keypoints.length,
            canvasWidth: canvas.width,
            standardModelFrameIndex
          })
        }
        // 上段オーバーレイ用の標準モデル描画にも同じ固定スケールを適用
        const scaledStandardKeypoints = getScaledKeypointsWithFixedTorso(standardModelFrame.keypoints, standardModelScaleRef)
        drawKeypoints(ctx, scaledStandardKeypoints, canvas.width, canvas.height, xOffset, { point: '#6699ff', line: '#6699ff' })
      } else {
        console.warn('⚠️ 標準モデルフレームデータが見つかりません:', { frameKey, availableFrames: Object.keys(standardModelKeypoints.frames) })
      }
    }
    
    if (frameData && frameData.landmarks_detected) {
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
  }, [poseData, showSkeleton, standardModelKeypoints, standardModelFrameIndex, problematicAngles])
  
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
  
  // 標準モデルキーポイントデータを取得（無効化中、コードは保持）
  useEffect(() => {
    if (!ENABLE_STANDARD_MODEL_COMPARISON) {
      console.log('⚠️ 標準モデル比較機能は現在無効化されています')
      return
    }
    
    const fetchStandardModelKeypoints = async () => {
      try {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        console.log('📥 標準モデルキーポイントデータを取得中...')
        const response = await fetch('/api/feature_extraction/standard_model/keypoints')
        if (!response.ok) {
          throw new Error(`API呼び出しエラー: ${response.status}`)
        }
        const data: StandardModelKeypoints = await response.json()
        console.log('✅ 標準モデルキーポイントデータ取得成功:', {
          total_frames: data.total_frames,
          is_cycle: data.is_cycle,
          note: data.note
        })
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        setStandardModelKeypoints(data)
      } catch (error) {
        console.error('❌ 標準モデルキーポイントデータの取得に失敗:', error)
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
      }
    }
    
    fetchStandardModelKeypoints()
  }, [])
  
  // ユーザーのランニング1周期を抽出
  useEffect(() => {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('🔄 ユーザー1周期抽出開始:', {
      hasZScoreAnalysis: !!zScoreAnalysis,
      zScoreAnalysisType: typeof zScoreAnalysis,
      hasSelectedCycle: !!zScoreAnalysis?.selected_cycle,
      hasPoseData: !!poseData.pose_data?.length,
      poseDataLength: poseData.pose_data?.length || 0
    })
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    
    if (!poseData.pose_data || !poseData.pose_data.length) {
      console.warn('⚠️ pose_dataが空です')
      setUserCycleFrames([])
      return
    }
    
    let finalFrames: FramePoseData[] = []
    
    // 方法1: zScoreAnalysis.selected_cycleから抽出
    if (zScoreAnalysis?.selected_cycle) {
      const { start_frame, end_frame } = zScoreAnalysis.selected_cycle
      console.log('🔍 selected_cycleから抽出を試みます:', { start_frame, end_frame })
      
      // フレーム番号でフィルタリング
      const cycleFrames = poseData.pose_data.filter(
        frame => frame.frame_number >= start_frame && frame.frame_number <= end_frame
      )
      
      if (cycleFrames.length > 0) {
        finalFrames = cycleFrames
        console.log('✅ selected_cycleから抽出成功:', {
          start_frame,
          end_frame,
          cycleFramesCount: finalFrames.length
        })
      } else {
        // フレーム番号が見つからない場合、インデックスベースで試す
        console.log('⚠️ フレーム番号でマッチしませんでした。インデックスベースで試します')
        const startIdx = Math.min(start_frame, poseData.pose_data.length - 1)
        const endIdx = Math.min(end_frame, poseData.pose_data.length - 1)
        finalFrames = poseData.pose_data.slice(startIdx, endIdx + 1)
        console.log('✅ インデックスベースで抽出成功:', {
          startIdx,
          endIdx,
          cycleFramesCount: finalFrames.length
        })
      }
    }
    
    // 方法2: selected_cycleが存在しない場合、最初の200フレームをフォールバックとして使用
    if (finalFrames.length === 0) {
      const fallbackFrameCount = 200
      const availableFrames = Math.min(fallbackFrameCount, poseData.pose_data.length)
      finalFrames = poseData.pose_data.slice(0, availableFrames)
      console.log('📋 フォールバック: 最初の200フレームを使用:', {
        fallbackFrameCount: availableFrames,
        totalFrames: poseData.pose_data.length,
        firstFrameNumber: finalFrames[0]?.frame_number,
        lastFrameNumber: finalFrames[finalFrames.length - 1]?.frame_number
      })
    }
    
    console.log('✅ ユーザー1周期を抽出完了:', {
      cycleFramesCount: finalFrames.length,
      totalFrames: poseData.pose_data.length,
      firstFrameNumber: finalFrames[0]?.frame_number,
      lastFrameNumber: finalFrames[finalFrames.length - 1]?.frame_number
    })
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    
    setUserCycleFrames(finalFrames)
  }, [zScoreAnalysis, poseData.pose_data])
  
  // zScoreAnalysisの構造を初期化時に一度だけ表示
  useEffect(() => {
    if (zScoreAnalysis) {
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
      console.log('🔍 zScoreAnalysisの構造:', {
        hasSelectedCycle: !!zScoreAnalysis.selected_cycle,
        hasEventsDetected: !!zScoreAnalysis.events_detected,
        selectedCycle: zScoreAnalysis.selected_cycle,
        eventsDetected: zScoreAnalysis.events_detected,
        fullStructure: zScoreAnalysis
      })
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    } else {
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
      console.log('⚠️ zScoreAnalysisが提供されていません')
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    }
  }, [zScoreAnalysis])
  
  // 標準モデル骨格を描画（updateCanvas内で処理済み）
  
  
  
  // 標準モデルとユーザー1周期を同期してループ再生（無効化中、コードは保持）
  useEffect(() => {
    if (!ENABLE_STANDARD_MODEL_COMPARISON) {
      return
    }
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('🔄 アニメーションループ初期化:', {
      hasStandardModelKeypoints: !!standardModelKeypoints,
      hasUserCycleFrames: !!userCycleFrames.length,
      userCycleFramesCount: userCycleFrames.length,
      standardModelTotalFrames: standardModelKeypoints?.total_frames,
      isManualSyncEnabled,
      leftStrikeTime,
      rightStrikeTime
    })
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    
    // 標準モデルがなくてもユーザー側のアニメーションは動かす
    const totalStandardFrames = standardModelKeypoints?.total_frames || 0
    const totalUserFrames = userCycleFrames.length || 0
    
    if (totalStandardFrames === 0 && totalUserFrames === 0) {
      console.warn('⚠️ アニメーション対象のデータがありません')
      return
    }
    
    // ペースを合わせる：標準モデルとユーザー1周期が同じ時間で1周期を完了するように調整
    // 標準モデルがない場合は101（デフォルトの標準モデルフレーム数）を使用
    const standardCycleDuration = totalStandardFrames > 0 ? totalStandardFrames : 101
    const userCycleDuration = totalUserFrames > 0 ? totalUserFrames : 1
    
    // 手動同期の場合と自動同期の場合で速度比を計算
    let speedRatio: number
    if (isManualSyncEnabled && leftStrikeTime !== null && rightStrikeTime !== null) {
      speedRatio = userCycleDuration / standardCycleDuration
      console.log('✅ 手動同期アニメーション開始:', {
        leftStrikeTime: leftStrikeTime.toFixed(3),
        rightStrikeTime: rightStrikeTime.toFixed(3),
        standardCycleDuration,
        userCycleDuration,
        speedRatio,
        note: `標準モデルとユーザーサイクルを同じ時間で1周期を完了します（速度比: ${speedRatio.toFixed(2)}）`
      })
    } else {
      speedRatio = userCycleDuration / standardCycleDuration
      console.log('✅ 自動同期アニメーション開始:', {
        totalStandardFrames,
        totalUserFrames,
        standardCycleDuration,
        userCycleDuration,
        speedRatio,
        note: `標準モデルを基準に、ユーザー1周期は${speedRatio.toFixed(2)}倍の速度で再生されます`
      })
    }
    
    let animationFrameId: number
    let startTime = Date.now()
    const fps = 30 // アニメーションのフレームレート
    let lastStandardFrame = -1
    let lastUserFrame = -1
    // 一時停止時のフレーム保持用
    let pausedStandardFrame = 0
    let pausedUserFrame = 0
    let standardPauseOffset = 0
    let userPauseOffset = 0
    let wasStandardPaused = false
    let wasUserPaused = false
    
    const animate = () => {
      const elapsed = Date.now() - startTime
      const frameTime = 1000 / fps
      const currentFrame = Math.floor(elapsed / frameTime)
      
      // 標準モデルのフレームインデックス（ループ）- 一時停止対応
      if (totalStandardFrames > 0 && !isStandardModelPaused) {
        if (wasStandardPaused) {
          // 一時停止から復帰: オフセットを調整して現在のフレームから続ける
          standardPauseOffset = currentFrame - pausedStandardFrame
          wasStandardPaused = false
        }
        const standardFrame = (currentFrame - standardPauseOffset) % totalStandardFrames
        if (standardFrame !== lastStandardFrame) {
          setStandardModelFrameIndex(standardFrame)
          lastStandardFrame = standardFrame
          pausedStandardFrame = currentFrame - standardPauseOffset
        }
      } else if (isStandardModelPaused) {
        if (!wasStandardPaused) {
          wasStandardPaused = true
        }
      }
      
      // ユーザー1周期のフレームインデックス（ループ、速度を調整）- 一時停止対応
      if (totalUserFrames > 0) {
        if (!isUserCyclePaused) {
          if (wasUserPaused) {
            userPauseOffset = currentFrame - pausedUserFrame
            wasUserPaused = false
          }
          const adjustedFrame = Math.floor((currentFrame - userPauseOffset) * speedRatio) % totalUserFrames
          if (adjustedFrame !== lastUserFrame) {
            setUserCycleFrameIndex(adjustedFrame)
            lastUserFrame = adjustedFrame
            pausedUserFrame = currentFrame - userPauseOffset
          }
        } else {
          if (!wasUserPaused) {
            wasUserPaused = true
          }
        }
      }
      
      animationFrameId = requestAnimationFrame(animate)
    }
    
    animate()
    
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
    }
  }, [standardModelKeypoints, userCycleFrames, isManualSyncEnabled, leftStrikeTime, rightStrikeTime, poseData.video_info.fps, isStandardModelPaused, isUserCyclePaused])
  
  // 棒人間のフレームコントロール
  const handleStandardModelStepForward = useCallback(() => {
    if (!standardModelKeypoints) return
    setStandardModelFrameIndex(prev => (prev + 1) % standardModelKeypoints.total_frames)
  }, [standardModelKeypoints])

  const handleStandardModelStepBackward = useCallback(() => {
    if (!standardModelKeypoints) return
    setStandardModelFrameIndex(prev => (prev - 1 + standardModelKeypoints.total_frames) % standardModelKeypoints.total_frames)
  }, [standardModelKeypoints])

  const handleUserCycleStepForward = useCallback(() => {
    if (!userCycleFrames.length) return
    setUserCycleFrameIndex(prev => (prev + 1) % userCycleFrames.length)
  }, [userCycleFrames])

  const handleUserCycleStepBackward = useCallback(() => {
    if (!userCycleFrames.length) return
    setUserCycleFrameIndex(prev => (prev - 1 + userCycleFrames.length) % userCycleFrames.length)
  }, [userCycleFrames])

  // 標準モデルフレームインデックスが変更されたときにキャンバスを更新（無効化中、コードは保持）
  useEffect(() => {
    if (!ENABLE_STANDARD_MODEL_COMPARISON) return
    drawStandardModelSkeleton()
  }, [standardModelFrameIndex, drawStandardModelSkeleton])
  
  // ユーザー1周期フレームインデックスが変更されたときにキャンバスを更新（無効化中、コードは保持）
  useEffect(() => {
    if (!ENABLE_STANDARD_MODEL_COMPARISON) return
    drawUserCycleSkeleton()
  }, [userCycleFrameIndex, drawUserCycleSkeleton])
  
  
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
    <div className={`${className} space-y-6`}>
      {/* メインエリア：動画（左2/3）+ お手本棒人間（右1/3） */}
      <div className="flex gap-4">
        {/* 左側：撮影した動画のリプレイ（2/3幅） */}
        <div className="w-2/3">
          <h3 className="text-lg font-semibold mb-2">撮影した動画</h3>
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
          </div>
        </div>

        {/* 右側：お手本棒人間（1/3幅） */}
        {ENABLE_STANDARD_MODEL_COMPARISON && (
          <div className="w-1/3 flex flex-col">
            <h3 className="text-lg font-semibold mb-2">
              お手本フォーム
              <span className="ml-2 text-xs font-normal text-gray-400">
                {standardModelFrameIndex + 1} / {standardModelKeypoints?.total_frames || 0}
              </span>
            </h3>
            <div className="relative flex-1 bg-gray-100 rounded-lg min-h-0" style={{ aspectRatio: '3/4' }}>
              <canvas
                ref={standardModelCanvasRef}
                className="absolute top-0 left-0 w-full h-full rounded-lg"
              />
            </div>
            <div className="flex items-center justify-center gap-2 mt-2">
              <button
                onClick={handleStandardModelStepBackward}
                disabled={!isStandardModelPaused}
                className={`px-3 py-1 text-sm rounded ${isStandardModelPaused ? 'bg-gray-200 hover:bg-gray-300 text-gray-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                title="1フレーム戻る"
              >
                ⏪
              </button>
              <button
                onClick={() => setIsStandardModelPaused(prev => !prev)}
                className={`px-4 py-1 text-sm rounded font-medium ${isStandardModelPaused ? 'bg-blue-500 hover:bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
              >
                {isStandardModelPaused ? '▶ 再生' : '⏸ 一時停止'}
              </button>
              <button
                onClick={handleStandardModelStepForward}
                disabled={!isStandardModelPaused}
                className={`px-3 py-1 text-sm rounded ${isStandardModelPaused ? 'bg-gray-200 hover:bg-gray-300 text-gray-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                title="1フレーム進む"
              >
                ⏩
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ペース同期用のUI（一時非表示、コードは保持） */}
      {/*
      {ENABLE_STANDARD_MODEL_COMPARISON && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-700">ペース同期設定</h4>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isManualSyncEnabled}
                onChange={(e) => setIsManualSyncEnabled(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-600">手動同期を有効にする</span>
            </label>
          </div>
        
        {isManualSyncEnabled && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 mb-3">
              動画を再生し、着地の瞬間に一時停止してボタンを押してください
            </p>
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={() => {
                  if (videoRef.current) {
                    const currentTime = videoRef.current.currentTime
                    setLeftStrikeTime(currentTime)
                    console.log('👟 左足着地を設定:', currentTime.toFixed(3), '秒')
                  }
                }}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  leftStrikeTime !== null
                    ? 'bg-green-500 text-white'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                👟 左足着地を設定
                {leftStrikeTime !== null && (
                  <span className="ml-2 text-xs">({leftStrikeTime.toFixed(2)}秒)</span>
                )}
              </button>
              <button
                onClick={() => {
                  if (videoRef.current) {
                    const currentTime = videoRef.current.currentTime
                    setRightStrikeTime(currentTime)
                    console.log('👟 右足着地を設定:', currentTime.toFixed(3), '秒')
                  }
                }}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  rightStrikeTime !== null
                    ? 'bg-green-500 text-white'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                👟 右足着地を設定
                {rightStrikeTime !== null && (
                  <span className="ml-2 text-xs">({rightStrikeTime.toFixed(2)}秒)</span>
                )}
              </button>
              {(leftStrikeTime !== null || rightStrikeTime !== null) && (
                <button
                  onClick={() => {
                    setLeftStrikeTime(null)
                    setRightStrikeTime(null)
                    console.log('🔄 着地タイミングをリセット')
                  }}
                  className="px-4 py-2 rounded-md text-sm font-medium bg-gray-500 text-white hover:bg-gray-600"
                >
                  🔄 リセット
                </button>
              )}
            </div>
            {leftStrikeTime !== null && rightStrikeTime !== null && (
              <div className="mt-2 text-xs text-gray-600">
                <p>✅ 両足の着地タイミングが設定されました</p>
                <p>1サイクルの長さ: {Math.abs(rightStrikeTime - leftStrikeTime).toFixed(2)}秒</p>
              </div>
            )}
          </div>
        )}
        </div>
      )}
      */}

      {/* ユーザー棒人間比較セクション（一時非表示、コードは保持） */}
      {/* 
      {ENABLE_STANDARD_MODEL_COMPARISON && (
        <div>
          <h3 className="text-lg font-semibold mb-2">棒人間同士の比較</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">
                あなたの走り（1周期）
                <span className="ml-2 text-xs text-gray-400">
                  フレーム: {userCycleFrameIndex + 1} / {userCycleFrames.length || 0}
                </span>
              </h4>
              <div className="relative w-full bg-gray-100 rounded-lg" style={{ aspectRatio: '16/9' }}>
                <canvas
                  ref={userCycleCanvasRef}
                  className="absolute top-0 left-0 w-full h-full rounded-lg"
                />
              </div>
              <div className="flex items-center justify-center gap-2 mt-2">
                <button
                  onClick={handleUserCycleStepBackward}
                  disabled={!isUserCyclePaused}
                  className={`px-3 py-1 text-sm rounded ${isUserCyclePaused ? 'bg-gray-200 hover:bg-gray-300 text-gray-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                  title="1フレーム戻る"
                >
                  ⏪
                </button>
                <button
                  onClick={() => setIsUserCyclePaused(prev => !prev)}
                  className={`px-4 py-1 text-sm rounded font-medium ${isUserCyclePaused ? 'bg-blue-500 hover:bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
                >
                  {isUserCyclePaused ? '▶ 再生' : '⏸ 一時停止'}
                </button>
                <button
                  onClick={handleUserCycleStepForward}
                  disabled={!isUserCyclePaused}
                  className={`px-3 py-1 text-sm rounded ${isUserCyclePaused ? 'bg-gray-200 hover:bg-gray-300 text-gray-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                  title="1フレーム進む"
                >
                  ⏩
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      */}
    </div>
  )
} 