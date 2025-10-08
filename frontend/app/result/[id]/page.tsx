'use client'

import { useState, useEffect } from 'react'
import { 
  Activity, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  PlayCircle,
  BarChart3,
  Loader2,
  ArrowLeft,
  Download,
  ChevronDown,
  ChevronUp,
  TrendingUp
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import PoseVisualizer from '@/app/components/PoseVisualizer'
import AngleGraphsCard from '@/app/components/AngleGraphsCard'
import { useResultStore } from '@/lib/store'

// より現実的なランニングサイクルのダミーデータを生成
const generateRunningCycleDummyData = () => {
  const frames = []
  const fps = 30.0
  const totalFrames = 60 // 2秒間のデータ
  
  for (let frame = 0; frame < totalFrames; frame++) {
    const time = frame / fps
    const cyclePhase = (time * 3.0 * 2) % 2.0 // 3歩/秒のランニング
    
    // 基本的な人体の位置
    const baseKeypoints = [
      // 0-10: 頭部
      {x: 0.5, y: 0.1}, {x: 0.48, y: 0.08}, {x: 0.49, y: 0.08}, {x: 0.47, y: 0.07},
      {x: 0.53, y: 0.07}, {x: 0.51, y: 0.08}, {x: 0.54, y: 0.07}, {x: 0.46, y: 0.09},
      {x: 0.54, y: 0.09}, {x: 0.48, y: 0.11}, {x: 0.52, y: 0.11},
      // 11-12: 肩
      {x: 0.45, y: 0.2}, {x: 0.55, y: 0.2},
      // 13-16: 肘・手首
      {x: 0.4, y: 0.3}, {x: 0.6, y: 0.3}, {x: 0.35, y: 0.4}, {x: 0.65, y: 0.4},
      // 17-22: 手部分
      {x: 0.33, y: 0.42}, {x: 0.67, y: 0.42}, {x: 0.32, y: 0.41}, {x: 0.68, y: 0.41},
      {x: 0.31, y: 0.40}, {x: 0.69, y: 0.40},
      // 23-24: 腰
      {x: 0.45, y: 0.5}, {x: 0.55, y: 0.5},
      // 25-26: 膝
      {x: 0.43, y: 0.7}, {x: 0.57, y: 0.7},
      // 27-28: 足首（重要：接地検出用）
      {x: 0.41, y: 0.85}, {x: 0.59, y: 0.85},
      // 29-32: 足部分
      {x: 0.39, y: 0.87}, {x: 0.61, y: 0.87}, {x: 0.37, y: 0.89}, {x: 0.63, y: 0.89}
    ]
    
    // ランニング動作の計算
    const leftPhase = cyclePhase % 1.0
    const rightPhase = (cyclePhase + 0.5) % 1.0
    
    // 足首の上下運動（接地・離地パターン）
    const leftAnkleY = 0.82 + 0.06 * generateFootCycle(leftPhase)
    const rightAnkleY = 0.82 + 0.06 * generateFootCycle(rightPhase)
    
    // キーポイントを生成
    const keypoints = baseKeypoints.map((base, i) => {
      let {x, y} = base
      
      // 足首の動的な動き
      if (i === 27) y = leftAnkleY  // 左足首
      if (i === 28) y = rightAnkleY // 右足首
      
      // 膝の動的な動き
      if (i === 25) y = 0.68 + 0.04 * generateFootCycle(leftPhase)  // 左膝
      if (i === 26) y = 0.68 + 0.04 * generateFootCycle(rightPhase) // 右膝
      
      // ノイズを追加
      x += (Math.random() - 0.5) * 0.01
      y += (Math.random() - 0.5) * 0.01
      
      return {
        x: Math.max(0.0, Math.min(1.0, x)),
        y: Math.max(0.0, Math.min(1.0, y)),
        z: Math.random() * 0.01,
        visibility: Math.random() * 0.2 + 0.8
      }
    })
    
    frames.push({
      keypoints,
      frame_number: frame,
      timestamp: time
    })
  }
  
  return frames
}

// 足の1サイクル内での上下運動パターン
const generateFootCycle = (phase: number) => {
  if (0.2 <= phase && phase <= 0.4) {
    return 1.0  // 接地期：足首が下に
  } else if (0.7 <= phase && phase <= 0.9) {
    return -1.0 // 遊脚期：足首が上に
  } else {
    return Math.sin((phase - 0.3) * 4 * Math.PI) * 0.5
  }
}

interface ZScoreAnalysisResult {
  status: string
  message: string
  events_detected: {
    left_strikes: number[]
    right_strikes: number[]
    left_offs: number[]
    right_offs: number[]
  }
  event_angles: {
    [event_type: string]: {
      [angle_name: string]: number
    }
  }
  z_scores: {
    [event_type: string]: {
      [angle_name: string]: number
    }
  }
  analysis_summary: {
    total_events_analyzed: number
    significant_deviations: Array<{
      event: string
      angle: string
      z_score: number
      severity: string
    }>
    overall_assessment: string
    recommendations: string[]
  }
  selected_cycle?: {
    start_frame: number
    end_frame: number
    duration: number
    events: {
      right_strike: number
      right_off: number
      left_strike: number
      left_off: number
    }
  }
}

interface AnalysisResult {
  status: string
  message: string
  upload_info: {
    file_id: string
    original_filename: string
    saved_filename: string
    file_size: number
    content_type: string
    upload_timestamp: string
    file_extension: string
  }
  pose_analysis: {
    status: string
    message: string
    video_info: {
      fps: number
      total_frames: number
      duration_seconds: number
      width: number
      height: number
    }
    pose_data: Array<{
      frame_number: number
      timestamp: number
      keypoints: Array<{
        x: number
        y: number
        z: number
        visibility: number
      }>
      landmarks_detected: boolean
    confidence_score: number
  }>
    summary: {
      total_processed_frames: number
      detected_pose_frames: number
      detection_rate: number
      average_confidence: number
      mediapipe_landmarks_count: number
    }
  }
  feature_analysis?: {
    status: string
    message: string
    features: {
      // 新しい絶対角度データ（feature_extractionサービスから）
      angle_statistics?: {
        trunk_angle?: { avg: number; min: number; max: number }
        left_thigh_angle?: { avg: number; min: number; max: number }
        right_thigh_angle?: { avg: number; min: number; max: number }
        left_lower_leg_angle?: { avg: number; min: number; max: number }
        right_lower_leg_angle?: { avg: number; min: number; max: number }
      }
      // 従来の関節角度データ（analysisサービスから）
      trunk_angle?: { avg: number; min: number; max: number }
      left_hip_angle?: { avg: number; min: number; max: number }
      right_hip_angle?: { avg: number; min: number; max: number }
      left_knee_angle?: { avg: number; min: number; max: number }
      right_knee_angle?: { avg: number; min: number; max: number }
      left_ankle_angle?: { avg: number; min: number; max: number }
      right_ankle_angle?: { avg: number; min: number; max: number }
      left_elbow_angle?: { avg: number; min: number; max: number }
      right_elbow_angle?: { avg: number; min: number; max: number }
      // ランニングメトリクス
      running_metrics?: {
        vertical_oscillation?: number
        pitch?: number
      }
      // 後方互換性のため旧フィールドも保持
      knee_angle?: number
      cadence?: number
      stride_length?: number
      contact_time?: number
    }
    analysis_details: {
      total_frames_analyzed: number
      valid_frames: number
      detection_rate: number
      video_duration: number
      analysis_method: string
    }
  }
  advice_analysis?: {
    status: string
    message: string
    video_id: string
    integrated_advice?: string
    high_level_issues?: string[]
  }
  advice_results?: {
    status: string
    message: string
    video_id: string
    integrated_advice?: string
    high_level_issues?: string[]
  }
  issue_analysis?: {
    status: string
    message: string
    issues: string[]
    analysis_details: {
      analyzed_metrics: {
        cadence: { value: number; unit: string; threshold: number; status: string }
        knee_angle_at_landing: { value: number; unit: string; threshold: number; status: string }
        ground_contact_time: { value: number; unit: string; threshold: number; status: string }
      }
      total_issues: number
      overall_assessment: string
    }
  }
  error?: string
}

export default function ResultPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [debugInfo, setDebugInfo] = useState<any>(null)
  const [zustandSaveLog, setZustandSaveLog] = useState<string>("")
  const [zScoreData, setZScoreData] = useState<ZScoreAnalysisResult | null>(null)
  const [zScoreLoading, setZScoreLoading] = useState(false)
  const [showAngleReference, setShowAngleReference] = useState(false)
  const [isImageModalOpen, setIsImageModalOpen] = useState(false)
  const [adviceData, setAdviceData] = useState<any>(null)
  const [adviceLoading, setAdviceLoading] = useState(false)
  
  // Zustandストアからpose_dataを取得
  const { poseData, videoInfo, uploadInfo } = useResultStore()

  // Z値分析を実行
  const fetchZScoreAnalysis = async (poseData: any, videoFps: number) => {
    if (!poseData || zScoreLoading) return

    setZScoreLoading(true)
    try {
      console.log('🎯 Z値分析開始:', { frames: poseData.length, fps: videoFps })
      
      const requestData = {
        keypoints_data: poseData,
        video_fps: videoFps
      }
      
      const response = await fetch('/api/analysis/analyze-z-score', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`Z値分析API呼び出しエラー: ${response.status}`)
      }

      const zScoreResult = await response.json()
      console.log('📊 Z値分析結果取得完了:', zScoreResult)
      
      if (zScoreResult && typeof zScoreResult === 'object') {
        setZScoreData(zScoreResult)
        
        // Z値分析成功後、自動的にAIアドバイス生成を呼び出し
        if (zScoreResult.status === 'success') {
          await generateAdviceFromZScore(zScoreResult)
        }
      } else {
        console.error('❌ 無効なZ値分析データ構造:', zScoreResult)
        setZScoreData({ 
          status: 'error', 
          message: 'Z値分析データの構造が無効です',
          events_detected: { left_strikes: [], right_strikes: [], left_offs: [], right_offs: [] },
          event_angles: {},
          z_scores: {},
          analysis_summary: { total_events_analyzed: 0, significant_deviations: [], overall_assessment: 'error', recommendations: [] }
        })
      }
    } catch (error) {
      console.error('❌ Z値分析エラー:', error)
      setZScoreData({ 
        status: 'error', 
        message: `Z値分析に失敗しました: ${error}`,
        events_detected: { left_strikes: [], right_strikes: [], left_offs: [], right_offs: [] },
        event_angles: {},
        z_scores: {},
        analysis_summary: { total_events_analyzed: 0, significant_deviations: [], overall_assessment: 'error', recommendations: [] }
      })
    } finally {
      setZScoreLoading(false)
    }
  }

  // アドバイステキストを読みやすく整形
  const formatAdviceText = (text: string): string => {
    if (!text) return '詳細な分析結果をもとに改善提案を準備中です。'
    
    // HTMLタグやMarkdown記号を除去
    let cleanText = text
      .replace(/<[^>]*>/g, '') // HTMLタグ除去
      .replace(/\*\*([^*]+)\*\*/g, '$1') // **太字** → 太字
      .replace(/\*([^*]+)\*/g, '$1') // *イタリック* → イタリック
      .replace(/#{1,6}\s+/g, '') // Markdownヘッダー除去
      .replace(/^\s*[\-\*\+]\s+/gm, '• ') // リスト記号統一
      .replace(/^\s*\d+\.\s+/gm, '') // 番号リスト除去
      .replace(/\n{3,}/g, '\n\n') // 過度な改行を2つまでに制限
      .trim()
    
    // 適切な長さに調整（120文字程度）
    if (cleanText.length > 120) {
      // 句読点や改行で自然に区切る
      const naturalBreaks = cleanText.split(/[。．\n]/);
      if (naturalBreaks.length > 1 && naturalBreaks[0].length > 30) {
        return naturalBreaks[0] + '。'
      }
      // 自然な区切りがない場合は120文字で切る
      return cleanText.substring(0, 120) + '...'
    }
    return cleanText
  }

  // アドバイスカードコンポーネント
  const AdviceCard = ({ advice, index }: { advice: any, index: number }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow h-full">
      <div className="flex flex-col h-full">
        {/* ヘッダー部分 */}
        <div className="flex items-start space-x-3 mb-4">
          <div className="flex-shrink-0 w-7 h-7 bg-emerald-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
            {index + 1}
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900 text-base mb-1 leading-tight">
              {advice.issue || advice.title || `課題 ${index + 1}`}
            </h4>
          </div>
        </div>
        
        {/* 詳細説明部分 */}
        <div className="flex-1 mb-4">
          <div className="text-gray-700 text-sm leading-relaxed space-y-2">
            {formatAdviceText(advice.description || '詳細な分析結果をもとに改善提案を準備中です。').split('\n').map((line, i) => (
              <p key={i} className="mb-1">{line}</p>
            ))}
          </div>
        </div>
        
        {/* エクササイズ部分 */}
        {advice.exercise && (
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <span className="text-sm font-medium text-emerald-700 flex items-center">
                💪 <span className="ml-1">推奨エクササイズ</span>
              </span>
            </div>
            <div className="text-sm text-emerald-800 leading-relaxed space-y-1">
              {formatAdviceText(advice.exercise).split('\n').map((line, i) => (
                <p key={i} className="mb-1">{line}</p>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )

  // Z値分析結果から課題リストを抽出
  const extractIssuesFromZScore = (zScoreData: ZScoreAnalysisResult): string[] => {
    if (!zScoreData || zScoreData.status !== 'success') {
      return []
    }

    const issues: string[] = []
    
    // 分析サマリーから有意な偏差を課題として抽出
    const significantDeviations = zScoreData.analysis_summary?.significant_deviations || []
    
    significantDeviations.forEach(deviation => {
      // Z値の重要度に基づいて課題を分類
      const absZScore = Math.abs(deviation.z_score || 0)
      const severity = absZScore >= 3.0 ? '大' : absZScore >= 2.0 ? '中' : '小'
      
      // 角度名と部位を日本語化
      const angleName = deviation.angle || ''
      const eventType = deviation.event || ''
      
      let bodyPart = ''
      let issue = ''
      
      if (angleName.includes('left_lower_leg') || angleName.includes('左下腿')) {
        bodyPart = '左下腿'
        issue = `${bodyPart}角度${severity}`
      } else if (angleName.includes('right_lower_leg') || angleName.includes('右下腿')) {
        bodyPart = '右下腿'
        issue = `${bodyPart}角度${severity}`
      } else if (angleName.includes('left_thigh') || angleName.includes('左大腿')) {
        bodyPart = '左大腿'
        issue = `${bodyPart}角度${severity}`
      } else if (angleName.includes('right_thigh') || angleName.includes('右大腿')) {
        bodyPart = '右大腿'
        issue = `${bodyPart}角度${severity}`
      } else if (angleName.includes('trunk') || angleName.includes('体幹')) {
        bodyPart = '体幹'
        issue = `${bodyPart}角度${severity}`
      }
      
      if (issue && !issues.includes(issue)) {
        issues.push(issue)
      }
    })
    
    // 最低1つの課題は生成する（フォールバック）
    if (issues.length === 0) {
      issues.push('基本的なランニングフォーム練習')
    }
    
    console.log('📝 抽出された課題リスト:', issues)
    return issues
  }

  // Z値分析結果からAIアドバイスを生成
  const generateAdviceFromZScore = async (zScoreResult: ZScoreAnalysisResult) => {
    if (!zScoreResult || zScoreResult.status !== 'success') return
    
    setAdviceLoading(true)
    try {
      console.log('🤖 AIアドバイス生成開始')
      
      const response = await fetch(`/api/advice_generation/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_id: params.id,
          issues: extractIssuesFromZScore(zScoreResult)
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const adviceResult = await response.json()
      console.log('✅ AIアドバイス生成成功:', adviceResult)
      setAdviceData(adviceResult)
      
    } catch (error) {
      console.error('❌ AIアドバイス生成エラー:', error)
    } finally {
      setAdviceLoading(false)
    }
  }

  // localStorage方式でZ値分析を実行
  const executeLocalStorageZScoreAnalysis = async () => {
    try {
      console.log('🔄 localStorage方式でZ値分析を開始')
      
      // 1. localStorageから実データを取得
      const savedResult = localStorage.getItem(`light_analysis_result_${params.id}`)
      if (!savedResult) {
        console.log('⚠️ localStorage結果データなし、ダミーデータでZ値分析')
        const dummyPoseData = generateRunningCycleDummyData()
        await fetchZScoreAnalysis(dummyPoseData, 30.0)
        return
      }
      
      const result = JSON.parse(savedResult)
      
      // 2. pose_dataの存在確認
      if (result.pose_analysis?.pose_data && result.pose_analysis.pose_data.length > 0) {
        const actualPoseData = result.pose_analysis.pose_data
        const actualVideoFps = result.pose_analysis.video_info?.fps || 30.0
        
        console.log('✅ localStorage結果データから実データを取得:', {
          frames: actualPoseData.length,
          fps: actualVideoFps
        })
        
        await fetchZScoreAnalysis(actualPoseData, actualVideoFps)
      } else {
        console.log('⚠️ localStorage内にpose_dataなし、ダミーデータでZ値分析')
        console.log('デバッグ情報:', {
          hasPoseAnalysis: !!result.pose_analysis,
          hasPoseData: !!result.pose_analysis?.pose_data,
          poseDataLength: result.pose_analysis?.pose_data?.length || 0,
          poseDataType: typeof result.pose_analysis?.pose_data
        })
        
        const dummyPoseData = generateRunningCycleDummyData()
        await fetchZScoreAnalysis(dummyPoseData, 30.0)
      }
    } catch (error) {
      console.error('❌ localStorage Z値分析エラー:', error)
      const dummyPoseData = generateRunningCycleDummyData()
      await fetchZScoreAnalysis(dummyPoseData, 30.0)
    }
  }

  useEffect(() => {
    const fetchResult = async () => {
      try {
        // デバッグ情報をlocalStorageから読み込み
        const debugData = localStorage.getItem('lastUploadDebug')
        if (debugData) {
          setDebugInfo(JSON.parse(debugData))
        }
        
        // Zustand保存ログを読み込み
        const saveLog = localStorage.getItem('lastZustandSaveLog')
        if (saveLog) {
          setZustandSaveLog(saveLog)
        }
        
        // localStorageから軽量な結果データを取得
        const savedResult = localStorage.getItem(`light_analysis_result_${params.id}`)
        console.log("🔍 localStorage確認:", {
          key: `light_analysis_result_${params.id}`,
          exists: !!savedResult,
          dataLength: savedResult?.length || 0
        })
        
        if (savedResult) {
          const lightResult = JSON.parse(savedResult)
          
          // 開発環境でlocalStorageデータの構造をデバッグ
          if (process.env.NODE_ENV === 'development') {
            console.log('📋 localStorage データ構造デバッグ:');
            console.log('  lightResult keys:', Object.keys(lightResult));
            console.log('  lightResult.advice_results:', lightResult.advice_results ? 'あり' : 'なし');
            console.log('  lightResult.advice_analysis:', lightResult.advice_analysis ? 'あり' : 'なし');
            console.log('  全データ:', lightResult);
          }
          
          // Zustandストアからpose_dataを追加してresultを再構成
          const completeResult = {
            ...lightResult,
            pose_analysis: {
              ...lightResult.pose_analysis,
              pose_data: poseData || [], // Zustandから取得
              video_info: videoInfo || lightResult.pose_analysis?.video_info
            }
          }
          
          
          setResult(completeResult)
          setLoading(false)
          
          // angle_statisticsが存在する場合、比較を実行
          if (completeResult.feature_analysis?.features?.angle_statistics) {
            console.log('📊 angle_statistics発見、比較処理開始...')
            
            // avgをmeanに変換
            const convertedStats: any = {}
            Object.entries(completeResult.feature_analysis.features.angle_statistics).forEach(([key, value]: [string, any]) => {
              convertedStats[key] = {
                mean: value.avg,
                avg: value.avg,
                min: value.min,
                max: value.max
              }
            })
            
            // Z値分析を実行（localStorage方式）
            executeLocalStorageZScoreAnalysis()
          }
          
          return
        }
        
        // localStorageにデータがない場合はダミーデータを表示

        // まずZ値分析を実行してから結果を表示
        console.log('🔄 ページ読み込み時にZ値分析を実行')
        
        // Z値分析を実行（API経由で直接pose_dataを取得）
        const executeZScoreAnalysis = async () => {
          console.log('🔄 API経由でpose_dataを直接取得します')
          
          try {
            const apiResponse = await fetch(`/api/video_processing/result/${params.id}`)
            if (apiResponse.ok) {
              const apiData = await apiResponse.json()
              
              if (apiData.pose_analysis?.pose_data && apiData.pose_analysis.pose_data.length > 0) {
                const actualPoseData = apiData.pose_analysis.pose_data
                const actualVideoFps = apiData.pose_analysis.video_info?.fps || 30.0
                
                console.log('✅ API経由で実データを取得:', { 
                  frames: actualPoseData.length, 
                  fps: actualVideoFps 
                })
                console.log('🎯 実データでZ値分析を実行:', { 
                  frames: actualPoseData.length, 
                  fps: actualVideoFps 
                })
                
                await fetchZScoreAnalysis(actualPoseData, actualVideoFps)
              } else {
                console.log('⚠️ APIからも実データを取得できず、ダミーデータでZ値分析を実行')
                const dummyPoseData = generateRunningCycleDummyData()
                await fetchZScoreAnalysis(dummyPoseData, 30.0)
              }
            } else {
              console.log('⚠️ API呼び出し失敗、ダミーデータでZ値分析を実行')
              const dummyPoseData = generateRunningCycleDummyData()
              await fetchZScoreAnalysis(dummyPoseData, 30.0)
            }
          } catch (apiError) {
            console.log('⚠️ API呼び出しエラー、ダミーデータでZ値分析を実行:', apiError)
            const dummyPoseData = generateRunningCycleDummyData()
            await fetchZScoreAnalysis(dummyPoseData, 30.0)
          }
        }
        
        // Z値分析を実行してからダミーデータを表示
        executeZScoreAnalysis().then(() => {
          console.log('✅ Z値分析完了、ダミーデータ表示を開始')
        })

        // ダミーデータで動作確認（実データの構造を模擬）
    setTimeout(() => {
      setResult({
            status: "success",
            message: "動画アップロード、骨格解析、特徴量計算が完了しました",
            upload_info: {
              file_id: params.id,
              original_filename: "running_sample.mp4",
              saved_filename: `20250126_${params.id}.mp4`,
              file_size: 2048000,
              content_type: "video/mp4",
              upload_timestamp: new Date().toISOString(),
              file_extension: ".mp4"
            },
            pose_analysis: {
              status: "success",
              message: "骨格検出が完了しました。285/300フレームで姿勢を検出",
              video_info: {
                fps: 30.0,
                total_frames: 300,
                duration_seconds: 10.0,
                width: 1920,
                height: 1080
              },
              pose_data: [], // 実際の実装では骨格データが入る
              summary: {
                total_processed_frames: 0,
                detected_pose_frames: 0,
                detection_rate: 0,
                average_confidence: 0,
                mediapipe_landmarks_count: 0
              }
            },
            feature_analysis: {
              status: "success",
              message: "絶対角度・重心上下動・ピッチの特徴量抽出が完了しました（ダミーデータ表示中）",
              features: {
                // 新しい絶対角度データ（正しい符号規則）
                angle_statistics: {
                  trunk_angle: { avg: 5.2, min: -8.1, max: 18.3 },     // 前傾で正値、後傾で負値
                  left_thigh_angle: { avg: -12.4, min: -35.7, max: 15.2 },   // 膝が後方で正値、前方で負値
                  right_thigh_angle: { avg: -11.8, min: -34.1, max: 16.7 },  // 膝が後方で正値、前方で負値
                  left_lower_leg_angle: { avg: -8.7, min: -25.3, max: 12.1 }, // 足首が後方で正値、前方で負値
                  right_lower_leg_angle: { avg: -9.2, min: -24.8, max: 13.4 } // 足首が後方で正値、前方で負値
                },
                // 従来の関節角度データ（analysisサービスから）
                trunk_angle: { avg: 15.2, min: 12.1, max: 18.5 },
                left_hip_angle: { avg: 140.8, min: 110.3, max: 165.2 },
                right_hip_angle: { avg: 142.1, min: 112.5, max: 168.0 },
                left_knee_angle: { avg: 155.6, min: 130.8, max: 178.1 },
                right_knee_angle: { avg: 154.9, min: 128.9, max: 177.5 },
                left_ankle_angle: { avg: 85.3, min: 70.1, max: 95.4 },
                right_ankle_angle: { avg: 86.1, min: 72.3, max: 98.2 },
                left_elbow_angle: { avg: 95.7, min: 75.4, max: 115.8 },
                right_elbow_angle: { avg: 94.8, min: 74.9, max: 114.5 },
                // ランニングメトリクス
                running_metrics: {
                  vertical_oscillation: 0.067, // 6.7%
                  pitch: 182 // 182 SPM
                },
                // 従来のメトリクス
                cadence: 182.0,
                stride_length: 1.35,
                contact_time: 245.5
              },
              analysis_details: {
                total_frames_analyzed: 0,
                valid_frames: 0,
                detection_rate: 0,
                video_duration: 0,
                analysis_method: "mediapipe_pose_landmarks"
              }
            },
            issue_analysis: {
              status: "success",
              message: "フォーム分析完了：1つの改善点を検出しました",
              issues: ["地面に足がついている時間が長く、エネルギー効率が低下している可能性があります。"],
              analysis_details: {
                analyzed_metrics: {
                  cadence: undefined as any, // デバッグ情報削除
                  knee_angle_at_landing: { value: 165.7, unit: "degrees", threshold: 170, status: "良好" },
                  ground_contact_time: undefined as any // デバッグ情報削除
                },
                total_issues: 1,
                overall_assessment: "1つの改善点が見つかりました"
              }
        }
      })
      setLoading(false)
        
        // ダミーデータの場合も比較を実行
        const dummyStats = {
          trunk_angle: { mean: 5.2, avg: 5.2, min: -8.1, max: 18.3 },
          left_thigh_angle: { mean: -12.4, avg: -12.4, min: -35.7, max: 15.2 },
          right_thigh_angle: { mean: -11.8, avg: -11.8, min: -34.1, max: 16.7 },
          left_lower_leg_angle: { mean: -8.7, avg: -8.7, min: -25.3, max: 12.1 },
          right_lower_leg_angle: { mean: -9.2, avg: -9.2, min: -24.8, max: 13.4 }
        }
        // Z値分析は既に上で実行済み
        console.log('📊 ダミーデータ表示完了（Z値分析は並行実行中）')
    }, 500)  // 表示を早める
      } catch (error) {
        console.error('結果取得エラー:', error)
        setLoading(false)
      }
    }

    fetchResult()
  }, [params.id])

  // Z値分析の強制実行タイマーは削除（初期実行で対応）

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-running flex items-center justify-center">
        <Card className="w-96 shadow-xl">
          <CardContent className="flex flex-col items-center space-y-4 p-8">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <CardTitle>解析結果を読み込み中...</CardTitle>
            <CardDescription>
              AIが動画を処理しています
            </CardDescription>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-gradient-running flex items-center justify-center">
        <Card className="w-96 shadow-xl">
          <CardContent className="flex flex-col items-center space-y-4 p-8">
            <AlertTriangle className="h-12 w-12 text-yellow-500" />
            <CardTitle>結果が見つかりません</CardTitle>
            <CardDescription>
              解析結果を取得できませんでした
            </CardDescription>
            <Button onClick={() => window.location.href = '/'}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              トップページに戻る
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const videoUrl = `/api/video/stream/${params.id}?t=${Date.now()}`

  return (
    <div className="min-h-screen bg-gradient-running">
      <div className="container mx-auto p-6 space-y-6">
      {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-600">解析結果</h1>
            <p className="text-muted-foreground">
              {result.upload_info.original_filename}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              result.status === 'success' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {result.status === 'success' ? '解析完了' : '部分的に完了'}
            </div>
            {false && result.pose_analysis && (
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                検出率: {(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%
        </div>
            )}
          </div>
        </div>

        {/* 2カラムレイアウト - 動画と解析結果を横並び（3:1の比率） */}
        <div className="grid lg:grid-cols-4 gap-6">
          {/* 左カラム：動画プレイヤー（3/4幅） */}
          <div className="lg:col-span-3">
            <Card className="shadow-xl h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PlayCircle className="h-5 w-5 mr-2" />
                  動画解析
                </CardTitle>
                <CardDescription>
                  骨格キーポイントがリアルタイムで表示されます
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                {poseData && poseData.length > 0 ? (
                  (() => {
                    // ★★★ ZustandストアからPoseVisualizerに渡すデータをデバッグ ★★★
                    console.log("🔍 Zustandストアのpose_data長さ:", poseData.length)
                    console.log("🔍 videoUrl:", videoUrl)
                    console.log("🔍 最初のフレームデータ:", poseData[0])
                    
                    // PoseVisualizerが期待する形式に変換
                    const poseAnalysisData = {
                      status: "success",
                      message: "骨格解析完了",
                      video_info: videoInfo || {
                        fps: 30,
                        total_frames: poseData.length,
                        duration_seconds: poseData.length / 30,
                        width: 640,
                        height: 480
                      },
                      pose_data: poseData.map(frame => ({
                        ...frame,
                        confidence_score: 0.9 // デフォルト値を設定
                      })),
                      summary: {
                        total_processed_frames: poseData.length,
                        detected_pose_frames: poseData.filter(frame => frame.landmarks_detected).length,
                        detection_rate: poseData.filter(frame => frame.landmarks_detected).length / poseData.length,
                        average_confidence: 0.9, // デフォルト値
                        mediapipe_landmarks_count: 33
                      }
                    }
                    
                    console.log("🔍 PoseVisualizerに渡すデータ:", poseAnalysisData)
                    
                    return (
                      <PoseVisualizer 
                        videoUrl={videoUrl}
                        poseData={poseAnalysisData}
                      />
                    )
                  })()
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                    <p>骨格データが見つかりません</p>
                    <p className="text-sm mt-2">
                      Zustandストア内のpose_data: {poseData?.length || 0}フレーム
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 角度推移グラフカードは削除されました */}
          </div>

          {/* 右カラム：解析結果（1/4幅） */}
          <div className="lg:col-span-1 space-y-6">
            {/* 解析結果カード - 開発環境でのみ表示 */}
            {false && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  解析結果
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {false && result.pose_analysis && (
                  <>
                    <div className="grid grid-cols-1 gap-3">
                      <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                        <div className="text-2xl font-bold text-green-700">
                          {(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%
        </div>
                        <div className="text-sm text-green-600">骨格検出率</div>
      </div>

                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                        <div className="text-2xl font-bold text-blue-700">
                          {(result.pose_analysis.summary.average_confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-blue-600">平均信頼度</div>
      </div>

                      <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                        <div className="text-2xl font-bold text-purple-700">
                          {result.pose_analysis.summary.detected_pose_frames}
                        </div>
                        <div className="text-sm text-purple-600">検出フレーム数</div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
                        </Card>
            )}

            {/* 関節角度カード - 開発環境でのみ表示 */}
            {false && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  関節角度
                </CardTitle>
                <div className="text-sm text-muted-foreground mt-1">
                  ランニング時の身体の角度
                </div>
              </CardHeader>
              <CardContent>

                {/* 新しい絶対角度データを優先して表示 */}
                {result.feature_analysis?.features?.angle_statistics && (
                  <div className="space-y-4">
                    {/* 体幹角度 */}
                    {result.feature_analysis.features.angle_statistics.trunk_angle && (
                      <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
                            <div className="text-lg font-bold text-green-700">
                          体幹角度
                            </div>
                        <div className="text-sm font-semibold text-green-600 mt-1">
                          平均: {result.feature_analysis.features.angle_statistics.trunk_angle.avg.toFixed(1)}° | 
                          最小: {result.feature_analysis.features.angle_statistics.trunk_angle.min.toFixed(1)}° | 
                          最大: {result.feature_analysis.features.angle_statistics.trunk_angle.max.toFixed(1)}°
                            </div>
                        <div className="text-xs text-green-500 mt-2">
                          腰から肩への直線ベクトルと鉛直軸の角度（前傾で正値、後傾で負値）
                        </div>
                      </div>
                    )}

                    {/* 大腿角度 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 左大腿角度 */}
                      {result.feature_analysis.features.angle_statistics.left_thigh_angle && (
                        <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                          <div className="text-lg font-bold text-purple-700">
                            左大腿角度
                            </div>
                          <div className="text-sm font-semibold text-purple-600 mt-1">
                            平均: {result.feature_analysis.features.angle_statistics.left_thigh_angle.avg.toFixed(1)}°
                            </div>
                          <div className="text-xs text-purple-600">
                            最小: {result.feature_analysis.features.angle_statistics.left_thigh_angle.min.toFixed(1)}° | 
                            最大: {result.feature_analysis.features.angle_statistics.left_thigh_angle.max.toFixed(1)}°
                          </div>
                          <div className="text-xs text-purple-500 mt-2">
                            膝関節点から股関節点に向かうベクトルと鉛直軸の角度（膝が後方で正値）
                          </div>
                              </div>
                            )}

                      {/* 右大腿角度 */}
                      {result.feature_analysis.features.angle_statistics.right_thigh_angle && (
                        <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                          <div className="text-lg font-bold text-purple-700">
                            右大腿角度
                          </div>
                          <div className="text-sm font-semibold text-purple-600 mt-1">
                            平均: {result.feature_analysis.features.angle_statistics.right_thigh_angle.avg.toFixed(1)}°
                          </div>
                          <div className="text-xs text-purple-600">
                            最小: {result.feature_analysis.features.angle_statistics.right_thigh_angle.min.toFixed(1)}° | 
                            最大: {result.feature_analysis.features.angle_statistics.right_thigh_angle.max.toFixed(1)}°
                          </div>
                          <div className="text-xs text-purple-500 mt-2">
                            膝関節点から股関節点に向かうベクトルと鉛直軸の角度（膝が後方で正値）
                        </div>
                      </div>
                    )}
                    </div>

                    {/* 下腿角度 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 左下腿角度 */}
                      {result.feature_analysis.features.angle_statistics.left_lower_leg_angle && (
                        <div className="text-center p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                          <div className="text-lg font-bold text-indigo-700">
                            左下腿角度
                            </div>
                          <div className="text-sm font-semibold text-indigo-600 mt-1">
                            平均: {result.feature_analysis.features.angle_statistics.left_lower_leg_angle.avg.toFixed(1)}°
                            </div>
                          <div className="text-xs text-indigo-600">
                            最小: {result.feature_analysis.features.angle_statistics.left_lower_leg_angle.min.toFixed(1)}° | 
                            最大: {result.feature_analysis.features.angle_statistics.left_lower_leg_angle.max.toFixed(1)}°
                          </div>
                          <div className="text-xs text-indigo-500 mt-2">
                            足関節点から膝関節点に向かうベクトルと鉛直軸の角度（足が後方で正値）
                          </div>
                              </div>
                            )}

                      {/* 右下腿角度 */}
                      {result.feature_analysis.features.angle_statistics.right_lower_leg_angle && (
                        <div className="text-center p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                          <div className="text-lg font-bold text-indigo-700">
                            右下腿角度
                          </div>
                          <div className="text-sm font-semibold text-indigo-600 mt-1">
                            平均: {result.feature_analysis.features.angle_statistics.right_lower_leg_angle.avg.toFixed(1)}°
                          </div>
                          <div className="text-xs text-indigo-600">
                            最小: {result.feature_analysis.features.angle_statistics.right_lower_leg_angle.min.toFixed(1)}° | 
                            最大: {result.feature_analysis.features.angle_statistics.right_lower_leg_angle.max.toFixed(1)}°
                          </div>
                          <div className="text-xs text-indigo-500 mt-2">
                            足関節点から膝関節点に向かうベクトルと鉛直軸の角度（足が後方で正値）
                        </div>
                      </div>
                    )}
                    </div>

                    {/* 新しい角度（上腕、前腕、足部） */}
                    {result.feature_analysis?.features?.angle_statistics && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-center mb-4">追加角度解析</h3>
                        
                        {/* 上腕角度 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {(result.feature_analysis.features.angle_statistics as any).left_upper_arm_angle && (
                            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                              <div className="text-lg font-bold text-orange-700">左上腕角度</div>
                              <div className="text-sm font-semibold text-orange-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).left_upper_arm_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-orange-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).left_upper_arm_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).left_upper_arm_angle.max.toFixed(1)}°
                              </div>
                      </div>
                    )}
                          {(result.feature_analysis.features.angle_statistics as any).right_upper_arm_angle && (
                            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                              <div className="text-lg font-bold text-orange-700">右上腕角度</div>
                              <div className="text-sm font-semibold text-orange-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).right_upper_arm_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-orange-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).right_upper_arm_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).right_upper_arm_angle.max.toFixed(1)}°
                              </div>
                </div>
                )}
                        </div>

                        {/* 前腕角度 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {(result.feature_analysis.features.angle_statistics as any).left_forearm_angle && (
                            <div className="text-center p-4 bg-teal-50 rounded-lg border border-teal-200">
                              <div className="text-lg font-bold text-teal-700">左前腕角度</div>
                              <div className="text-sm font-semibold text-teal-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).left_forearm_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-teal-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).left_forearm_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).left_forearm_angle.max.toFixed(1)}°
                              </div>
                </div>
                )}
                          {(result.feature_analysis.features.angle_statistics as any).right_forearm_angle && (
                            <div className="text-center p-4 bg-teal-50 rounded-lg border border-teal-200">
                              <div className="text-lg font-bold text-teal-700">右前腕角度</div>
                              <div className="text-sm font-semibold text-teal-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).right_forearm_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-teal-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).right_forearm_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).right_forearm_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                        </div>

                        {/* 足部角度 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {(result.feature_analysis.features.angle_statistics as any).left_foot_angle && (
                            <div className="text-center p-4 bg-rose-50 rounded-lg border border-rose-200">
                              <div className="text-lg font-bold text-rose-700">左足部角度</div>
                              <div className="text-sm font-semibold text-rose-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).left_foot_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-rose-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).left_foot_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).left_foot_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                          {(result.feature_analysis.features.angle_statistics as any).right_foot_angle && (
                            <div className="text-center p-4 bg-rose-50 rounded-lg border border-rose-200">
                              <div className="text-lg font-bold text-rose-700">右足部角度</div>
                              <div className="text-sm font-semibold text-rose-600 mt-1">
                                平均: {(result.feature_analysis.features.angle_statistics as any).right_foot_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-rose-600">
                                最小: {(result.feature_analysis.features.angle_statistics as any).right_foot_angle.min.toFixed(1)}° | 
                                最大: {(result.feature_analysis.features.angle_statistics as any).right_foot_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 従来の関節角度データにフォールバック（新データがない場合） */}
                {!result.feature_analysis?.features?.angle_statistics && result.feature_analysis?.features && (
                  <div className="space-y-4">
                    {/* 従来の体幹角度表示 */}
                    {result.feature_analysis.features.trunk_angle && (
                      <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
                        <div className="text-lg font-bold text-green-700">
                          体幹角度
                        </div>
                        <div className="text-sm font-semibold text-green-600 mt-1">
                          平均: {result.feature_analysis.features.trunk_angle.avg.toFixed(1)}° | 
                          最小: {result.feature_analysis.features.trunk_angle.min.toFixed(1)}° | 
                          最大: {result.feature_analysis.features.trunk_angle.max.toFixed(1)}°
                        </div>
                        <div className="text-xs text-green-500 mt-2">
                          腰から肩への直線ベクトルと鉛直軸の角度（前傾で正値、後傾で負値）
                        </div>
                      </div>
                    )}

                    {/* 従来の関節角度データ表示 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* 股関節角度 */}
                      {(result.feature_analysis.features.left_hip_angle || result.feature_analysis.features.right_hip_angle) && (
                        <>
                          {result.feature_analysis.features.left_hip_angle && (
                            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                              <div className="text-lg font-bold text-blue-700">左股関節角度</div>
                              <div className="text-sm font-semibold text-blue-600 mt-1">
                                平均: {result.feature_analysis.features.left_hip_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-blue-600">
                                最小: {result.feature_analysis.features.left_hip_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.left_hip_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                          {result.feature_analysis.features.right_hip_angle && (
                            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                              <div className="text-lg font-bold text-blue-700">右股関節角度</div>
                              <div className="text-sm font-semibold text-blue-600 mt-1">
                                平均: {result.feature_analysis.features.right_hip_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-blue-600">
                                最小: {result.feature_analysis.features.right_hip_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.right_hip_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                        </>
                      )}

                      {/* 膝関節角度 */}
                      {(result.feature_analysis.features.left_knee_angle || result.feature_analysis.features.right_knee_angle) && (
                        <>
                          {result.feature_analysis.features.left_knee_angle && (
                            <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                              <div className="text-lg font-bold text-purple-700">左膝関節角度</div>
                              <div className="text-sm font-semibold text-purple-600 mt-1">
                                平均: {result.feature_analysis.features.left_knee_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-purple-600">
                                最小: {result.feature_analysis.features.left_knee_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.left_knee_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                          {result.feature_analysis.features.right_knee_angle && (
                            <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                              <div className="text-lg font-bold text-purple-700">右膝関節角度</div>
                              <div className="text-sm font-semibold text-purple-600 mt-1">
                                平均: {result.feature_analysis.features.right_knee_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-purple-600">
                                最小: {result.feature_analysis.features.right_knee_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.right_knee_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                        </>
                      )}

                      {/* 足関節角度 */}
                      {(result.feature_analysis.features.left_ankle_angle || result.feature_analysis.features.right_ankle_angle) && (
                        <>
                          {result.feature_analysis.features.left_ankle_angle && (
                            <div className="text-center p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                              <div className="text-lg font-bold text-indigo-700">左足関節角度</div>
                              <div className="text-sm font-semibold text-indigo-600 mt-1">
                                平均: {result.feature_analysis.features.left_ankle_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-indigo-600">
                                最小: {result.feature_analysis.features.left_ankle_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.left_ankle_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                          {result.feature_analysis.features.right_ankle_angle && (
                            <div className="text-center p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                              <div className="text-lg font-bold text-indigo-700">右足関節角度</div>
                              <div className="text-sm font-semibold text-indigo-600 mt-1">
                                平均: {result.feature_analysis.features.right_ankle_angle.avg.toFixed(1)}°
                              </div>
                              <div className="text-xs text-indigo-600">
                                最小: {result.feature_analysis.features.right_ankle_angle.min.toFixed(1)}° | 
                                最大: {result.feature_analysis.features.right_ankle_angle.max.toFixed(1)}°
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                </div>
                )}

                {/* データが存在しない場合の表示（新しいデザインに合わせて改善） */}
                {!result.feature_analysis?.features?.angle_statistics && !result.feature_analysis?.features && (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
                  </div>
                )}
              </CardContent>
            </Card>
            )}

            {/* ランニングメトリクスカード */}
            <Card className="shadow-lg h-full flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  ランニングメトリクス
                </CardTitle>
                <div className="text-sm text-muted-foreground mt-1">
                  重心上下動とピッチ（ケイデンス）
                </div>
              </CardHeader>
              <CardContent className="flex-1">
                {result.feature_analysis?.features && (
                  <div className="space-y-4 h-full flex flex-col justify-center">
                    {/* 重心上下動 */}
                    {(result.feature_analysis.features as any)?.running_metrics?.vertical_oscillation && (
                      <div className="text-center p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                        <div className="text-lg font-bold text-emerald-700">
                          重心上下動: {((result.feature_analysis.features as any).running_metrics.vertical_oscillation * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-emerald-600 mt-1">
                          身長に対する上下動の比率
                        </div>
                        <div className="text-xs text-emerald-500 mt-1">
                          理想値: 5-8%程度
                        </div>
                      </div>
                    )}
                    
                    {/* ピッチ（ケイデンス） */}
                    {(result.feature_analysis.features as any)?.running_metrics?.pitch && (
                      <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="text-lg font-bold text-blue-700">
                          ピッチ: {((result.feature_analysis.features as any).running_metrics.pitch).toFixed(0)} SPM
                        </div>
                        <div className="text-xs text-blue-600 mt-1">
                          1分間あたりの歩数（Steps Per Minute）
                        </div>
                        <div className="text-xs text-blue-500 mt-1">
                          理想値: 180 SPM前後
                        </div>
          </div>
                    )}
                    
                    {/* 角度参照図 - アコーディオン形式 */}
                    <div className="mt-6 border rounded-lg bg-white">
                      <button
                        onClick={() => setShowAngleReference(!showAngleReference)}
                        className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors duration-200"
                      >
                        <h3 className="text-lg font-semibold text-gray-800">角度測定の基準</h3>
                        <div className="flex items-center">
                          <span className="text-sm text-gray-600 mr-2">
                            {showAngleReference ? '非表示' : '表示'}
                          </span>
                          {showAngleReference ? (
                            <ChevronUp className="h-5 w-5 text-gray-600" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-gray-600" />
                          )}
                        </div>
                      </button>
                      
                      {showAngleReference && (
                        <div className="px-4 pb-4 border-t">
                          <div className="pt-4">
                            <div className="flex justify-center">
                              <img 
                                src="/angle_reference_diagram.png" 
                                alt="角度測定の基準図"
                                className="max-w-full h-auto rounded-lg shadow-sm cursor-pointer hover:opacity-80 transition-opacity duration-200"
                                style={{ maxHeight: '400px' }}
                                onClick={() => setIsImageModalOpen(true)}
                              />
                            </div>
                            <p className="text-sm text-gray-600 mt-3 text-center">
                              各角度の定義と符号規則を示した図（クリックで拡大）
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* アクションボタン */}
                    <div className="space-y-3 mt-6 pt-4 border-t">
                      <Button 
                        onClick={() => window.location.href = '/'}
                        className="w-full"
                        size="lg"
                      >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        もう一度解析する
                      </Button>
                      
                      <Button 
                        variant="outline"
                        onClick={() => window.open(videoUrl, '_blank')}
                        className="w-full"
                        size="lg"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        動画をダウンロード
                      </Button>
                    </div>
                    
                    {/* 従来のメトリクス表示（新しいrunning_metricsがない場合） */}
                    {!(result.feature_analysis.features as any)?.running_metrics && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* ケイデンス */}
                        {result.feature_analysis.features.cadence && (
                          <div className="text-center p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                            <div className="text-lg font-bold text-cyan-700">
                              ケイデンス: {result.feature_analysis.features.cadence.toFixed(0)} SPM
                            </div>
                            <div className="text-xs text-cyan-600 mt-1">
                              1分間あたりの歩数
                            </div>
                            <div className="text-xs text-cyan-500 mt-1">
                              理想値: 180 SPM前後
                            </div>
                          </div>
                        )}
                        
                        {/* ストライド長 */}
                        {result.feature_analysis.features.stride_length && (
                          <div className="text-center p-4 bg-teal-50 rounded-lg border border-teal-200">
                            <div className="text-lg font-bold text-teal-700">
                              ストライド長: {result.feature_analysis.features.stride_length.toFixed(2)}m
                            </div>
                            <div className="text-xs text-teal-600 mt-1">
                              1歩あたりの距離
                            </div>
                            <div className="text-xs text-teal-500 mt-1">
                              身長の約0.8倍が理想
                            </div>
                          </div>
                        )}
                        
                        {/* 接地時間 */}
                        {result.feature_analysis.features.contact_time && (
                          <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
                            <div className="text-lg font-bold text-amber-700">
                              接地時間: {result.feature_analysis.features.contact_time.toFixed(0)}ms
                            </div>
                            <div className="text-xs text-amber-600 mt-1">
                              足が地面に接している時間
                            </div>
                            <div className="text-xs text-amber-500 mt-1">
                              短いほど効率的（200-250ms程度）
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* データが不足している場合（すべてのメトリクスがない場合のみ） */}
                    {!(result.feature_analysis.features as any)?.running_metrics?.vertical_oscillation && 
                     !(result.feature_analysis.features as any)?.running_metrics?.pitch &&
                     !result.feature_analysis.features.cadence &&
                     !result.feature_analysis.features.stride_length &&
                     !result.feature_analysis.features.contact_time && (
                      <div className="text-center py-6 text-muted-foreground">
                        <Activity className="h-8 w-8 mx-auto mb-2" />
                        <p className="text-sm">データ不足のため計算できませんでした</p>
                        <p className="text-xs mt-1">より長い動画での分析をお試しください</p>
                      </div>
                    )}
                </div>
                )}
                {!result.feature_analysis && (
                  <div className="text-center py-6 text-muted-foreground">
                    <Activity className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
              </div>
                )}
              </CardContent>
            </Card>

          {/* 課題分析カード - 開発環境でのみ表示 */}
          {false && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  課題分析
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.issue_analysis ? (
                  <div className="space-y-3">
                    <div className="text-sm text-muted-foreground">
                      {result.issue_analysis.analysis_details.total_issues}個の改善点が検出されました
                </div>
                    {result.issue_analysis.issues.length > 0 ? (
                      <div className="space-y-2">
                        {result.issue_analysis.issues.map((issue, index) => (
                          <div key={index} className="flex items-start space-x-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
                            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-amber-800">{issue}</span>
              </div>
                        ))}
                </div>
                    ) : (
                      <div className="flex items-center space-x-2 p-3 bg-green-50 rounded-lg border border-green-200">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-sm text-green-800">フォームに大きな問題は見つかりませんでした</span>
              </div>
                    )}
                </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">分析中...</p>
              </div>
                )}
              </CardContent>
            </Card>
            )}

          </div>
        </div>

        {/* 角度推移分析カード - Zustand直接使用版 */}
        {poseData && poseData.length > 0 ? (
          <AngleGraphsCard 
            poseData={poseData}
            videoInfo={videoInfo || { fps: 30, width: 640, height: 480, total_frames: poseData.length, duration_seconds: poseData.length / 30 }}
          />
        ) : (
          <Card className="shadow-lg mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                📈 角度推移分析（詳細デバッグ）
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                <p className="text-lg mb-4">🔍 データ不足の詳細調査</p>
                <div className="text-xs mt-2 bg-gray-100 p-4 rounded text-left space-y-2">
                  
                  {/* 基本情報 */}
                  <div className="bg-white p-2 rounded border">
                    <strong>基本データ状況:</strong>
                    <p>• result存在: {result ? 'あり' : 'なし'}</p>
                    <p>• pose_analysis存在: {result?.pose_analysis ? 'あり' : 'なし'}</p>
                    <p>• pose_data存在: {result?.pose_analysis?.pose_data ? 'あり' : 'なし'}</p>
                    <p>• pose_dataサイズ: {result?.pose_analysis?.pose_data?.length || 0}</p>
                    <p>• video_info存在: {result?.pose_analysis?.video_info ? 'あり' : 'なし'}</p>
                  </div>

                  {/* Zustandストア情報 */}
                  <div className="bg-blue-50 p-2 rounded border">
                    <strong>Zustandストア状況:</strong>
                    <p>• Zustand poseData: {poseData?.length || 0}フレーム</p>
                    <p>• Zustand videoInfo: {videoInfo ? 'あり' : 'なし'}</p>
                    <p>• Zustand uploadInfo: {uploadInfo ? 'あり' : 'なし'}</p>
                  </div>

                  {/* オブジェクトキー */}
                  {result?.pose_analysis && (
                    <div className="bg-green-50 p-2 rounded border">
                      <strong>pose_analysis keys:</strong>
                      <p>{Object.keys(result.pose_analysis).join(', ')}</p>
                    </div>
                  )}
                  
                  {result && (
                    <div className="bg-yellow-50 p-2 rounded border">
                      <strong>result keys:</strong>
                      <p>{Object.keys(result).join(', ')}</p>
                    </div>
                  )}

                  {/* localStorage確認 */}
                  <div className="bg-red-50 p-2 rounded border">
                    <strong>localStorage確認:</strong>
                    <p>• キー: light_analysis_result_{params.id}</p>
                    <p>• 存在: {typeof window !== 'undefined' && localStorage.getItem(`light_analysis_result_${params.id}`) ? 'あり' : 'なし'}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Z値分析カード - 画面全体幅で4イベント並列表示 */}
        <Card className="shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2" />
              イベント別Z値分析
            </CardTitle>
            <CardDescription>
              ワンサイクルの4つのイベント時点でのフォーム偏差分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            {zScoreLoading ? (
              <div className="text-center py-6">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
                <p className="text-sm text-muted-foreground">Z値分析中...</p>
              </div>
            ) : zScoreData?.status === 'success' ? (
              <div className="space-y-6">
                {/* 分析サマリー */}
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-lg border border-purple-200">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-purple-700">
                        {zScoreData.analysis_summary?.total_events_analyzed || 0}
                      </div>
                      <div className="text-sm text-purple-600">分析イベント数</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${
                        zScoreData.analysis_summary?.overall_assessment === 'excellent' ? 'text-green-600' :
                        zScoreData.analysis_summary?.overall_assessment === 'good' ? 'text-blue-600' :
                        zScoreData.analysis_summary?.overall_assessment === 'needs_improvement' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {zScoreData.analysis_summary?.overall_assessment === 'excellent' ? '✅' :
                         zScoreData.analysis_summary?.overall_assessment === 'good' ? '🟢' :
                         zScoreData.analysis_summary?.overall_assessment === 'needs_improvement' ? '🟡' :
                         '🔴'}
                      </div>
                      <div className="text-sm text-gray-600">総合評価</div>
                    </div>
                  </div>
                </div>

                {/* 4つのイベントを並列表示 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
                  {['right_strike', 'right_off', 'left_strike', 'left_off'].map((eventType) => {
                    const scores = zScoreData.z_scores?.[eventType]
                    if (!scores || Object.keys(scores).length === 0) return null
                    
                    const eventNames: {[key: string]: string} = {
                      'right_strike': '右足接地',
                      'right_off': '右足離地', 
                      'left_strike': '左足接地',
                      'left_off': '左足離地'
                    }
                    
                    const eventName = eventNames[eventType] || eventType
                    
                    return (
                      <div key={eventType} className="border rounded-lg p-4 bg-white shadow-sm">
                        <h3 className="text-lg font-semibold mb-3 text-gray-800 text-center">
                          🎯 {eventName}
                        </h3>
                        <div className="space-y-3">
                          {Object.entries(scores || {}).map(([angleName, zScore]) => {
                            const absZScore = Math.abs(zScore)
                            const severity = absZScore >= 3.0 ? 'high' : absZScore >= 2.0 ? 'moderate' : absZScore >= 1.0 ? 'mild' : 'normal'
                            
                            const severityConfig = {
                              'high': { color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-400', icon: '🔴', label: '要改善' },
                              'moderate': { color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-400', icon: '🟡', label: '注意' },
                              'mild': { color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-400', icon: '🟢', label: '良好' },
                              'normal': { color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-400', icon: '✅', label: '優秀' }
                            }
                            
                            const config = severityConfig[severity]
                            
                            return (
                              <div 
                                key={angleName} 
                                className={`p-3 rounded-lg border ${config.border} ${config.bg}`}
                              >
                                <div className="space-y-2">
                                  {/* 角度名とZ値 */}
                                  <div className="text-center">
                                    <div className="font-medium text-gray-700 text-sm">
                                      {angleName}
                                    </div>
                                    <div className={`text-sm font-semibold ${config.color}`}>
                                      Z値: {zScore >= 0 ? '+' : ''}{zScore.toFixed(2)}
                                    </div>
                                  </div>
                                  
                                  {/* コンパクトなメモリ表示（白抜き仕様） */}
                                  <div className="space-y-1">
                                    <div className="relative h-4 bg-white border-2 border-gray-300 rounded-full overflow-hidden">
                                      {/* ゾーン区切り線 */}
                                      <div className="absolute inset-0 flex">
                                        {/* -3 to -2 ゾーン */}
                                        <div className="w-1/6 border-r border-gray-300"></div>
                                        {/* -2 to -1 ゾーン */}
                                        <div className="w-1/6 border-r border-gray-300"></div>
                                        {/* -1 to +1 ゾーン（正常範囲） */}
                                        <div className="w-1/3 border-r border-gray-300"></div>
                                        {/* +1 to +2 ゾーン */}
                                        <div className="w-1/6 border-r border-gray-300"></div>
                                        {/* +2 to +3 ゾーン */}
                                        <div className="w-1/6"></div>
                                      </div>
                                      
                                      {/* 中央線（Z=0）を太くして目立たせる */}
                                      <div className="absolute left-1/2 top-0 h-full w-1 bg-gray-600 transform -translate-x-0.5"></div>
                                      
                                      {/* Z値インジケーター（より太く、ドロップシャドウ付き） */}
                                      <div 
                                        className={`absolute top-0 h-full w-1.5 rounded-full shadow-md transform -translate-x-0.5 ${
                                          config.color.includes('red') ? 'bg-red-600' : 
                                          config.color.includes('yellow') ? 'bg-yellow-500' : 
                                          config.color.includes('blue') ? 'bg-blue-600' : 
                                          'bg-green-600'
                                        }`}
                                        style={{
                                          left: `${Math.max(0, Math.min(100, ((zScore + 3) / 6) * 100))}%`
                                        }}
                                      ></div>
                                    </div>
                                    
                                    {/* 評価アイコン */}
                                    <div className={`text-center text-xs ${config.color}`}>
                                      {config.icon} {config.label}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Z値の説明 */}
                <div className="bg-gray-50 p-4 rounded-lg border">
                  <h4 className="font-semibold text-gray-800 mb-2">📖 Z値について</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-600">
                    <div className="text-center p-2 bg-green-100 rounded">
                      <div className="font-medium">|Z| &lt; 1.0</div>
                      <div className="text-green-600">✅ 標準範囲内</div>
                    </div>
                    <div className="text-center p-2 bg-blue-100 rounded">
                      <div className="font-medium">1.0 ≤ |Z| &lt; 2.0</div>
                      <div className="text-blue-600">🟢 やや外れ</div>
                    </div>
                    <div className="text-center p-2 bg-yellow-100 rounded">
                      <div className="font-medium">2.0 ≤ |Z| &lt; 3.0</div>
                      <div className="text-yellow-600">🟡 大きく外れ</div>
                    </div>
                    <div className="text-center p-2 bg-red-100 rounded">
                      <div className="font-medium">|Z| ≥ 3.0</div>
                      <div className="text-red-600">🔴 非常に外れ</div>
                    </div>
                  </div>
                  <p className="text-xs mt-2 text-gray-500 text-center">
                    ※ 4つのイベント（右足接地・離地、左足接地・離地）ごとの統計的偏差分析
                  </p>
                </div>
              </div>
            ) : zScoreData?.status === 'error' ? (
              <div className="text-center py-6 text-muted-foreground">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                <p className="text-sm">Z値分析の取得に失敗しました</p>
                <p className="text-xs mt-1">しばらく待ってから再度お試しください</p>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                <p className="text-sm">Z値分析を準備中...</p>
                <p className="text-xs mt-1">動画データが利用可能になると自動で分析を開始します</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 動画情報 - 開発環境でのみ詳細表示 */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>動画情報（開発環境のみ）</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">ファイルサイズ:</span>
                  <p className="text-muted-foreground">
                    {(result.upload_info.file_size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <div>
                  <span className="font-medium">アップロード日時:</span>
                  <p className="text-muted-foreground">
                    {new Date(result.upload_info.upload_timestamp).toLocaleString('ja-JP')}
                  </p>
                </div>
                {result.pose_analysis && (
                  <>
                    <div>
                      <span className="font-medium">動画時間:</span>
                      <p className="text-muted-foreground">
                        {result.pose_analysis.video_info.duration_seconds.toFixed(1)}秒
                      </p>
                    </div>
                    <div>
                      <span className="font-medium">解像度:</span>
                      <p className="text-muted-foreground">
                        {result.pose_analysis.video_info.width}×{result.pose_analysis.video_info.height}
                      </p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}


          {/* ローディング中の表示 - 改善版 */}
          {adviceLoading && (
            <Card className="shadow-lg mt-6 border-l-4 border-amber-400">
              <CardHeader className="bg-gradient-to-r from-amber-50 to-yellow-50">
                <CardTitle className="flex items-center text-amber-800 text-lg">
                  <Loader2 className="h-5 w-5 mr-2 animate-spin text-amber-600" />
                  🤖 AI分析中...
                </CardTitle>
                <CardDescription className="text-amber-700">
                  ランニングフォームを詳細分析してアドバイスを生成しています
                </CardDescription>
              </CardHeader>
              <CardContent className="py-4">
                <div className="flex items-center space-x-2 text-sm text-amber-600">
                  <div className="animate-pulse">📊</div>
                  <span>Z値分析結果の解析中...</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 統合アドバイスセクション */}
          {(() => {
            // 統合アドバイスを表示
            const integratedAdvice = result?.advice_results?.integrated_advice || result?.advice_analysis?.integrated_advice;
            const finalAdvice = integratedAdvice;
            const highLevelIssues = result?.advice_results?.high_level_issues || result?.advice_analysis?.high_level_issues || [];
            
            // 一時的な本番環境デバッグ情報（問題解決後に削除）
            console.log('🎯 統合アドバイス表示デバッグ（本番環境）:');
            console.log('  integratedAdvice:', integratedAdvice ? `"${integratedAdvice.substring(0, 100)}..."` : '❌ なし');
            console.log('  finalAdvice:', finalAdvice ? `"${finalAdvice.substring(0, 100)}..."` : '❌ なし');
            console.log('  result.advice_results:', result?.advice_results ? '✅ あり' : '❌ なし');
            console.log('  result.advice_analysis:', result?.advice_analysis ? '✅ あり' : '❌ なし');
            console.log('  result 全体構造:', result ? Object.keys(result) : '❌ result が null/undefined');
            console.log('  result 詳細:', result);
            console.log('  result のタイプ:', typeof result);
            console.log('  result は配列か:', Array.isArray(result));
            
            // advice_results と advice_analysis の詳細構造をチェック
            if (result?.advice_results) {
              console.log('  advice_results キー:', Object.keys(result.advice_results));
            }
            if (result?.advice_analysis) {
              console.log('  advice_analysis キー:', Object.keys(result.advice_analysis));
            }
            
            if (finalAdvice && finalAdvice.trim()) {
              const isIntegrated = !!integratedAdvice;
              
              return (
                <Card className="shadow-xl mt-6 border-l-4 border-purple-500">
                  <CardHeader>
                    <CardTitle className="flex items-center text-purple-800">
                      🎯 {isIntegrated ? '総合アドバイス（プロコーチ＋AI統合）' : 'プロコーチからのアドバイス'}
                    </CardTitle>
                    <CardDescription>
                      {isIntegrated ? 'プロコーチの知見とAI詳細解析を統合した包括的な改善提案' : '課題の組み合わせを考慮した総合的な改善提案'}
                    </CardDescription>
                    {highLevelIssues.length > 0 && (
                      <div className="text-sm text-purple-600">
                        検出された課題: {highLevelIssues.join(', ')}
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <pre className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {finalAdvice}
                      </pre>
        </div>
                  </CardContent>
                </Card>
              );
            }
            
            // アドバイスが見つからない場合は何も表示しない（開発環境と本番環境で統一）
            
            return null;
          })()}

                  {/* 従来の改善アドバイスカードは統合アドバイス機能により不要になったため削除 */}

          {/* デバッグ情報セクション - 本番環境では非表示 */}
          {process.env.NODE_ENV === 'development' && debugInfo && (
            <Card className="shadow-xl mt-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  🔍 デバッグ情報（開発環境のみ）
                </CardTitle>
                <CardDescription>
                  最後のアップロードのデバッグ情報（{new Date(debugInfo.timestamp).toLocaleString()}）
                </CardDescription>
              </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <span className="font-medium">利用可能なキー:</span>
                  <p className="text-muted-foreground bg-gray-100 p-2 rounded">
                    {JSON.stringify(debugInfo.availableKeys, null, 2)}
                  </p>
                </div>
                <div>
                  <span className="font-medium">pose_analysis.pose_data 長さ:</span>
                  <p className="text-muted-foreground">
                    {debugInfo.pose_analysis_pose_data_length}
                  </p>
          </div>
                                 <div>
                   <span className="font-medium">pose_data.pose_data 長さ:</span>
                   <p className="text-muted-foreground">
                     {debugInfo.pose_data_pose_data_length}
                   </p>
        </div>
                 <div className="bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
                   <span className="font-medium text-yellow-800">🔍 Zustand状態確認:</span>
                   <div className="mt-2 text-sm text-yellow-700">
                     <p>現在のZustandストア内のpose_data長さ: <strong>{poseData?.length || 0}</strong></p>
                     <p>期待値: <strong>{debugInfo.pose_analysis_pose_data_length}</strong></p>
                     {(poseData?.length || 0) === 0 && debugInfo.pose_analysis_pose_data_length > 0 && (
                       <p className="text-red-600 font-medium mt-1">
                         ⚠️ Zustandストアにpose_dataが保存されていません！
                       </p>
                     )}
                     {(poseData?.length || 0) > 0 && (
                       <p className="text-green-600 font-medium mt-1">
                         ✅ Zustandストアにpose_dataが正常に保存されています
                       </p>
                     )}
                     {zustandSaveLog && (
                       <p className="mt-2 text-xs bg-gray-100 p-2 rounded">
                         <strong>アップロード時のログ:</strong> {zustandSaveLog}
                       </p>
                     )}
          </div>
        </div>
                 <div>
                   <span className="font-medium">pose_analysis キー:</span>
                   <p className="text-muted-foreground bg-gray-100 p-2 rounded text-xs">
                     {JSON.stringify(debugInfo.pose_analysis_keys, null, 2)}
                   </p>
                 </div>
                 <div>
                   <span className="font-medium">pose_data キー:</span>
                   <p className="text-muted-foreground bg-gray-100 p-2 rounded text-xs">
                     {JSON.stringify(debugInfo.pose_data_keys, null, 2)}
                   </p>
                 </div>
                 {debugInfo.pose_analysis_sample && (
                   <details className="mt-4">
                     <summary className="cursor-pointer font-medium">pose_analysis サンプル（最初の2フレーム）</summary>
                     <pre className="text-xs bg-gray-100 p-3 rounded mt-2 overflow-auto max-h-96">
                       {JSON.stringify(debugInfo.pose_analysis_sample, null, 2)}
                     </pre>
                   </details>
                 )}
                 {debugInfo.pose_data_sample && (
                   <details className="mt-4">
                     <summary className="cursor-pointer font-medium">pose_data サンプル（最初の2フレーム）</summary>
                     <pre className="text-xs bg-gray-100 p-3 rounded mt-2 overflow-auto max-h-96">
                       {JSON.stringify(debugInfo.pose_data_sample, null, 2)}
                     </pre>
                   </details>
                 )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 画像拡大モーダル */}
      {isImageModalOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4"
          onClick={() => setIsImageModalOpen(false)}
        >
          <div className="relative max-w-7xl max-h-screen">
            <button
              onClick={() => setIsImageModalOpen(false)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300 transition-colors"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <img 
              src="/angle_reference_diagram.png" 
              alt="角度測定の基準図（拡大）"
              className="max-w-full max-h-screen object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  )
} 