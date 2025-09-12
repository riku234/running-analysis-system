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
  Download
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import PoseVisualizer from '@/app/components/PoseVisualizer'
import { useResultStore } from '@/lib/store'

interface ComparisonResult {
  status: string
  message?: string
  comparison_data?: {
    status: string
    comparison_results: {
      [indicator: string]: {
        user_data: any
        standard_data: any
        differences: {
          [stat: string]: {
            user_value: number
            standard_value: number
            difference: number
            percentage_diff: number
            statistical_judgment: string
            needs_improvement: boolean
          }
        }
      }
    }
    summary: {
      total_indicators: number
      indicators_compared: string[]
    }
  }
  analysis_summary?: {
    total_indicators: number
    issues_detected: number
    indicators_compared: string[]
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
    advice_list: Array<{
      issue: string
      title: string
      description: string
      exercise: string
    }>
    summary: {
      total_issues: number
      total_advice: number
      generation_timestamp: string
    }
  }
  advice_results?: {
    status: string
    message: string
    video_id: string
    advice_list: Array<{
      issue: string
      title: string
      description: string
      exercise: string
    }>
    summary: {
      total_issues: number
      total_advice: number
      generation_timestamp: string
    }
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
  const [comparisonData, setComparisonData] = useState<ComparisonResult | null>(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  
  // Zustandストアからpose_dataを取得
  const { poseData, videoInfo, uploadInfo } = useResultStore()

  // ユーザー統計値と標準モデルの比較を実行
  const fetchComparison = async (userStats: any) => {
    if (!userStats || comparisonLoading) return

    setComparisonLoading(true)
    try {
      console.log('🔍 比較データ取得開始:', userStats)
      
      const response = await fetch('/api/feature_extraction/compare_with_standard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userStats),
      })

      if (!response.ok) {
        throw new Error(`比較API呼び出しエラー: ${response.status}`)
      }

      const comparisonResult = await response.json()
      console.log('📊 比較結果取得完了:', comparisonResult)
      
      // レスポンスデータの構造を検証
      if (comparisonResult && typeof comparisonResult === 'object') {
        setComparisonData(comparisonResult)
      } else {
        console.error('❌ 無効な比較データ構造:', comparisonResult)
        setComparisonData({ status: 'error', message: '比較データの構造が無効です' })
      }
    } catch (error) {
      console.error('❌ 比較データ取得エラー:', error)
      setComparisonData({ status: 'error', message: `比較データ取得に失敗しました: ${error}` })
    } finally {
      setComparisonLoading(false)
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
            
            fetchComparison(convertedStats)
          }
          
          return
        }
        
        // localStorageにデータがない場合はダミーデータを表示

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
        console.log('📊 ダミーデータで比較処理開始...')
        fetchComparison(dummyStats)
    }, 1500)
      } catch (error) {
        console.error('結果取得エラー:', error)
        setLoading(false)
      }
    }

    fetchResult()
  }, [params.id])

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

  const videoUrl = `/api/video/stream/${result.upload_info.saved_filename}`

  return (
    <div className="min-h-screen bg-gradient-running">
      <div className="container mx-auto p-6 space-y-6">
      {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-primary-gradient">解析結果</h1>
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

        {/* 2カラムレイアウト - 動画と解析結果を横並び */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* 左カラム：動画プレイヤー（1/2幅） */}
          <div>
            <Card className="shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PlayCircle className="h-5 w-5 mr-2" />
                  動画解析
                </CardTitle>
                <CardDescription>
                  骨格キーポイントがリアルタイムで表示されます
                </CardDescription>
              </CardHeader>
              <CardContent>
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
          </div>

          {/* 右カラム：解析結果（1/2幅） */}
          <div className="space-y-6">
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

            {/* 関節角度カード */}
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

            {/* ランニングメトリクスカード */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  ランニングメトリクス
                </CardTitle>
                <div className="text-sm text-muted-foreground mt-1">
                  重心上下動とピッチ（ケイデンス）
                </div>
              </CardHeader>
              <CardContent>
                {result.feature_analysis?.features && (
                  <div className="space-y-4">
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

            {/* 標準モデル比較カード */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  フォーム比較分析
                </CardTitle>
                <CardDescription>
                  あなたのランニングフォームと標準モデルとの詳細比較
                </CardDescription>
              </CardHeader>
              <CardContent>
                {comparisonLoading ? (
                  <div className="text-center py-6">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
                    <p className="text-sm text-muted-foreground">標準モデルと比較中...</p>
                  </div>
                ) : comparisonData?.status === 'success' && comparisonData?.comparison_data?.comparison_results ? (
                  <div className="space-y-6">
                    {/* 比較サマリー */}
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-700">
                            {comparisonData.comparison_data?.summary?.total_indicators || 0}
                          </div>
                          <div className="text-sm text-blue-600">比較項目数</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-red-600">
                            {(() => {
                              // 改善推奨項目数を計算
                              const results = comparisonData.comparison_data?.comparison_results || {}
                              let issuesDetected = 0
                              Object.values(results).forEach((indicator: any) => {
                                Object.values(indicator?.differences || {}).forEach((diff: any) => {
                                  if (diff?.needs_improvement) issuesDetected++
                                })
                              })
                              return issuesDetected
                            })()}
                          </div>
                          <div className="text-sm text-red-500">改善推奨項目</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-green-600">
                            {(() => {
                              // 正常範囲項目数を計算
                              const results = comparisonData.comparison_data?.comparison_results || {}
                              let totalItems = 0
                              let issuesDetected = 0
                              Object.values(results).forEach((indicator: any) => {
                                Object.values(indicator?.differences || {}).forEach((diff: any) => {
                                  totalItems++
                                  if (diff?.needs_improvement) issuesDetected++
                                })
                              })
                              return totalItems - issuesDetected
                            })()}
                          </div>
                          <div className="text-sm text-green-500">正常範囲項目</div>
                        </div>
                      </div>
                    </div>

                    {/* 詳細比較データ */}
                    <div className="space-y-4">
                      {Object.entries(comparisonData.comparison_data?.comparison_results || {}).map(([indicator, data]) => (
                        <div key={indicator} className="border rounded-lg p-4 bg-white">
                          <h3 className="text-lg font-semibold mb-3 text-gray-800">
                            📊 {indicator}
                          </h3>
                          <div className="grid gap-3">
                            {Object.entries(data?.differences || {}).map(([statKey, diff]) => {
                              const judgmentColor = diff?.statistical_judgment === '課題あり' ? 'text-red-600' : 'text-green-600'
                              const judgmentIcon = diff?.statistical_judgment === '課題あり' ? '🔴' : '🟢'
                              const diffValue = (diff?.difference || 0) >= 0 ? `+${(diff?.difference || 0).toFixed(1)}` : (diff?.difference || 0).toFixed(1)
                              
                              return (
                                <div 
                                  key={statKey} 
                                  className={`p-3 rounded-lg border-l-4 ${
                                    diff?.statistical_judgment === '課題あり' 
                                      ? 'bg-red-50 border-red-400' 
                                      : 'bg-green-50 border-green-400'
                                  }`}
                                >
                                  <div className="flex justify-between items-center">
                                    <div>
                                      <div className="font-medium text-gray-700">
                                        {statKey === 'mean' && '平均値'}
                                        {statKey === 'max' && '最大値'}
                                        {statKey === 'min' && '最小値'}
                                      </div>
                                      <div className="text-sm text-gray-600">
                                        あなた: <span className="font-semibold">{(diff?.user_value || 0).toFixed(1)}°</span> | 
                                        標準: <span className="font-semibold">{(diff?.standard_value || 0).toFixed(1)}°</span> | 
                                        差分: <span className={`font-semibold ${(diff?.difference || 0) >= 0 ? 'text-blue-600' : 'text-purple-600'}`}>
                                          {diffValue}°
                                        </span>
                                      </div>
                                    </div>
                                    <div className={`text-center ${judgmentColor}`}>
                                      <div className="text-2xl">{judgmentIcon}</div>
                                      <div className="text-xs font-medium">
                                        [{diff?.statistical_judgment || '判定不可'}]
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* 判定基準の説明 */}
                    <div className="bg-gray-50 p-4 rounded-lg border">
                      <h4 className="font-semibold text-gray-800 mb-2">📖 判定基準について</h4>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p><span className="font-medium">🔴 課題あり:</span> 統計的に有意な差が検出 → フォーム改善を推奨</p>
                        <p><span className="font-medium">🟢 OK:</span> 正常範囲内 → 現在のフォームを維持</p>
                        <p className="text-xs mt-2 text-gray-500">
                          ※ 変動係数(CV)と重み付け変動度を用いた科学的分析により判定
                        </p>
                      </div>
                    </div>
                  </div>
                ) : comparisonData?.status === 'error' ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                    <p className="text-sm">比較データの取得に失敗しました</p>
                    <p className="text-xs mt-1">しばらく待ってから再度お試しください</p>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">比較データを準備中...</p>
                    <p className="text-xs mt-1">角度データが利用可能になると自動で比較を開始します</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 課題分析カード */}
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

            {/* アクションボタン */}
            <div className="space-y-3">
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
          </div>
        </div>

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

                  {/* アドバイスセクション */}
          {(() => {
            // advice_resultsまたはadvice_analysisからアドバイスリストを取得
            const adviceList = result?.advice_results?.advice_list || result?.advice_analysis?.advice_list || [];
            
            if (adviceList.length > 0) {
              return (
                <Card className="shadow-xl mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      💡 改善アドバイス
                    </CardTitle>
                    <CardDescription>
                      検出された課題に基づく具体的な改善提案
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {adviceList.map((advice: any, index: number) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4">
                          <h3 className="font-semibold text-lg mb-2">{advice.title}</h3>
                          <p className="text-gray-700 mb-3">{advice.description}</p>
                          <div className="bg-blue-50 p-3 rounded-md">
                            <h4 className="font-medium text-blue-800 mb-1">推奨エクササイズ:</h4>
                            <p className="text-blue-700">{advice.exercise}</p>
              </div>
            </div>
          ))}
        </div>
                  </CardContent>
                </Card>
              );
            } else {
              // アドバイスがない場合の表示
              return (
                <Card className="shadow-xl mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      ✨ 素晴らしい走りです！
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700">
                      今回の分析では、特に改善を要する大きな課題は見つかりませんでした。現在の良いフォームを維持しましょう！
                    </p>
                  </CardContent>
                </Card>
              );
            }
          })()}

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
    </div>
  )
} 