'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestZScorePage() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testZScoreAnalysis = async () => {
    setLoading(true)
    try {
      console.log('🎯 Z値分析テスト開始')
      
      // 60フレームのダミーデータを生成
      const generateDummyData = () => {
        const frames = []
        for (let frame = 0; frame < 60; frame++) {
          const time = frame / 30.0
          const cyclePhase = (time * 3.0 * 2) % 2.0
          
          const leftPhase = cyclePhase % 1.0
          const rightPhase = (cyclePhase + 0.5) % 1.0
          
          const generateFootCycle = (phase: number) => {
            if (0.2 <= phase && phase <= 0.4) {
              return 1.0  // 接地期
            } else if (0.7 <= phase && phase <= 0.9) {
              return -1.0  // 遊脚期
            } else {
              return Math.sin((phase - 0.3) * 4 * Math.PI) * 0.5
            }
          }
          
          const leftAnkleY = 0.82 + 0.06 * generateFootCycle(leftPhase)
          const rightAnkleY = 0.82 + 0.06 * generateFootCycle(rightPhase)
          
          const keypoints = Array.from({length: 33}, (_, i) => {
            let x = 0.5, y = 0.5
            
            // 基本位置設定
            if (i <= 10) { x = 0.5; y = 0.1 } // 頭部
            else if (i === 11) { x = 0.45; y = 0.2 } // 左肩
            else if (i === 12) { x = 0.55; y = 0.2 } // 右肩
            else if (i === 23) { x = 0.45; y = 0.5 } // 左腰
            else if (i === 24) { x = 0.55; y = 0.5 } // 右腰
            else if (i === 25) { x = 0.43; y = 0.68 + 0.04 * generateFootCycle(leftPhase) } // 左膝
            else if (i === 26) { x = 0.57; y = 0.68 + 0.04 * generateFootCycle(rightPhase) } // 右膝
            else if (i === 27) { x = 0.41; y = leftAnkleY } // 左足首
            else if (i === 28) { x = 0.59; y = rightAnkleY } // 右足首
            
            return {
              x: Math.max(0.0, Math.min(1.0, x + (Math.random() - 0.5) * 0.01)),
              y: Math.max(0.0, Math.min(1.0, y + (Math.random() - 0.5) * 0.01)),
              z: 0.01,
              visibility: 0.9
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
      
      const dummyData = generateDummyData()
      console.log('📊 ダミーデータ生成完了:', { frames: dummyData.length })
      
      const requestData = {
        keypoints_data: dummyData,
        video_fps: 30.0
      }
      
      const response = await fetch('/api/analysis/analyze-z-score', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })
      
      console.log('📡 レスポンス受信:', response.status)
      
      if (!response.ok) {
        throw new Error(`API呼び出しエラー: ${response.status}`)
      }
      
      const zScoreResult = await response.json()
      console.log('📊 Z値分析結果:', zScoreResult)
      setResult(zScoreResult)
      
    } catch (error) {
      console.error('❌ エラー:', error)
      setResult({ status: 'error', message: String(error) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Z値分析テストページ</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={testZScoreAnalysis}
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Z値分析実行中...' : 'Z値分析をテスト'}
            </Button>
            
            {result && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-3">分析結果:</h3>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto max-h-96">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
