'use client'

import { useState, useMemo, useRef, useEffect } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { ChevronRight, ChevronLeft, Play, Info, CheckCircle, Activity } from 'lucide-react'

interface ZScoreData {
  [event: string]: {
    [angle: string]: number
  }
}

interface PoseFrame {
  frame_number: number
  timestamp: number
  keypoints: Array<{
    x: number
    y: number
    z: number
    visibility: number
  }>
  landmarks_detected: boolean
}

interface AnalysisResultLiteProps {
  zScoreData: ZScoreData | null
  adviceData?: {
    ai_advice?: {
      title?: string
      message?: string
      key_points?: string[]
    }
    raw_issues?: Array<{
      name: string
      severity?: string
      angle?: string
      target_metric?: string
      observation?: string
      cause?: string
      action?: string
      drill?: {
        name?: string
        url?: string
      }
    }>
  } | null
  videoUrl?: string | null
  poseData?: PoseFrame[] | null
}

// MediaPipeの骨格接続定義
const POSE_CONNECTIONS = [
  // 顔の輪郭
  [0, 1], [1, 2], [2, 3], [3, 7],
  [0, 4], [4, 5], [5, 6], [6, 8],
  // 肩
  [11, 12],
  // 左腕
  [11, 13], [13, 15],
  // 右腕
  [12, 14], [14, 16],
  // 胴体
  [11, 23], [12, 24], [23, 24],
  // 左脚
  [23, 25], [25, 27],
  // 右脚
  [24, 26], [26, 28],
]

// 角度計算関数（3点から角度を計算）
const calculateAngle = (p1: { x: number, y: number }, p2: { x: number, y: number }, p3: { x: number, y: number }): number => {
  const radians1 = Math.atan2(p1.y - p2.y, p1.x - p2.x)
  const radians2 = Math.atan2(p3.y - p2.y, p3.x - p2.x)
  let angle = Math.abs((radians1 - radians2) * 180 / Math.PI)
  if (angle > 180) angle = 360 - angle
  return angle
}

