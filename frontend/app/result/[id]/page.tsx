'use client'

import { useState, useEffect } from 'react'
import { 
  Play, 
  Target, 
  Activity, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Download,
  Loader2,
  FileVideo,
  Zap
} from 'lucide-react'
import PoseVisualizer from '../../components/PoseVisualizer'

interface UploadInfo {
  file_id: string
  original_filename: string
  saved_filename: string
  file_size: number
  content_type: string
  upload_timestamp: string
  file_extension: string
}

interface PoseAnalysisResult {
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

interface AnalysisResult {
  status: string
  message: string
  upload_info: UploadInfo
  pose_analysis: PoseAnalysisResult | null
  error?: string
}

export default function ResultPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('visualization')

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
            message: "動画アップロードと骨格解析が完了しました",
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
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">解析結果を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">結果が見つかりません</h2>
        <p className="text-gray-600">解析結果を取得できませんでした。</p>
      </div>
    )
  }

  const videoUrl = `/api/video/stream/${result.upload_info.saved_filename}`

  return (
    <div className="max-w-7xl mx-auto">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ランニングフォーム解析結果
        </h1>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center">
            <FileVideo className="h-4 w-4 mr-1" />
            {result.upload_info.original_filename}
          </div>
          <div className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {new Date(result.upload_info.upload_timestamp).toLocaleString('ja-JP')}
          </div>
          <div className="flex items-center">
            <Download className="h-4 w-4 mr-1" />
            {(result.upload_info.file_size / 1024 / 1024).toFixed(1)} MB
          </div>
        </div>
      </div>

      {/* ステータス表示 */}
      <div className="mb-6">
        {result.status === 'success' && result.pose_analysis ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <div>
                <h3 className="font-medium text-green-800">解析完了</h3>
                <p className="text-green-700">{result.message}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
              <div>
                <h3 className="font-medium text-yellow-800">部分的な処理</h3>
                <p className="text-yellow-700">{result.message}</p>
                {result.error && (
                  <p className="text-sm text-yellow-600 mt-1">エラー: {result.error}</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('visualization')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'visualization'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Play className="h-4 w-4 inline mr-1" />
            骨格可視化
          </button>
          <button
            onClick={() => setActiveTab('metrics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'metrics'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BarChart3 className="h-4 w-4 inline mr-1" />
            詳細データ
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analysis'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Target className="h-4 w-4 inline mr-1" />
            フォーム分析
          </button>
        </nav>
      </div>

      {/* タブコンテンツ */}
      {activeTab === 'visualization' && result.pose_analysis && (
        <div>
          <h2 className="text-xl font-semibold mb-4">骨格検出結果の可視化</h2>
          <PoseVisualizer
            videoUrl={videoUrl}
            poseData={result.pose_analysis}
            className="mb-6"
          />
        </div>
      )}

      {activeTab === 'metrics' && result.pose_analysis && (
        <div>
          <h2 className="text-xl font-semibold mb-4">詳細統計データ</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* 動画情報 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center">
                <FileVideo className="h-5 w-5 mr-2 text-blue-500" />
                動画情報
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">解像度</span>
                  <span className="font-medium">{result.pose_analysis.video_info.width} × {result.pose_analysis.video_info.height}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">フレームレート</span>
                  <span className="font-medium">{result.pose_analysis.video_info.fps} FPS</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">総フレーム数</span>
                  <span className="font-medium">{result.pose_analysis.video_info.total_frames}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">動画時間</span>
                  <span className="font-medium">{result.pose_analysis.video_info.duration_seconds.toFixed(1)}秒</span>
                </div>
              </div>
            </div>

            {/* 検出統計 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2 text-green-500" />
                骨格検出統計
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">検出フレーム</span>
                  <span className="font-medium">{result.pose_analysis.summary.detected_pose_frames}/{result.pose_analysis.summary.total_processed_frames}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">検出率</span>
                  <span className="font-medium">{(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">平均信頼度</span>
                  <span className="font-medium">{(result.pose_analysis.summary.average_confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">ランドマーク数</span>
                  <span className="font-medium">{result.pose_analysis.summary.mediapipe_landmarks_count}点</span>
                </div>
              </div>
            </div>
          </div>

          {/* 処理品質インジケーター */}
          <div className="mt-6 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <Zap className="h-5 w-5 mr-2 text-yellow-500" />
              処理品質評価
            </h3>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">検出率</span>
                  <span className="text-sm text-gray-500">{(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${result.pose_analysis.summary.detection_rate * 100}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">平均信頼度</span>
                  <span className="text-sm text-gray-500">{(result.pose_analysis.summary.average_confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${result.pose_analysis.summary.average_confidence * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analysis' && (
        <div>
          <h2 className="text-xl font-semibold mb-4">フォーム分析（開発中）</h2>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <Target className="h-6 w-6 text-blue-500 mr-2" />
              <h3 className="text-lg font-medium text-blue-800">詳細分析機能</h3>
            </div>
            
            <div className="text-blue-700 space-y-2">
              <p>以下の高度な分析機能を開発中です：</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>関節角度の時系列分析</li>
                <li>ストライド長・ケイデンスの計算</li>
                <li>重心移動軌跡の評価</li>
                <li>左右対称性の定量的評価</li>
                <li>着地パターンの分類</li>
                <li>効率性スコアの算出</li>
                <li>怪我リスクの評価</li>
                <li>パーソナライズされた改善提案</li>
              </ul>
            </div>
            
            <div className="mt-4 text-sm text-blue-600">
              これらの機能は Feature Extraction、Analysis、Advice Generation サービスの実装により提供予定です。
            </div>
          </div>
        </div>
      )}

      {!result.pose_analysis && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <AlertTriangle className="h-12 w-12 text-orange-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">骨格解析データが利用できません</h3>
          <p className="text-gray-600">動画は正常にアップロードされましたが、骨格解析が完了していません。</p>
        </div>
      )}
    </div>
  )
} 