'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CheckCircle, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'

interface BackViewAnalysisResultProps {
  analysisResult: {
    hip_drop: {
      value: number
      unit: string
      max_drop: number
      average_drop: number
      angle_degrees: number
      max_angle_degrees: number
      average_angle_degrees: number
      status: string
    }
    vertical_oscillation: {
      value: number
      unit: string
      min_y: number
      max_y: number
      oscillation_range: number
      oscillation_range_ratio?: number
      status: string
    }
    crossover: {
      value: number
      unit: string
      left_crossover: number
      right_crossover: number
      max_crossover: number
      average_crossover: number
      left_crossover_angle?: number
      right_crossover_angle?: number
      max_crossover_angle?: number
      average_crossover_angle?: number
      landing_count: number
      status: string
    }
    summary: {
      total_frames: number
      analyzed_frames: number
      hip_drop_status: string
      vertical_oscillation_status: string
      crossover_status: string
    }
  }
}

export default function BackViewAnalysisResult({ analysisResult }: BackViewAnalysisResultProps) {
  const { hip_drop, vertical_oscillation, crossover, summary } = analysisResult

  // ステータス判定用のヘルパー関数
  const getHipDropStatus = (angleDegrees: number) => {
    if (angleDegrees < 2.0) return { icon: <CheckCircle className="h-5 w-5 text-green-500" />, text: '良好', color: 'text-green-600' }
    if (angleDegrees < 5.0) return { icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />, text: '注意', color: 'text-yellow-600' }
    return { icon: <AlertCircle className="h-5 w-5 text-red-500" />, text: '要改善', color: 'text-red-600' }
  }

  const getOscillationStatus = (range: number, isHeightRatio: boolean = false) => {
    // 身長比での判定（0.05以下が良好、0.1以上が要改善）
    // または正規化座標での判定（フォールバック用）
    const threshold = isHeightRatio ? 0.05 : 0.05
    const warningThreshold = isHeightRatio ? 0.1 : 0.1
    
    if (range < threshold) return { icon: <CheckCircle className="h-5 w-5 text-green-500" />, text: '良好', color: 'text-green-600' }
    if (range < warningThreshold) return { icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />, text: '注意', color: 'text-yellow-600' }
    return { icon: <AlertCircle className="h-5 w-5 text-red-500" />, text: '要改善', color: 'text-red-600' }
  }

  const getCrossoverStatus = (maxCrossoverAngle: number) => {
    // 角度での判定（5度以下が良好、10度以上が要改善）
    if (maxCrossoverAngle < 5.0) return { icon: <CheckCircle className="h-5 w-5 text-green-500" />, text: '良好', color: 'text-green-600' }
    if (maxCrossoverAngle < 10.0) return { icon: <AlertTriangle className="h-5 w-5 text-yellow-500" />, text: '注意', color: 'text-yellow-600' }
    return { icon: <AlertCircle className="h-5 w-5 text-red-500" />, text: '要改善', color: 'text-red-600' }
  }

  const hipDropStatus = getHipDropStatus(hip_drop.max_angle_degrees)
  const oscillationValue = vertical_oscillation.oscillation_range_ratio ?? vertical_oscillation.oscillation_range
  const oscillationStatus = getOscillationStatus(oscillationValue, !!vertical_oscillation.oscillation_range_ratio)
  const crossoverAngle = crossover.max_crossover_angle ?? crossover.max_crossover
  const crossoverStatus = getCrossoverStatus(crossoverAngle)

  return (
    <div className="space-y-6">
      {/* サマリーカード */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-gray-900">背後解析サマリー</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">総フレーム数</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_frames}</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">解析フレーム数</p>
              <p className="text-2xl font-bold text-gray-900">{summary.analyzed_frames}</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">検出率</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.total_frames > 0 
                  ? ((summary.analyzed_frames / summary.total_frames) * 100).toFixed(1)
                  : 0}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Hip Drop（骨盤の沈み込み） */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
            <TrendingDown className="h-6 w-6 mr-2 text-blue-600" />
            Hip Drop（骨盤の沈み込み）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {hipDropStatus.icon}
                <span className="font-semibold text-gray-900">ステータス</span>
              </div>
              <span className={`font-medium ${hipDropStatus.color}`}>{hipDropStatus.text}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">最大角度</p>
                <p className="text-2xl font-bold text-blue-600">{hip_drop.max_angle_degrees.toFixed(2)}°</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">平均角度</p>
                <p className="text-2xl font-bold text-blue-600">{hip_drop.average_angle_degrees.toFixed(2)}°</p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>説明:</strong> 接地時の骨盤の左右の傾きを測定します。角度が大きいほど、骨盤の沈み込みが大きいことを示します。
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Vertical Oscillation（上下動） */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
            <TrendingUp className="h-6 w-6 mr-2 text-indigo-600" />
            Vertical Oscillation（上下動）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {oscillationStatus.icon}
                <span className="font-semibold text-gray-900">ステータス</span>
              </div>
              <span className={`font-medium ${oscillationStatus.color}`}>{oscillationStatus.text}</span>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div className="p-4 bg-indigo-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">上下動範囲（身長比）</p>
                <p className="text-2xl font-bold text-indigo-600">
                  {vertical_oscillation.oscillation_range_ratio 
                    ? `${(vertical_oscillation.oscillation_range_ratio * 100).toFixed(2)}%`
                    : `${(vertical_oscillation.oscillation_range * 100).toFixed(2)}%`}
                </p>
                {vertical_oscillation.oscillation_range_ratio && (
                  <p className="text-xs text-gray-500 mt-1">
                    身長に対する割合: {vertical_oscillation.oscillation_range_ratio.toFixed(4)}
                  </p>
                )}
              </div>
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>説明:</strong> 重心の上下のブレ幅を計測します。値が小さいほど、効率的な走りを示します。
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Crossover（着地のクロスオーバー） */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
            <AlertCircle className="h-6 w-6 mr-2 text-red-600" />
            Crossover（着地のクロスオーバー）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {crossoverStatus.icon}
                <span className="font-semibold text-gray-900">ステータス</span>
              </div>
              <span className={`font-medium ${crossoverStatus.color}`}>{crossoverStatus.text}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">最大クロスオーバー角度</p>
                <p className="text-2xl font-bold text-red-600">
                  {crossover.max_crossover_angle 
                    ? `${crossover.max_crossover_angle.toFixed(2)}°`
                    : `${(crossover.max_crossover * 100).toFixed(2)}%`}
                </p>
                {crossover.max_crossover_angle && (
                  <p className="text-xs text-gray-500 mt-1">中心線からの角度</p>
                )}
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">平均クロスオーバー角度</p>
                <p className="text-2xl font-bold text-red-600">
                  {crossover.average_crossover_angle 
                    ? `${crossover.average_crossover_angle.toFixed(2)}°`
                    : `${(crossover.average_crossover * 100).toFixed(2)}%`}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">左足クロスオーバー角度</p>
                <p className="text-lg font-semibold text-gray-900">
                  {crossover.left_crossover_angle !== undefined
                    ? `${crossover.left_crossover_angle.toFixed(2)}°`
                    : `${(crossover.left_crossover * 100).toFixed(2)}%`}
                  {crossover.left_crossover_angle !== undefined && (
                    <>
                      {crossover.left_crossover_angle < 0 && <span className="text-red-600 ml-2">（内側）</span>}
                      {crossover.left_crossover_angle > 0 && <span className="text-blue-600 ml-2">（外側）</span>}
                      {crossover.left_crossover_angle === 0 && <span className="text-green-600 ml-2">（中心線上）</span>}
                    </>
                  )}
                  {crossover.left_crossover_angle === undefined && (
                    <>
                      {crossover.left_crossover < 0 && <span className="text-red-600 ml-2">（内側）</span>}
                      {crossover.left_crossover > 0 && <span className="text-blue-600 ml-2">（外側）</span>}
                    </>
                  )}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">右足クロスオーバー角度</p>
                <p className="text-lg font-semibold text-gray-900">
                  {crossover.right_crossover_angle !== undefined
                    ? `${crossover.right_crossover_angle.toFixed(2)}°`
                    : `${(crossover.right_crossover * 100).toFixed(2)}%`}
                  {crossover.right_crossover_angle !== undefined && (
                    <>
                      {crossover.right_crossover_angle < 0 && <span className="text-red-600 ml-2">（内側）</span>}
                      {crossover.right_crossover_angle > 0 && <span className="text-blue-600 ml-2">（外側）</span>}
                      {crossover.right_crossover_angle === 0 && <span className="text-green-600 ml-2">（中心線上）</span>}
                    </>
                  )}
                  {crossover.right_crossover_angle === undefined && (
                    <>
                      {crossover.right_crossover < 0 && <span className="text-red-600 ml-2">（内側）</span>}
                      {crossover.right_crossover > 0 && <span className="text-blue-600 ml-2">（外側）</span>}
                    </>
                  )}
                </p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>説明:</strong> 足が体の中心線を超えて着地していないか（シザース動作）を判定します。
                中心線からの角度で表示し、0度が中心線上、負の角度は内側へのクロス、正の角度は外側への着地を示します。検出着地数: {crossover.landing_count}回
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