// --- 新規コンポーネント: 追従ラベル付き動画プレイヤー ---
const DynamicTrackingVideo = ({ videoUrl, poseData }: { videoUrl?: string | null, poseData?: PoseFrame[] | null }) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const animationFrameRef = useRef<number | null>(null)
  const loggedEmptyPoseData = useRef(false)
  const loggedNoMatch = useRef(false)
  
  // スローモーション設定と動画読み込み
  useEffect(() => {
    if (!videoUrl || !videoRef.current) {
      console.warn('⚠️ videoUrlまたはvideoRefがありません:', { videoUrl, hasVideoRef: !!videoRef.current })
      return
    }

    const video = videoRef.current
    console.log('📹 動画読み込み開始:', videoUrl)
    
    // 動画の読み込み完了を待ってから再生
    const handleCanPlay = () => {
      if (video && video.readyState >= 2) { // HAVE_CURRENT_DATA以上
        console.log('✅ 動画再生可能状態:', { readyState: video.readyState, duration: video.duration })
        video.playbackRate = 0.3 // 0.3倍速（よりスローモーション）
        video.play().catch(err => {
          // 自動再生がブロックされた場合は警告のみ（ユーザー操作で再生可能）
          if (err.name !== 'AbortError' && err.name !== 'NotAllowedError') {
            console.warn('⚠️ 動画再生エラー:', err)
          } else {
            console.info('ℹ️ 自動再生がブロックされました（ユーザー操作で再生可能）')
          }
        })
      }
    }

    const handleLoadedData = () => {
      console.log('✅ 動画データ読み込み完了:', { readyState: video.readyState })
      if (video.readyState >= 2) {
        video.playbackRate = 0.3
        video.play().catch(err => {
          if (err.name !== 'AbortError' && err.name !== 'NotAllowedError') {
            console.warn('⚠️ 動画再生エラー:', err)
          }
        })
      }
    }

    const handleError = (e: Event) => {
      console.error('❌ 動画読み込みエラー:', {
        error: e,
        networkState: video.networkState,
        errorCode: video.error?.code,
        errorMessage: video.error?.message
      })
    }

    // 既に読み込まれている場合
    if (video.readyState >= 2) {
      console.log('✅ 動画は既に読み込まれています')
      video.playbackRate = 0.3
      video.play().catch(err => {
        if (err.name !== 'AbortError' && err.name !== 'NotAllowedError') {
          console.warn('⚠️ 動画再生エラー:', err)
        }
      })
    } else {
      // イベントリスナーを追加
      video.addEventListener('canplay', handleCanPlay, { once: true })
      video.addEventListener('loadeddata', handleLoadedData, { once: true })
      video.addEventListener('error', handleError, { once: true })
      
      // 動画を明示的に読み込む
      video.load()
      console.log('📥 動画読み込みリクエスト送信')
    }

    return () => {
      video.removeEventListener('canplay', handleCanPlay)
      video.removeEventListener('loadeddata', handleLoadedData)
      video.removeEventListener('error', handleError)
    }
  }, [videoUrl])

  // requestAnimationFrameを使ってより頻繁に更新（スローモーション時の同期を改善）
  useEffect(() => {
    const updateTime = () => {
      if (videoRef.current) {
        setCurrentTime(videoRef.current.currentTime)
      }
      animationFrameRef.current = requestAnimationFrame(updateTime)
    }
    
    if (videoUrl && videoRef.current) {
      animationFrameRef.current = requestAnimationFrame(updateTime)
    }
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [videoUrl])

  const handleTimeUpdate = () => {
    // フォールバックとしてもtimeupdateイベントを監視
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  // 指定された時刻に近いランドマークを取得する関数（精度向上）
  const getCurrentLandmarks = () => {
    if (!poseData || poseData.length === 0) {
      // デバッグログは初回のみ表示（無限ループを防ぐ）
      if (!loggedEmptyPoseData.current) {
        console.warn('⚠️ poseDataが空です:', { 
          poseData: poseData ? '存在するが空' : 'null/undefined',
          length: poseData?.length || 0,
          type: typeof poseData,
          isArray: Array.isArray(poseData)
        })
        loggedEmptyPoseData.current = true
      }
      return null
    }
    
    // フレーム番号ベースのマッチングも試す（より正確）
    if (videoRef.current && poseData.length > 0) {
      const video = videoRef.current
      // FPS計算を改善（タイムスタンプが0の場合の処理）
      let fps = 30 // デフォルト値
      if (poseData.length > 1) {
        const timeDiff = poseData[1].timestamp - poseData[0].timestamp
        if (timeDiff > 0) {
          fps = 1 / timeDiff
        } else if (poseData[0].frame_number !== undefined && poseData[1].frame_number !== undefined) {
          // フレーム番号からFPSを推定
          const frameDiff = poseData[1].frame_number - poseData[0].frame_number
          if (frameDiff > 0 && video.duration > 0) {
            fps = frameDiff / video.duration
          }
        }
      }
      
      const frameNumber = Math.round(currentTime * fps)
      
      // フレーム番号で直接マッチング
      const frameMatch = poseData.find(frame => frame.frame_number === frameNumber)
      if (frameMatch && frameMatch.keypoints) {
        return frameMatch.keypoints
      }
    }
    
    // タイムスタンプベースのマッチング（フォールバック）
    if (poseData.length > 0) {
      const closestFrame = poseData.reduce((prev, curr) => {
        const prevDiff = Math.abs((prev.timestamp || 0) - currentTime)
        const currDiff = Math.abs((curr.timestamp || 0) - currentTime)
        return currDiff < prevDiff ? curr : prev
      })
      
      // より緩い閾値（0.1秒以内、スローモーション時でも表示されるように）
      if (Math.abs((closestFrame.timestamp || 0) - currentTime) < 0.1) {
        if (closestFrame.keypoints && closestFrame.keypoints.length > 0) {
          return closestFrame.keypoints
        }
      }
      
      // 最後のフォールバック: 最初のフレームを表示
      if (poseData[0] && poseData[0].keypoints && poseData[0].keypoints.length > 0) {
        return poseData[0].keypoints
      }
    }
    
    // デバッグログは初回のみ表示
    if (!(getCurrentLandmarks as any)._noMatchLogged) {
      console.warn('⚠️ ランドマークが見つかりません:', { 
        currentTime, 
        poseDataLength: poseData?.length,
        firstFrameTimestamp: poseData?.[0]?.timestamp,
        lastFrameTimestamp: poseData?.[poseData.length - 1]?.timestamp
      })
      ;(getCurrentLandmarks as any)._noMatchLogged = true
    }
    return null
  }

  const landmarks = getCurrentLandmarks()
  
  // デバッグ用ログ
  useEffect(() => {
    if (videoUrl) {
      console.log('📹 videoUrl:', videoUrl)
    }
    if (poseData) {
      console.log('🦴 poseData:', { length: poseData.length, firstFrame: poseData[0] })
    }
    if (landmarks) {
      console.log('📍 landmarks:', { count: landmarks.length })
    }
  }, [videoUrl, poseData, landmarks])

  // ラベル位置計算ヘルパー（小さめのサイズに調整）
  const getStyle = (index: number, defaultPos: { x: number, y: number }) => {
    if (landmarks && landmarks[index]) {
      return {
        left: `${landmarks[index].x * 100}%`,
        top: `${landmarks[index].y * 100}%`,
      }
    }
    return {
      left: `${defaultPos.x}%`,
      top: `${defaultPos.y}%`,
    }
  }

  // 角度の可視化用ヘルパー
  const getAngleLine = (p1Index: number, p2Index: number, p3Index: number | null = null) => {
    if (!landmarks) return null
    
    const p1 = landmarks[p1Index]
    const p2 = landmarks[p2Index]
    if (!p1 || !p2) return null

    const x1 = p1.x * 100
    const y1 = p1.y * 100
    const x2 = p2.x * 100
    const y2 = p2.y * 100

    // 角度がある場合は3点目も使用
    if (p3Index !== null && landmarks[p3Index]) {
      const p3 = landmarks[p3Index]
      const x3 = p3.x * 100
      const y3 = p3.y * 100
      return { x1, y1, x2, y2, x3, y3 }
    }

    return { x1, y1, x2, y2 }
  }

  return (
    <div className="relative w-full h-full bg-purple-900 rounded-[2rem] overflow-hidden shadow-2xl border-4 border-purple-700 group">
      {/* 1. 動画レイヤー */}
      <div className="absolute inset-0 bg-purple-900">
        {videoUrl ? (
          <>
            <video
              ref={videoRef}
              src={videoUrl}
              className="w-full h-full object-contain"
              muted
              loop
              playsInline
              preload="auto"
              onTimeUpdate={handleTimeUpdate}
              onError={(e) => {
                console.error('❌ 動画読み込みエラー:', {
                  error: e,
                  videoUrl: videoUrl,
                  videoElement: videoRef.current
                })
                if (videoRef.current) {
                  console.error('動画要素の状態:', {
                    readyState: videoRef.current.readyState,
                    networkState: videoRef.current.networkState,
                    error: videoRef.current.error
                  })
                }
              }}
              onLoadedMetadata={() => {
                console.log('✅ 動画メタデータ読み込み完了:', {
                  videoUrl: videoUrl,
                  duration: videoRef.current?.duration,
                  videoWidth: videoRef.current?.videoWidth,
                  videoHeight: videoRef.current?.videoHeight
                })
              }}
              onLoadedData={() => {
                console.log('✅ 動画データ読み込み完了:', videoUrl)
                if (videoRef.current) {
                  videoRef.current.playbackRate = 0.3
                  videoRef.current.play().catch(err => {
                    console.warn('⚠️ 自動再生がブロックされました:', err)
                    // ユーザー操作で再生可能にする
                    const tryPlay = () => {
                      if (videoRef.current) {
                        videoRef.current.play().catch(console.error)
                      }
                    }
                    document.addEventListener('click', tryPlay, { once: true })
                    document.addEventListener('touchstart', tryPlay, { once: true })
                  })
                }
              }}
              onCanPlay={() => {
                console.log('✅ 動画再生可能:', videoUrl)
                if (videoRef.current && videoRef.current.readyState >= 2) {
                  videoRef.current.playbackRate = 0.3
                  videoRef.current.play().catch(err => {
                    if (err.name !== 'AbortError' && err.name !== 'NotAllowedError') {
                      console.warn('⚠️ 動画再生エラー:', err)
                    }
                  })
                }
              }}
              onPlay={() => {
                console.log('▶️ 動画再生開始')
              }}
              onPause={() => {
                console.log('⏸️ 動画一時停止')
              }}
            />
            {/* 紫のフィルターオーバーレイ - 背景を消すために濃く */}
            <div className="absolute inset-0 bg-purple-800/85 mix-blend-multiply pointer-events-none"></div>
            {/* 追加のフィルターレイヤーで背景をさらに消す */}
            <div className="absolute inset-0 bg-purple-900/50 mix-blend-overlay pointer-events-none"></div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-purple-800 text-white">
            <p>動画を読み込み中...</p>
          </div>
        )}
      </div>

      {/* 2. 骨格オーバーレイ (SVG描画) - 全て白 */}
      {landmarks && landmarks.length > 0 ? (
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ opacity: 0.9, zIndex: 10 }}>
          {/* 骨格線を描画 */}
          {POSE_CONNECTIONS.map(([start, end], idx) => {
            if (start >= landmarks.length || end >= landmarks.length) return null
            const startPoint = landmarks[start]
            const endPoint = landmarks[end]
            if (!startPoint || !endPoint || (startPoint.visibility !== undefined && startPoint.visibility < 0.3) || (endPoint.visibility !== undefined && endPoint.visibility < 0.3)) return null
            
            return (
              <line
                key={idx}
                x1={`${startPoint.x * 100}%`}
                y1={`${startPoint.y * 100}%`}
                x2={`${endPoint.x * 100}%`}
                y2={`${endPoint.y * 100}%`}
                stroke="white"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )
          })}
          
          {/* 関節ポイントを描画 */}
          {landmarks.map((point, idx) => {
            if (!point || (point.visibility !== undefined && point.visibility < 0.3)) return null
            return (
              <circle
                key={idx}
                cx={`${point.x * 100}%`}
                cy={`${point.y * 100}%`}
                r="4"
                fill="white"
                stroke="purple"
                strokeWidth="1"
              />
            )
          })}
        </svg>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-white/50 text-sm">骨格データを読み込み中...</p>
        </div>
      )}

      {/* 3. 角度測定線とラベル - 全て白 */}
      <div className="absolute inset-0 pointer-events-none">
        {/* A. 姿勢（上半身の傾き）: 肩(11,12)から腰(23,24)への線 */}
        {landmarks && landmarks[11] && landmarks[12] && landmarks[23] && landmarks[24] && (
          <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.9 }}>
            {/* 垂直基準線（破線） */}
            <line
              x1={`${((landmarks[11].x + landmarks[12].x) / 2) * 100}%`}
              y1={`${((landmarks[11].y + landmarks[12].y) / 2) * 100}%`}
              x2={`${((landmarks[11].x + landmarks[12].x) / 2) * 100}%`}
              y2={`${((landmarks[23].y + landmarks[24].y) / 2) * 100}%`}
              stroke="white"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              opacity="0.6"
            />
            {/* 体幹線（実線） */}
            <line
              x1={`${((landmarks[11].x + landmarks[12].x) / 2) * 100}%`}
              y1={`${((landmarks[11].y + landmarks[12].y) / 2) * 100}%`}
              x2={`${((landmarks[23].x + landmarks[24].x) / 2) * 100}%`}
              y2={`${((landmarks[23].y + landmarks[24].y) / 2) * 100}%`}
              stroke="white"
              strokeWidth="2"
            />
          </svg>
        )}
        <div 
          className="absolute transition-all duration-75 ease-linear"
          style={getStyle(11, { x: 45, y: 25 })}
        >
          <div className="bg-white/90 backdrop-blur-sm border border-white text-purple-900 px-2 py-1 rounded-lg shadow-lg text-xs font-bold whitespace-nowrap">
            姿勢
          </div>
        </div>

        {/* B. 着地（膝下の振り出し）: 膝(25)から足首(27)への線と垂直ベクトルとの角度 */}
        {landmarks && landmarks[25] && landmarks[27] && (
          <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.9 }}>
            {/* 膝から足首への線（下腿ベクトル） */}
            <line
              x1={`${landmarks[25].x * 100}%`}
              y1={`${landmarks[25].y * 100}%`}
              x2={`${landmarks[27].x * 100}%`}
              y2={`${landmarks[27].y * 100}%`}
              stroke="white"
              strokeWidth="2"
            />
            {/* 垂直基準線（破線）- 足首から上方向へ */}
            <line
              x1={`${landmarks[27].x * 100}%`}
              y1={`${landmarks[27].y * 100}%`}
              x2={`${landmarks[27].x * 100}%`}
              y2={`${(landmarks[27].y - 0.15) * 100}%`}
              stroke="white"
              strokeWidth="1.5"
              strokeDasharray="3 3"
              opacity="0.6"
            />
          </svg>
        )}
        <div 
          className="absolute transition-all duration-75 ease-linear"
          style={getStyle(27, { x: 55, y: 80 })}
        >
          <div className="bg-white/90 backdrop-blur-sm border border-white text-purple-900 px-2 py-1 rounded-lg shadow-lg text-xs font-bold whitespace-nowrap">
            着地
          </div>
        </div>

        {/* C. スイング（上下動）: 腰(23)から膝(25)への線と垂直動き */}
        {landmarks && landmarks[23] && landmarks[25] && (
          <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.9 }}>
            {/* 腰から膝への線 */}
            <line
              x1={`${landmarks[23].x * 100}%`}
              y1={`${landmarks[23].y * 100}%`}
              x2={`${landmarks[25].x * 100}%`}
              y2={`${landmarks[25].y * 100}%`}
              stroke="white"
              strokeWidth="2"
            />
            {/* 垂直動きの矢印（簡易表示） */}
            <line
              x1={`${((landmarks[23].x + landmarks[25].x) / 2) * 100}%`}
              y1={`${Math.min(landmarks[23].y, landmarks[25].y) * 100}%`}
              x2={`${((landmarks[23].x + landmarks[25].x) / 2) * 100}%`}
              y2={`${Math.max(landmarks[23].y, landmarks[25].y) * 100}%`}
              stroke="white"
              strokeWidth="1.5"
              strokeDasharray="4 2"
              opacity="0.7"
              markerEnd="url(#arrowhead-white)"
            />
            <defs>
              <marker id="arrowhead-white" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="white" />
              </marker>
            </defs>
          </svg>
        )}
        <div 
          className="absolute transition-all duration-75 ease-linear"
          style={getStyle(25, { x: 60, y: 55 })}
        >
          <div className="bg-white/90 backdrop-blur-sm border border-white text-purple-900 px-2 py-1 rounded-lg shadow-lg text-xs font-bold whitespace-nowrap">
            スイング
          </div>
        </div>
      </div>

      {/* UI装飾 */}
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/30">
        <Activity className="text-white animate-pulse w-4 h-4" />
        <span className="text-white font-mono text-xs tracking-wider opacity-90">スローモーション解析中</span>
      </div>
    </div>
  )
}

