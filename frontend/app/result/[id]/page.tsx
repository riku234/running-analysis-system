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
      trunk_angle?: { avg: number; min: number; max: number }
      left_hip_angle?: { avg: number; min: number; max: number }
      right_hip_angle?: { avg: number; min: number; max: number }
      left_knee_angle?: { avg: number; min: number; max: number }
      right_knee_angle?: { avg: number; min: number; max: number }
      left_ankle_angle?: { avg: number; min: number; max: number }
      right_ankle_angle?: { avg: number; min: number; max: number }
      left_elbow_angle?: { avg: number; min: number; max: number }
      right_elbow_angle?: { avg: number; min: number; max: number }
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
  
  // Zustandストアからpose_dataを取得
  const { poseData, videoInfo, uploadInfo } = useResultStore()

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
          
          // ★★★ データの内容をデバッグ ★★★
          console.log("📊 localStorage軽量データ:", lightResult)
          console.log("📊 Zustandのpose_data長さ:", poseData?.length || 0)
          console.log("📊 完成したcompleteResult:", completeResult)
          console.log("📊 pose_analysis.pose_data長さ:", completeResult.pose_analysis.pose_data?.length || 0)
          
          // ★★★ アドバイスデータのデバッグ ★★★
          console.log("============================================================")
          console.log("💡 [FRONTEND] アドバイスデータの確認:")
          console.log("   - advice_analysis存在:", !!completeResult.advice_analysis)
          console.log("   - advice_results存在:", !!completeResult.advice_results)
          if (completeResult.advice_analysis) {
            console.log("   - advice_analysis内容:", completeResult.advice_analysis)
            console.log("   - advice_listの長さ:", completeResult.advice_analysis.advice_list?.length || 0)
          }
          if (completeResult.advice_results) {
            console.log("   - advice_results内容:", completeResult.advice_results)
            console.log("   - advice_results.advice_listの長さ:", completeResult.advice_results.advice_list?.length || 0)
          }
          console.log("============================================================")
          
          setResult(completeResult)
          setLoading(false)
          return
        }
        
        // localStorageにデータがない場合はダミーデータで動作確認
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
                total_processed_frames: 300,
                detected_pose_frames: 285,
                detection_rate: 0.95,
                average_confidence: 0.87,
                mediapipe_landmarks_count: 33
              }
            },
            feature_analysis: {
              status: "success",
              message: "300フレームから特徴量を抽出しました",
              features: {
                trunk_angle: { avg: 15.2, min: 12.1, max: 18.5 },
                left_hip_angle: { avg: 140.8, min: 110.3, max: 165.2 },
                right_hip_angle: { avg: 142.1, min: 112.5, max: 168.0 },
                left_knee_angle: { avg: 155.6, min: 130.8, max: 178.1 },
                right_knee_angle: { avg: 154.9, min: 128.9, max: 177.5 },
                left_ankle_angle: { avg: 85.3, min: 70.1, max: 95.4 },
                right_ankle_angle: { avg: 86.1, min: 72.3, max: 98.2 },
                left_elbow_angle: { avg: 95.7, min: 75.4, max: 115.8 },
                right_elbow_angle: { avg: 94.8, min: 74.9, max: 114.5 },
                // 後方互換性のため
                cadence: 182.0,
                stride_length: 1.35,
                contact_time: 245.5
              },
              analysis_details: {
                total_frames_analyzed: 300,
                valid_frames: 285,
                detection_rate: 0.95,
                video_duration: 10.0,
                analysis_method: "mediapipe_pose_landmarks"
              }
            },
            issue_analysis: {
              status: "success",
              message: "フォーム分析完了：1つの改善点を検出しました",
              issues: ["地面に足がついている時間が長く、エネルギー効率が低下している可能性があります。"],
              analysis_details: {
                analyzed_metrics: {
                  cadence: { value: 182.0, unit: "steps/min", threshold: 170, status: "良好" },
                  knee_angle_at_landing: { value: 165.7, unit: "degrees", threshold: 170, status: "良好" },
                  ground_contact_time: { value: 245.5, unit: "ms", threshold: 240, status: "要改善" }
                },
                total_issues: 1,
                overall_assessment: "1つの改善点が見つかりました"
              }
        }
      })
      setLoading(false)
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
            {result.pose_analysis && (
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                検出率: {(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%
        </div>
            )}
          </div>
        </div>

        {/* 2カラムレイアウト */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* 左カラム：動画プレイヤー（2/3幅） */}
          <div className="lg:col-span-2">
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

          {/* 右カラム：解析結果（1/3幅） */}
          <div className="space-y-6">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  解析結果
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.pose_analysis && (
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

            {/* 特徴量データ */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  ケイデンス
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.feature_analysis ? (
                  <div className="text-center py-4">
                    <div className="text-3xl font-bold text-orange-600">
                      {result.feature_analysis.features.cadence}
                    </div>
                    <div className="text-sm text-orange-500">steps/min</div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Clock className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  ストライド長
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.feature_analysis ? (
                  <div className="text-center py-4">
                    <div className="text-3xl font-bold text-teal-600">
                      {result.feature_analysis.features.stride_length}
                    </div>
                    <div className="text-sm text-teal-500">meters</div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  接地時間
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.feature_analysis ? (
                  <div className="text-center py-4">
                    <div className="text-3xl font-bold text-pink-600">
                      {result.feature_analysis.features.contact_time}
                    </div>
                    <div className="text-sm text-pink-500">ms</div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Clock className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
          </div>
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
              </CardHeader>
              <CardContent>
                {result.feature_analysis?.features && (
                  <div className="space-y-4">
                    {/* 膝角度 */}
                    {result.feature_analysis.features.left_knee_angle && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center">
                          <div className="text-lg font-bold text-indigo-600">
                            左膝: {result.feature_analysis.features.left_knee_angle.avg.toFixed(1)}°
                          </div>
                          <div className="text-xs text-muted-foreground">
                            平均 {result.feature_analysis.features.left_knee_angle.min.toFixed(1)}°-{result.feature_analysis.features.left_knee_angle.max.toFixed(1)}°
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-indigo-600">
                            右膝: {result.feature_analysis.features.right_knee_angle?.avg.toFixed(1)}°
                          </div>
                          <div className="text-xs text-muted-foreground">
                            平均 {result.feature_analysis.features.right_knee_angle?.min.toFixed(1)}°-{result.feature_analysis.features.right_knee_angle?.max.toFixed(1)}°
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* 体幹角度 */}
                    {result.feature_analysis.features.trunk_angle && (
                      <div className="text-center border-t pt-2">
                        <div className="text-lg font-bold text-green-600">
                          体幹前傾: {result.feature_analysis.features.trunk_angle.avg.toFixed(1)}°
                        </div>
                        <div className="text-xs text-muted-foreground">
                          範囲 {result.feature_analysis.features.trunk_angle.min.toFixed(1)}°-{result.feature_analysis.features.trunk_angle.max.toFixed(1)}°
                        </div>
                      </div>
                    )}
                    
                    {/* 股関節角度 */}
                    {result.feature_analysis.features.left_hip_angle && (
                      <div className="grid grid-cols-2 gap-4 border-t pt-2">
                        <div className="text-center">
                          <div className="text-lg font-bold text-purple-600">
                            左股関節: {result.feature_analysis.features.left_hip_angle.avg.toFixed(1)}°
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-purple-600">
                            右股関節: {result.feature_analysis.features.right_hip_angle?.avg.toFixed(1)}°
                          </div>
                        </div>
                      </div>
                    )}
                </div>
                )} 
                {!result.feature_analysis && (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
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