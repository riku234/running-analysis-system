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
  BarChart3
} from 'lucide-react'

interface AnalysisResult {
  video_id: string
  overall_score: number
  efficiency_rating: string
  injury_risk_level: string
  issues: Array<{
    title: string
    description: string
    severity: string
    confidence_score: number
  }>
  strengths: string[]
  metrics: {
    cadence: number
    stride_length: number
    ground_contact_time: number
    vertical_oscillation: number
  }
}

export default function ResultPage({ params }: { params: { id: string } }) {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    // TODO: 実際のAPI呼び出しに置き換える
    setTimeout(() => {
      setResult({
        video_id: params.id,
        overall_score: 7.2,
        efficiency_rating: "B+",
        injury_risk_level: "medium",
        issues: [
          {
            title: "オーバーストライド",
            description: "ストライド長が理想値よりも長く、着地時の衝撃が大きくなっています。",
            severity: "medium",
            confidence_score: 0.85
          },
          {
            title: "左右非対称性",
            description: "左右の膝関節角度に5度以上の差があり、フォームの非対称性が見られます。",
            severity: "low",
            confidence_score: 0.92
          }
        ],
        strengths: [
          "適切なケイデンス（180 spm）",
          "良好な体幹姿勢",
          "安定した腕振りリズム"
        ],
        metrics: {
          cadence: 180,
          stride_length: 1.45,
          ground_contact_time: 0.25,
          vertical_oscillation: 0.08
        }
      })
      setLoading(false)
    }, 1500)
  }, [params.id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">解析結果を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">解析結果が見つかりません。</p>
      </div>
    )
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-danger-600 bg-danger-50 border-danger-200'
      case 'medium': return 'text-warning-600 bg-warning-50 border-warning-200'
      case 'low': return 'text-success-600 bg-success-50 border-success-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <AlertTriangle className="w-5 h-5" />
      case 'medium': return <Target className="w-5 h-5" />
      case 'low': return <CheckCircle className="w-5 h-5" />
      default: return null
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          解析結果 - {result.video_id}
        </h1>
        <p className="text-gray-600">
          AIによるランニングフォーム解析が完了しました
        </p>
      </div>

      {/* 総合スコア */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card text-center">
          <div className="text-4xl font-bold text-primary-600 mb-2">
            {result.overall_score}/10
          </div>
          <p className="text-gray-600">総合スコア</p>
        </div>
        <div className="card text-center">
          <div className="text-4xl font-bold text-primary-600 mb-2">
            {result.efficiency_rating}
          </div>
          <p className="text-gray-600">効率性評価</p>
        </div>
        <div className="card text-center">
          <div className={`text-4xl font-bold mb-2 ${
            result.injury_risk_level === 'low' ? 'text-success-600' :
            result.injury_risk_level === 'medium' ? 'text-warning-600' : 'text-danger-600'
          }`}>
            {result.injury_risk_level === 'low' ? '低' :
             result.injury_risk_level === 'medium' ? '中' : '高'}
          </div>
          <p className="text-gray-600">怪我リスク</p>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: '概要', icon: BarChart3 },
            { id: 'issues', label: '問題点', icon: AlertTriangle },
            { id: 'metrics', label: '詳細データ', icon: Activity },
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 強み */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-success-600 mr-2" />
              フォームの強み
            </h3>
            <ul className="space-y-2">
              {result.strengths.map((strength, index) => (
                <li key={index} className="flex items-center text-gray-700">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-3"></div>
                  {strength}
                </li>
              ))}
            </ul>
          </div>

          {/* 主要メトリクス */}
          <div className="card">
            <h3 className="text-xl font-bold text-gray-900 mb-4">主要指標</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.metrics.cadence}
                </div>
                <div className="text-sm text-gray-600">ケイデンス (spm)</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.metrics.stride_length}m
                </div>
                <div className="text-sm text-gray-600">ストライド長</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.metrics.ground_contact_time}s
                </div>
                <div className="text-sm text-gray-600">接地時間</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {result.metrics.vertical_oscillation}m
                </div>
                <div className="text-sm text-gray-600">上下動</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'issues' && (
        <div className="space-y-4">
          {result.issues.map((issue, index) => (
            <div key={index} className={`border rounded-lg p-6 ${getSeverityColor(issue.severity)}`}>
              <div className="flex items-start">
                <div className="mr-3 mt-1">
                  {getSeverityIcon(issue.severity)}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2">{issue.title}</h3>
                  <p className="mb-3">{issue.description}</p>
                  <div className="flex justify-between items-center text-sm">
                    <span>重要度: {issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低'}</span>
                    <span>信頼度: {(issue.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'metrics' && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">詳細データ</h3>
          <div className="text-center py-12 text-gray-500">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>詳細なグラフとチャートを準備中です</p>
          </div>
        </div>
      )}

      {activeTab === 'advice' && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">改善アドバイス</h3>
          <div className="text-center py-12 text-gray-500">
            <Target className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>個別の改善プランを準備中です</p>
          </div>
        </div>
      )}

      {/* アクションボタン */}
      <div className="flex justify-center space-x-4 mt-8">
        <button className="btn-primary">
          詳細レポートをダウンロード
        </button>
        <button className="btn-secondary">
          新しい動画を解析
        </button>
      </div>
    </div>
  )
} 