export default function AnalysisResultLite({ zScoreData, adviceData, videoUrl, poseData }: AnalysisResultLiteProps) {
  // ページ管理 (0~4 の全5ページ)
  const [currentStep, setCurrentStep] = useState(0)
  const totalSteps = 5

  // ページ遷移関数
  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, totalSteps - 1))
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

  // デバッグログ
  useEffect(() => {
    console.log('📊 AnalysisResultLite Props:', {
      hasZScoreData: !!zScoreData,
      hasAdviceData: !!adviceData,
      videoUrl: videoUrl?.substring(0, 50) + '...',
      poseDataLength: poseData?.length || 0,
      adviceDataRaw: adviceData ? {
        hasRawIssues: !!adviceData.raw_issues,
        rawIssuesLength: adviceData.raw_issues?.length || 0
      } : null
    })
  }, [zScoreData, adviceData, videoUrl, poseData])

  // Z値から3要素のスコアを計算
  const radarData = useMemo(() => {
    if (!zScoreData) {
      return []
    }

    // 全イベントから最大のZ値を取得
    const getMaxZScore = (angleNames: string[]): number => {
      let maxZ = 0
      Object.values(zScoreData).forEach(eventData => {
        angleNames.forEach(angleName => {
          // 直接マッチング
          let value = eventData[angleName]
          
          // 見つからない場合、様々なパターンを試す
          if (value === undefined) {
            value = eventData[angleName.replace('角度', '')] ||
                   eventData[`${angleName}_z`] ||
                   eventData[`left_${angleName}_z`] ||
                   eventData[`right_${angleName}_z`]
          }
          
          // まだ見つからない場合、部分マッチング
          if (value === undefined) {
            const matchingKey = Object.keys(eventData).find(key => 
              key.includes(angleName) || 
              key.includes(angleName.replace('角度', '')) ||
              key.toLowerCase().includes(angleName.toLowerCase())
            )
            if (matchingKey) {
              value = eventData[matchingKey]
            }
          }
          
          if (value !== undefined && !isNaN(value) && typeof value === 'number') {
            const absZ = Math.abs(value)
            if (absZ > maxZ) maxZ = absZ
          }
        })
      })
      return maxZ
    }

    // 3要素のZ値を取得（複数の角度名を試す）
    const postureZ = Math.max(
      getMaxZScore(['体幹角度', 'trunk_angle', 'trunk']),
      getMaxZScore(['trunk_angle_z'])
    )
    const landingZ = Math.max(
      getMaxZScore(['右下腿角度', '左下腿角度', 'shank_angle', 'right_shank_angle', 'left_shank_angle']),
      getMaxZScore(['右下腿', '左下腿', 'shank'])
    )
    const swingZ = Math.max(
      getMaxZScore(['右大腿角度', '左大腿角度', 'thigh_angle', 'right_thigh_angle', 'left_thigh_angle']),
      getMaxZScore(['右大腿', '左大腿', 'thigh'])
    )

    // Z値を100点満点スコアに変換（Z=0が100点、Z>=10が0点）
    const zToScore = (z: number): number => {
      if (z === 0) return 100
      if (z >= 10) return 0
      return Math.max(0, Math.round(100 - (z / 10) * 100))
    }

    const postureScore = zToScore(postureZ)
    const landingScore = zToScore(landingZ)
    const swingScore = zToScore(swingZ)

    return [
      {
        category: '姿勢',
        score: postureScore,
        fullMark: 100
      },
      {
        category: '着地',
        score: landingScore,
        fullMark: 100
      },
      {
        category: 'スイング',
        score: swingScore,
        fullMark: 100
      }
    ]
  }, [zScoreData])

  // 総合スコア計算（3要素の平均）
  const totalScore = useMemo(() => {
    if (radarData.length === 0) return 0
    const sum = radarData.reduce((acc, item) => acc + item.score, 0)
    return Math.round(sum / radarData.length)
  }, [radarData])

  // One Big Thing（最優先課題）- Z値が最も大きい課題を1つだけ選択
  const oneBigThing = useMemo(() => {
    if (!adviceData) {
      console.warn('⚠️ adviceDataがありません')
      return null
    }

    // 複数のパターンからraw_issuesを取得
    let rawIssues: any[] = []
    
    // パターン1: adviceData.raw_issuesが直接存在
    if (adviceData.raw_issues && Array.isArray(adviceData.raw_issues)) {
      rawIssues = adviceData.raw_issues
    }
    // パターン2: adviceData.issuesが存在
    else if ((adviceData as any).issues && Array.isArray((adviceData as any).issues)) {
      rawIssues = (adviceData as any).issues
    }
    // パターン3: advice_results内にraw_issuesが存在
    else if ((adviceData as any).advice_results?.raw_issues && Array.isArray((adviceData as any).advice_results.raw_issues)) {
      rawIssues = (adviceData as any).advice_results.raw_issues
    }
    // パターン4: 直接配列として渡されている
    else if (Array.isArray(adviceData)) {
      rawIssues = adviceData
    }

    if (rawIssues.length === 0) {
      // raw_issuesが空の場合でも、ai_adviceがあれば表示可能な情報を返す
      const aiAdvice = (adviceData as any).ai_advice
      if (aiAdvice && (aiAdvice.title || aiAdvice.message)) {
        console.log('ℹ️ raw_issuesは空ですが、ai_adviceがあります:', aiAdvice)
        return {
          name: aiAdvice.title || '良好なフォームです',
          observation: aiAdvice.message || '特筆すべき統計的な乖離は見当たりません。',
          cause: '',
          action: aiAdvice.key_points?.join('\n') || '',
          drillName: 'フォーム維持',
          drillPoints: aiAdvice.key_points || ['現在の素晴らしいフォームを維持してください'],
          drillUrl: null
        }
      }
      
      console.warn('⚠️ raw_issuesが空です:', { 
        adviceDataKeys: Object.keys(adviceData),
        adviceDataType: typeof adviceData,
        hasAiAdvice: !!(adviceData as any).ai_advice,
        adviceDataStructure: JSON.stringify(adviceData).substring(0, 500)
      })
      return null
    }
    
    console.log('✅ raw_issuesを取得:', { count: rawIssues.length, issues: rawIssues.map((i: any) => i.name || i.issue || 'unknown') })

    // Z値データから各課題のZ値を取得して、最も大きいものを選択
    let maxZScore = 0
    let targetIssue = rawIssues[0]

    // 角度名のマッピング（target_metric → 実際のZ値データのキー名）
    const angleMapping: Record<string, string[]> = {
      "trunk_angle_z": ["体幹角度", "trunk_angle_z"],
      "shank_angle_z": ["右下腿角度", "左下腿角度", "right_shank_angle_z", "left_shank_angle_z"],
      "thigh_angle_z": ["右大腿角度", "左大腿角度", "right_thigh_angle_z", "left_thigh_angle_z"],
      "knee_angle_z": ["右膝角度", "左膝角度", "right_knee_angle_z", "left_knee_angle_z"]
    }

    // 各課題について、対応するZ値を取得
    for (const issue of rawIssues) {
      if (!zScoreData) continue

      const targetMetric = issue.target_metric || issue.angle || (issue as any).metric
      if (!targetMetric) continue

      const checkAngles = angleMapping[targetMetric] || [targetMetric, issue.angle, (issue as any).metric].filter(Boolean)

      // 角度名からZ値を取得
      let issueZScore = 0
      Object.values(zScoreData).forEach((eventData: any) => {
        for (const angleName of checkAngles) {
          const angleValue = eventData[angleName] || 
                            eventData[angleName.replace('角度', '')] ||
                            eventData[`${angleName}_z`] ||
                            eventData[`left_${angleName}_z`] ||
                            eventData[`right_${angleName}_z`]
          
          if (angleValue !== undefined) {
            const absZ = Math.abs(angleValue)
            if (absZ > issueZScore) issueZScore = absZ
          }
        }
      })

      // severityがhighの場合は優先度を上げる（Z値に+2.0を加算）
      const priorityZ = (issue.severity === 'high' || (issue as any).priority === 'high') ? issueZScore + 2.0 : issueZScore

      if (priorityZ > maxZScore) {
        maxZScore = priorityZ
        targetIssue = issue
      }
    }

    // ドリルのポイントを抽出（actionから）
    const drillPoints: string[] = []
    if (targetIssue.action) {
      // actionから箇条書きを抽出
      const lines = targetIssue.action.split('\n').filter(line => line.trim())
      lines.forEach(line => {
        // 「・」「-」「1.」などの箇条書き記号を除去
        const cleaned = line.replace(/^[・\-\d\.\s]+/, '').trim()
        if (cleaned && cleaned.length > 0) {
          drillPoints.push(cleaned)
        }
      })
    }

    // ドリル名がactionに含まれている場合は抽出
    let drillName = targetIssue.drill?.name || ''
    if (!drillName && targetIssue.action) {
      // actionの最初の行をドリル名として使用
      const firstLine = targetIssue.action.split('\n')[0]?.trim()
      if (firstLine && firstLine.length < 50) {
        drillName = firstLine
      }
    }

    return {
      name: targetIssue.name,
      observation: targetIssue.observation || '',
      cause: targetIssue.cause || '',
      action: targetIssue.action || '',
      drillName: drillName || '改善トレーニング',
      drillPoints: drillPoints.length > 0 ? drillPoints : [
        '姿勢を意識する',
        'ゆっくりと動作を行う',
        '呼吸を整える'
      ],
      drillUrl: targetIssue.drill?.url || null
    }
  }, [adviceData, zScoreData])

  // oneBigThingのデバッグログ
  useEffect(() => {
    if (oneBigThing) {
      console.log('✅ oneBigThing:', {
        name: oneBigThing.name,
        drillName: oneBigThing.drillName,
        drillPointsCount: oneBigThing.drillPoints.length,
        hasDrillUrl: !!oneBigThing.drillUrl
      })
    } else {
      console.warn('⚠️ oneBigThingがnullです')
    }
  }, [oneBigThing])

  if (!zScoreData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Z値データがありません</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-full h-screen bg-gray-50 overflow-hidden text-slate-800 font-sans selection:bg-red-100">
      
      {/* メインカードエリア */}
      <div className="flex-1 px-6 pt-6 pb-2 flex items-center justify-center">
        <div className="w-full max-w-7xl h-full bg-white rounded-[2rem] shadow-xl overflow-hidden relative flex flex-col border border-gray-200">
          
          {/* --- Header Decoration (Xebio Line) --- */}
          <div className="h-2 w-full flex">
            <div className="h-full w-1/3 bg-blue-900"></div>
            <div className="h-full w-2/3 bg-red-600"></div>
          </div>

          {/* --- Page 0: スコア（左側）+ 指標の説明（右側）を統合 - iPad最適化 --- */}
          {currentStep === 0 && (
            <div className="flex-1 flex flex-col p-4 md:p-6 animate-fade-in overflow-hidden">
              {/* タイトル */}
              <div className="text-center mb-4 shrink-0">
                <h1 className="text-2xl md:text-3xl font-extrabold text-blue-900 mb-1 tracking-tight">あなたのランニングスコア</h1>
                <p className="text-sm md:text-base text-gray-500 font-medium">AI解析による総合診断結果</p>
              </div>

              {/* メインコンテンツ: 左側にスコア、右側に説明 */}
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 overflow-y-auto px-2">
                {/* 左側: スコア表示 */}
                <div className="flex flex-col items-center justify-center space-y-4">
                  {/* レーダーチャート表示エリア */}
                  <div className="w-full max-w-sm h-[240px] md:h-[280px] bg-slate-50 rounded-2xl flex items-center justify-center relative border border-slate-200 p-3 md:p-4">
                    {radarData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="#e5e7eb" />
                          <PolarAngleAxis 
                            dataKey="category" 
                            tick={{ fill: '#1e3a8a', fontSize: 12, fontWeight: 700 }}
                          />
                          <PolarRadiusAxis 
                            angle={90} 
                            domain={[0, 100]} 
                            tick={{ fill: '#64748b', fontSize: 10 }}
                          />
                          <Radar
                            name="スコア"
                            dataKey="score"
                            stroke="#dc2626"
                            fill="#dc2626"
                            fillOpacity={0.6}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="text-center text-gray-400">
                        <p className="mb-2 font-bold text-sm">レーダーチャート表示エリア</p>
                        <div className="flex gap-2 text-xs justify-center mt-2">
                          <span className="px-3 py-1 bg-blue-900 text-white rounded-full font-bold">姿勢</span>
                          <span className="px-3 py-1 bg-red-600 text-white rounded-full font-bold">着地</span>
                          <span className="px-3 py-1 bg-sky-500 text-white rounded-full font-bold">スイング</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 総合スコア */}
                  <div className="flex items-baseline gap-2">
                    <span className="text-blue-900 text-base md:text-lg font-bold">総合スコア</span>
                    <span className="text-5xl md:text-6xl font-extrabold text-red-600 tracking-tighter drop-shadow-sm">{totalScore}</span>
                    <span className="text-xl md:text-2xl font-bold text-red-600">点</span>
                  </div>
                </div>

                {/* 右側: 指標の説明 */}
                <div className="flex flex-col justify-center space-y-3 md:space-y-4">
                  <h2 className="text-lg md:text-xl font-bold text-blue-900 mb-2 text-center">3つの指標について</h2>
                  
                  {/* ① 姿勢 (Navy/Blue - Stability) */}
                  <div className="bg-white p-3 md:p-4 rounded-xl flex items-start gap-3 border-2 border-blue-100 shadow-sm">
                    <div className="w-8 h-8 md:w-10 md:h-10 bg-blue-900 rounded-lg flex items-center justify-center text-white font-bold text-sm md:text-base shadow-md shrink-0">1</div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base md:text-lg font-bold text-blue-900 mb-1">姿勢</h3>
                      <p className="text-xs md:text-sm font-bold text-slate-700 mb-1 leading-snug">
                        「走りの土台となる、上半身の角度」
                      </p>
                      <p className="text-xs md:text-sm text-slate-500 leading-relaxed">
                        走っている時の背筋が伸びているか、前かがみや後ろ反りになりすぎていないかを分析します。適切な前傾姿勢は、重心移動をスムーズにし、省エネで走るための鍵となります。
                      </p>
                    </div>
                  </div>

                  {/* ② 着地 (Red - Power/Impact) */}
                  <div className="bg-white p-3 md:p-4 rounded-xl flex items-start gap-3 border-2 border-red-100 shadow-sm">
                    <div className="w-8 h-8 md:w-10 md:h-10 bg-red-600 rounded-lg flex items-center justify-center text-white font-bold text-sm md:text-base shadow-md shrink-0">2</div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base md:text-lg font-bold text-red-700 mb-1">着地</h3>
                      <p className="text-xs md:text-sm font-bold text-slate-700 mb-1 leading-snug">
                        「ブレーキをかけない、スムーズな接地」
                      </p>
                      <p className="text-xs md:text-sm text-slate-500 leading-relaxed">
                        足が地面に着く瞬間の「すねの角度」を見ます。足が体の重心より前に出すぎているとブレーキがかかってしまいます。スムーズに次の一歩へつなげるための重要な指標です。
                      </p>
                    </div>
                  </div>

                  {/* ③ スイング (Sky Blue/Light Blue - Speed) */}
                  <div className="bg-white p-3 md:p-4 rounded-xl flex items-start gap-3 border-2 border-sky-100 shadow-sm">
                    <div className="w-8 h-8 md:w-10 md:h-10 bg-sky-500 rounded-lg flex items-center justify-center text-white font-bold text-sm md:text-base shadow-md shrink-0">3</div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base md:text-lg font-bold text-sky-700 mb-1">スイング</h3>
                      <p className="text-xs md:text-sm font-bold text-slate-700 mb-1 leading-snug">
                        「ダイナミックな脚の運び」
                      </p>
                      <p className="text-xs md:text-sm text-slate-500 leading-relaxed">
                        太ももがしっかりと上がり、脚が前に出ているかを分析します。ここが弱いと歩幅（ストライド）が伸び悩みます。アクセル全開で走るための「脚の振り出し」の強さを表します。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* --- Page 1: 計測ポイント可視化動画 --- */}
          {currentStep === 1 && (
            <div className="flex-1 p-8 animate-fade-in flex flex-col items-center overflow-y-auto">
              <div className="w-full max-w-5xl h-full flex flex-col">
                <div className="text-center mb-6 shrink-0">
                  <h2 className="text-3xl font-bold text-blue-900">AIによる解析ポイント</h2>
                  <p className="text-slate-500 mt-2">あなたの走りを3つの視点でリアルタイムに計測しています</p>
                </div>
                
                <div className="flex-1 relative min-h-[400px]">
                  {/* 新規作成した動画コンポーネントを使用 */}
                  <DynamicTrackingVideo videoUrl={videoUrl} poseData={poseData} />
                </div>

                <div className="flex justify-center gap-8 mt-6 shrink-0">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-900 rounded-full"></div>
                    <span className="font-bold text-blue-900">姿勢 (体幹)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-600 rounded-full"></div>
                    <span className="font-bold text-red-600">着地 (足首)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-sky-500 rounded-full"></div>
                    <span className="font-bold text-sky-500">スイング (脚)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* --- Page 2: One Big Thing (Red Emphasis) - 現象・原因・改善策を表示（縦並び） --- */}
          {currentStep === 2 && (
            <div className="flex-1 flex flex-col items-center p-6 animate-fade-in bg-gradient-to-br from-white via-red-50/30 to-white overflow-y-auto">
              {oneBigThing ? (
                <>
                  <div className="bg-red-600 text-white px-6 py-2 rounded-full text-base font-bold mb-5 shadow-lg flex items-center gap-2 ring-4 ring-red-100 shrink-0">
                    <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                    あなたの最優先課題 (One Big Thing)
                  </div>
                  
                  <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-6 tracking-tight text-center px-4 shrink-0">
                    {oneBigThing.name}
                  </h2>
                  
                  <div className="w-full max-w-4xl space-y-4 px-4 pb-4">
                    {/* 現象 */}
                    {oneBigThing.observation && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-blue-900">
                        <h3 className="text-xl font-bold text-blue-900 mb-3 flex items-center gap-2">
                          <span className="text-2xl">🔍</span> 現象
                        </h3>
                        <p className="text-base leading-relaxed text-slate-700 font-medium">
                          {oneBigThing.observation}
                        </p>
                      </div>
                    )}
                    
                    {/* 原因 */}
                    {oneBigThing.cause && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-red-600">
                        <h3 className="text-xl font-bold text-red-700 mb-3 flex items-center gap-2">
                          <span className="text-2xl">🧐</span> 原因
                        </h3>
                        <p className="text-base leading-relaxed text-slate-700 font-medium">
                          {oneBigThing.cause}
                        </p>
                      </div>
                    )}
                    
                    {/* 改善策 */}
                    {oneBigThing.action && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-sky-500">
                        <h3 className="text-xl font-bold text-sky-700 mb-3 flex items-center gap-2">
                          <span className="text-2xl">💡</span> 改善策
                        </h3>
                        <div className="text-base leading-relaxed text-slate-700 font-medium whitespace-pre-line">
                          {oneBigThing.action}
                        </div>
                      </div>
                    )}
                    
                    {/* データがない場合のフォールバック */}
                    {!oneBigThing.observation && !oneBigThing.cause && !oneBigThing.action && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-gray-400">
                        <p className="text-base text-slate-500 text-center">
                          詳細なアドバイスデータがありません
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center">
                  <p className="text-xl text-gray-500">課題データが見つかりません</p>
                </div>
              )}
            </div>
          )}

          {/* --- Page 3: 具体的なドリル (Action: Red/Blue) - iPad最適化 --- */}
          {currentStep === 3 && (
            <div className="flex-1 px-10 py-8 animate-fade-in flex flex-col overflow-y-auto">
              <h2 className="text-3xl font-bold text-blue-900 mb-8 flex items-center gap-4 justify-center">
                <span className="bg-red-600 text-white px-6 py-2 rounded-lg text-xl font-bold shadow-md tracking-wider">ACTION</span>
                改善のためのトレーニング
              </h2>
              
              {oneBigThing ? (
                <div className="flex-1 grid grid-cols-2 gap-10 items-start max-w-6xl mx-auto w-full">
                  {/* Left: Text */}
                  <div className="space-y-6">
                    <div className="bg-white border-2 border-blue-100 p-6 rounded-2xl shadow-sm">
                      <span className="text-blue-900 font-extrabold tracking-wider text-xs uppercase mb-2 block">Drill Name</span>
                      <h3 className="text-3xl font-bold text-slate-900 mb-3">{oneBigThing.drillName}</h3>
                      <p className="text-lg text-slate-700 leading-relaxed">
                        {oneBigThing.action || oneBigThing.cause || '背筋を伸ばし、一歩踏み出すごとに骨盤を「グッ」と前に押し出す意識で歩きます。'}
                      </p>
                    </div>
                    
                    <div className="bg-slate-50 p-6 rounded-2xl">
                      <h4 className="text-lg font-bold text-slate-800 mb-5 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-red-600" />
                        意識するポイント
                      </h4>
                      <ul className="space-y-3">
                        {oneBigThing.drillPoints.map((point, idx) => (
                          <li key={idx} className="flex items-center gap-3 text-lg text-slate-700 font-medium bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                            <span className="w-7 h-7 bg-blue-900 text-white rounded-full flex items-center justify-center font-bold text-xs shrink-0">
                              {idx + 1}
                            </span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Right: Video Player */}
                  <div className="h-full max-h-[450px] w-full bg-black rounded-2xl overflow-hidden relative group cursor-pointer shadow-2xl ring-4 ring-slate-100">
                    {oneBigThing.drillUrl ? (
                      <video 
                        src={oneBigThing.drillUrl} 
                        className="w-full h-full object-cover" 
                        controls
                        playsInline
                      />
                    ) : (
                      <>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-28 h-28 bg-red-600/90 backdrop-blur-md rounded-full flex items-center justify-center border-4 border-white transition-transform group-hover:scale-105 shadow-xl">
                            <Play className="w-12 h-12 text-white ml-2 fill-white" />
                          </div>
                        </div>
                        <div className="absolute bottom-8 left-8 text-white">
                          <span className="px-3 py-1 bg-blue-900 rounded-lg text-xs font-bold mb-2 inline-block shadow-lg border border-blue-700">WATCH</span>
                          <p className="text-2xl font-bold">ドリル実演動画</p>
                          <p className="text-gray-300 mt-1 text-base">動画URLが設定されていません</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-2xl text-gray-500">ドリルデータが見つかりません</p>
                </div>
              )}
            </div>
          )}

          {/* --- Page 4: おすすめのシューズ (Title Only) --- */}
          {currentStep === 4 && (
            <div className="flex-1 flex flex-col items-center justify-center p-10 animate-fade-in bg-slate-50">
              <div className="text-center">
                <h2 className="text-5xl font-extrabold text-blue-900 mb-6 tracking-tight">あなたに最適のランニングシューズ</h2>
                <div className="w-24 h-2 bg-red-600 mx-auto rounded-full"></div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* --- Footer Navigation (Xebio Style) --- */}
      <div className="h-24 bg-white border-t border-slate-200 px-12 flex items-center justify-between shadow-lg z-10">
        
        {/* Back Button (Neutral/Navy) */}
        <button 
          onClick={prevStep} 
          disabled={currentStep === 0}
          className={`flex items-center gap-3 px-8 py-4 rounded-full text-xl font-bold transition-all transform active:scale-95 ${
            currentStep === 0 
              ? 'opacity-0 pointer-events-none' 
              : 'text-slate-500 hover:bg-slate-100 hover:text-blue-900'
          }`}
        >
          <ChevronLeft className="w-7 h-7" />
          戻る
        </button>

        {/* Progress Bar (Blue & Red) */}
        <div className="flex gap-4">
          {[...Array(totalSteps)].map((_, i) => (
            <div 
              key={i} 
              className={`h-3 rounded-full transition-all duration-500 ease-out ${
                i === currentStep 
                  ? 'w-16 bg-red-600'  // Active is Red
                  : i < currentStep 
                    ? 'w-3 bg-blue-900' // Passed is Navy
                    : 'w-3 bg-slate-200' // Future is Gray
              }`}
            />
          ))}
        </div>

        {/* Next Button (Primary Red) */}
        <button 
          onClick={nextStep} 
          disabled={currentStep === totalSteps - 1}
          className={`flex items-center gap-3 px-10 py-4 rounded-full text-xl font-bold shadow-lg transition-all transform active:scale-95 ${
            currentStep === totalSteps - 1 
              ? 'bg-slate-300 text-white cursor-default shadow-none' 
              : 'bg-red-600 text-white hover:bg-red-700 hover:shadow-xl ring-4 ring-red-100'
          }`}
        >
          {currentStep === totalSteps - 1 ? '完了' : '次へ'}
          {currentStep !== totalSteps - 1 && <ChevronRight className="w-7 h-7" />}
        </button>
      </div>
    </div>
  )
}
