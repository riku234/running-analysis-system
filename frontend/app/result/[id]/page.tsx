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
import PoseVisualizer from '../../components/PoseVisualizer'

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
      knee_angle: number
      left_knee_angle: number
      right_knee_angle: number
      cadence: number
      stride_length: number
      contact_time: number
    }
    analysis_details: {
      total_frames_analyzed: number
      valid_frames: number
      detection_rate: number
      video_duration: number
      analysis_method: string
    }
  }
  error?: string
}

export default function ResultPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        // localStorageから結果データを取得
        const savedResult = localStorage.getItem(`analysis_result_${params.id}`)
        if (savedResult) {
          setResult(JSON.parse(savedResult))
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
                knee_angle: 165.7,
                left_knee_angle: 164.2,
                right_knee_angle: 167.1,
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
                {result.pose_analysis ? (
                  <PoseVisualizer 
                    videoUrl={videoUrl}
                    poseData={result.pose_analysis}
                  />
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                    <p>骨格解析データが利用できません</p>
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

            {/* 膝角度カード */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  膝角度
                </CardTitle>
              </CardHeader>
              <CardContent>
                {result.feature_analysis ? (
                  <div className="text-center py-4">
                    <div className="text-3xl font-bold text-indigo-600">
                      {result.feature_analysis.features.knee_angle.toFixed(1)}
                    </div>
                    <div className="text-sm text-indigo-500">degrees</div>
                    <div className="text-xs text-muted-foreground mt-2">
                      L: {result.feature_analysis.features.left_knee_angle.toFixed(1)}° 
                      R: {result.feature_analysis.features.right_knee_angle.toFixed(1)}°
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">計算中...</p>
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

        {/* フッター情報 */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>動画情報</CardTitle>
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
      </div>
    </div>
  )
} 