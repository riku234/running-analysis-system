'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Activity, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  PlayCircle,
  BarChart3,
  Loader2
} from 'lucide-react'
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
  error?: string
}

export default function ResultPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('video')

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
          解析結果 - {result.upload_info.original_filename}
        </h1>
        <p className="text-gray-600">
          AIによるランニングフォーム解析が完了しました
        </p>
        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
          <span>ファイルサイズ: {(result.upload_info.file_size / 1024 / 1024).toFixed(2)} MB</span>
          <span>アップロード日時: {new Date(result.upload_info.upload_timestamp).toLocaleString('ja-JP')}</span>
        </div>
      </div>

      {/* ステータスバッジ */}
      <div className="flex items-center space-x-4 mb-6">
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

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {[
            { id: 'video', label: '動画解析', icon: PlayCircle },
            { id: 'overview', label: '解析概要', icon: BarChart3 },
            { id: 'details', label: '詳細データ', icon: Activity },
            { id: 'advice', label: '改善アドバイス', icon: Target }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* タブコンテンツ */}
      {activeTab === 'video' && result.pose_analysis && (
        <div>
          <PoseVisualizer 
            videoUrl={videoUrl}
            poseData={result.pose_analysis}
            className="mb-8"
          />
        </div>
      )}

      {activeTab === 'overview' && result.pose_analysis && (
        <div className="space-y-6">
          {/* 解析サマリー */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-4xl font-bold text-primary-600 mb-2">
                {(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%
              </div>
              <p className="text-gray-600">骨格検出率</p>
            </div>
            <div className="card text-center">
              <div className="text-4xl font-bold text-primary-600 mb-2">
                {(result.pose_analysis.summary.average_confidence * 100).toFixed(1)}%
              </div>
              <p className="text-gray-600">平均信頼度</p>
            </div>
            <div className="card text-center">
              <div className="text-4xl font-bold text-primary-600 mb-2">
                {result.pose_analysis.summary.detected_pose_frames}
              </div>
              <p className="text-gray-600">検出フレーム数</p>
            </div>
          </div>

          {/* 動画情報 */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-4">動画情報</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.pose_analysis.video_info.fps.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">フレームレート (FPS)</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.pose_analysis.video_info.duration_seconds.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600">動画時間</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.pose_analysis.video_info.width}×{result.pose_analysis.video_info.height}
                </div>
                <div className="text-sm text-gray-600">解像度</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.pose_analysis.video_info.total_frames}
                </div>
                <div className="text-sm text-gray-600">総フレーム数</div>
              </div>
            </div>
          </div>

          {/* メッセージ */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-4">解析結果</h3>
            <p className="text-gray-700 mb-4">{result.pose_analysis.message}</p>
            {result.error && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">注意: {result.error}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'details' && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">詳細データ</h3>
          <div className="text-center py-12 text-gray-500">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>詳細なフォーム分析機能は今後実装予定です</p>
            <p className="text-sm mt-2">ケイデンス、ストライド長、関節角度などの分析を追加します</p>
          </div>
        </div>
      )}

      {activeTab === 'advice' && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">改善アドバイス</h3>
          <div className="text-center py-12 text-gray-500">
            <Target className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>個別の改善プランは今後実装予定です</p>
            <p className="text-sm mt-2">AIによるパーソナライズされたアドバイス機能を追加します</p>
          </div>
        </div>
      )}

      {/* アクションボタン */}
      <div className="flex justify-center space-x-4 mt-8">
        <button 
          className="btn-primary"
          onClick={() => window.location.href = '/'}
        >
          新しい動画を解析
        </button>
        <button 
          className="btn-secondary"
          onClick={() => window.open(videoUrl, '_blank')}
        >
          動画をダウンロード
        </button>
      </div>
    </div>
  )
} 