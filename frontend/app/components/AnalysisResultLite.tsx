'use client'

import { useMemo } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

interface ZScoreData {
  [event: string]: {
    [angle: string]: number
  }
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
    }>
  } | null
}

export default function AnalysisResultLite({ zScoreData, adviceData }: AnalysisResultLiteProps) {
  // デバッグ: データ構造を確認
  console.log('🔍 AnalysisResultLite - zScoreData:', zScoreData)
  console.log('🔍 AnalysisResultLite - adviceData:', adviceData)

  // Z値から3要素のスコアを計算
  const radarData = useMemo(() => {
    if (!zScoreData) {
      console.log('⚠️ zScoreData is null or undefined')
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
      console.log(`📊 getMaxZScore for ${angleNames.join(', ')}: ${maxZ}`)
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

    console.log('📊 Z値取得結果:', { postureZ, landingZ, swingZ })

    // Z値を100点満点スコアに変換（Z=0が100点、Z>=10が0点）
    const zToScore = (z: number): number => {
      if (z === 0) return 100
      if (z >= 10) return 0
      return Math.max(0, Math.round(100 - (z / 10) * 100))
    }

    const postureScore = zToScore(postureZ)
    const landingScore = zToScore(landingZ)
    const swingScore = zToScore(swingZ)

    console.log('📊 スコア変換結果:', {
      POSTURE: { z: postureZ, score: postureScore },
      LANDING: { z: landingZ, score: landingScore },
      SWING: { z: swingZ, score: swingScore }
    })

    return [
      {
        category: 'POSTURE',
        score: postureScore,
        fullMark: 100
      },
      {
        category: 'LANDING',
        score: landingScore,
        fullMark: 100
      },
      {
        category: 'SWING',
        score: swingScore,
        fullMark: 100
      }
    ]
  }, [zScoreData])

  // ステータスリスト用のデータ
  const statusList = useMemo(() => {
    if (!zScoreData) return []

    const getStatus = (category: string, angleNames: string[]) => {
      let maxZ = 0
      Object.values(zScoreData).forEach(eventData => {
        angleNames.forEach(angleName => {
          const value = eventData[angleName] || 
                       eventData[angleName.replace('角度', '')] ||
                       eventData[`${angleName}_z`] ||
                       eventData[`left_${angleName}_z`] ||
                       eventData[`right_${angleName}_z`]
          
          if (value !== undefined) {
            const absZ = Math.abs(value)
            if (absZ > maxZ) maxZ = absZ
          }
        })
      })

      let icon = <CheckCircle className="h-5 w-5 text-green-500" />
      let status = '良好'
      let color = 'text-green-600'

      if (maxZ >= 2.0) {
        icon = <AlertCircle className="h-5 w-5 text-red-500" />
        status = '要改善'
        color = 'text-red-600'
      } else if (maxZ >= 1.0) {
        icon = <AlertTriangle className="h-5 w-5 text-yellow-500" />
        status = '注意'
        color = 'text-yellow-600'
      }

      return { category, maxZ, icon, status, color }
    }

    return [
      getStatus('POSTURE', ['体幹角度', 'trunk_angle']),
      getStatus('LANDING', ['右下腿角度', '左下腿角度', 'shank_angle', 'right_shank_angle', 'left_shank_angle']),
      getStatus('SWING', ['右大腿角度', '左大腿角度', 'thigh_angle', 'right_thigh_angle', 'left_thigh_angle'])
    ]
  }, [zScoreData])

  // One Big Thing（最優先課題）
  const oneBigThing = useMemo(() => {
    console.log('🔍 One Big Thing - adviceData:', adviceData)
    
    if (!adviceData) {
      console.log('⚠️ adviceData is null or undefined')
      return null
    }

    // raw_issuesが存在するか確認
    const rawIssues = adviceData.raw_issues || []
    console.log('🔍 raw_issues:', rawIssues)

    if (rawIssues.length === 0) {
      // raw_issuesがない場合、ai_adviceから情報を取得
      if (adviceData.ai_advice) {
        const keyPoints = adviceData.ai_advice.key_points || []
        if (keyPoints.length > 0) {
          return {
            name: adviceData.ai_advice.title || 'フォーム改善',
            message: adviceData.ai_advice.message || keyPoints[0],
            severity: 'medium' as const
          }
        }
      }
      console.log('⚠️ raw_issues and ai_advice are both empty')
      return null
    }

    // raw_issuesからseverityがhighのものを優先的に選択
    const highPriorityIssues = rawIssues.filter(issue => issue.severity === 'high')
    const targetIssue = highPriorityIssues.length > 0 ? highPriorityIssues[0] : rawIssues[0]

    // 対応するメッセージを取得
    const message = adviceData.ai_advice?.message || 
                   adviceData.ai_advice?.key_points?.[0] || 
                   `${targetIssue.name}の改善に取り組みましょう。`

    console.log('✅ One Big Thing selected:', { name: targetIssue.name, message })

    return {
      name: targetIssue.name,
      message: message,
      severity: targetIssue.severity || 'medium'
    }
  }, [adviceData])

  if (!zScoreData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Z値データがありません</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 3要素レーダーチャート */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-gray-900">3つの力</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis 
                  dataKey="category" 
                  tick={{ fill: '#374151', fontSize: 14, fontWeight: 600 }}
                />
                <PolarRadiusAxis 
                  angle={90} 
                  domain={[0, 100]} 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                />
                <Radar
                  name="スコア"
                  dataKey="score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* ステータスリスト */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-gray-900">ステータス</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {statusList.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {item.icon}
                  <span className="font-semibold text-gray-900">{item.category}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`font-medium ${item.color}`}>{item.status}</span>
                  <span className="text-sm text-gray-500">(Z値: {item.maxZ.toFixed(2)})</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* One Big Thing */}
      {oneBigThing && (
        <Card className="shadow-lg border-2 border-blue-500">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
              <span className="text-2xl mr-2">🎯</span>
              One Big Thing
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="text-lg font-bold text-gray-900 mb-2">{oneBigThing.name}</h3>
                <p className="text-gray-700 leading-relaxed">{oneBigThing.message}</p>
              </div>
              {adviceData?.ai_advice?.key_points && adviceData.ai_advice.key_points.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold text-gray-900 mb-2">ポイント</h4>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {adviceData.ai_advice.key_points.slice(0, 3).map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

