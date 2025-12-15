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

  // One Big Thing（最優先課題）- Z値が最も大きい課題を1つだけ選択
  const oneBigThing = useMemo(() => {
    console.log('🔍 One Big Thing - adviceData:', adviceData)
    console.log('🔍 One Big Thing - zScoreData:', zScoreData)
    
    if (!adviceData) {
      console.log('⚠️ adviceData is null or undefined')
      return null
    }

    // raw_issuesが存在するか確認
    const rawIssues = adviceData.raw_issues || []
    console.log('🔍 raw_issues:', rawIssues)
    console.log('🔍 raw_issues[0]:', rawIssues[0])
    if (rawIssues[0]) {
      console.log('🔍 raw_issues[0].observation:', rawIssues[0].observation)
      console.log('🔍 raw_issues[0].cause:', rawIssues[0].cause)
      console.log('🔍 raw_issues[0].action:', rawIssues[0].action)
      console.log('🔍 raw_issues[0].drill:', rawIssues[0].drill)
    }

    if (rawIssues.length === 0) {
      console.log('⚠️ raw_issues is empty')
      return null
    }

    // Z値データから各課題のZ値を取得して、最も大きいものを選択
    let maxZScore = 0
    let targetIssue = rawIssues[0] // デフォルトは最初の課題

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

      // target_metricから角度名リストを取得
      const targetMetric = issue.target_metric || issue.angle
      if (!targetMetric) continue

      const checkAngles = angleMapping[targetMetric] || [targetMetric, issue.angle].filter(Boolean)

      // 角度名からZ値を取得
      let issueZScore = 0
      Object.values(zScoreData).forEach(eventData => {
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
      const priorityZ = issue.severity === 'high' ? issueZScore + 2.0 : issueZScore

      if (priorityZ > maxZScore) {
        maxZScore = priorityZ
        targetIssue = issue
      }
    }

    console.log('✅ One Big Thing selected:', { 
      name: targetIssue.name, 
      severity: targetIssue.severity,
      maxZScore,
      observation: targetIssue.observation,
      cause: targetIssue.cause,
      action: targetIssue.action,
      drill: targetIssue.drill
    })

    // 専門家の見解からメッセージを構築（改行付き）
    const messageParts: string[] = []
    
    // raw_issuesから直接取得を試みる
    if (targetIssue.observation) {
      messageParts.push(`【現象】: ${targetIssue.observation}`)
    } else {
      console.warn('⚠️ observation is missing for:', targetIssue.name)
    }
    
    if (targetIssue.cause) {
      messageParts.push(`【原因】: ${targetIssue.cause}`)
    } else {
      console.warn('⚠️ cause is missing for:', targetIssue.name)
    }
    
    if (targetIssue.action) {
      messageParts.push(`【改善策】: ${targetIssue.action}`)
    } else {
      console.warn('⚠️ action is missing for:', targetIssue.name)
    }
    
    if (targetIssue.drill?.name) {
      messageParts.push(`【ドリル】: ${targetIssue.drill.name}`)
    } else {
      console.warn('⚠️ drill is missing for:', targetIssue.name)
    }

    // もしraw_issuesから取得できなかった場合、ai_advice.messageから抽出を試みる
    if (messageParts.length === 0 || (messageParts.length === 1 && targetIssue.drill?.name)) {
      console.log('⚠️ raw_issuesから情報が取得できなかったため、ai_advice.messageから抽出を試みます')
      const aiMessage = adviceData?.ai_advice?.message || ''
      
      // ai_advice.messageから課題名に一致する部分を抽出
      const issueNamePattern = new RegExp(`【${targetIssue.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}】([\\s\\S]*?)(?=【|$)`, 'i')
      const match = aiMessage.match(issueNamePattern)
      
      if (match && match[1]) {
        const issueContent = match[1].trim()
        // 現象、原因、改善策、ドリルを抽出
        const observationMatch = issueContent.match(/【現象】:\s*(.+?)(?=【|$)/)
        const causeMatch = issueContent.match(/【原因】:\s*(.+?)(?=【|$)/)
        const actionMatch = issueContent.match(/【改善策】:\s*(.+?)(?=【|$)/)
        const drillMatch = issueContent.match(/【ドリル】:\s*(.+?)(?=【|$)/)
        
        if (observationMatch) messageParts.push(`【現象】: ${observationMatch[1].trim()}`)
        if (causeMatch) messageParts.push(`【原因】: ${causeMatch[1].trim()}`)
        if (actionMatch) messageParts.push(`【改善策】: ${actionMatch[1].trim()}`)
        if (drillMatch) messageParts.push(`【ドリル】: ${drillMatch[1].trim()}`)
      }
    }

    console.log('📝 Message parts:', messageParts)
    console.log('📝 Final message:', messageParts.join('\n'))

    return {
      name: targetIssue.name,
      message: messageParts.join('\n'),
      severity: targetIssue.severity || 'medium'
    }
  }, [adviceData, zScoreData])

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
                <h3 className="text-lg font-bold text-gray-900 mb-3">{oneBigThing.name}</h3>
                <div className="text-gray-700 leading-relaxed whitespace-pre-line">
                  {oneBigThing.message}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

