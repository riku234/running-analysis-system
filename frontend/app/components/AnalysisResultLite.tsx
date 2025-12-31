'use client'

import { useState, useMemo } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { ChevronRight, ChevronLeft, Play, Info, CheckCircle } from 'lucide-react'
import Image from 'next/image'

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
  // ページ管理 (0~5 の全6ページ)
  const [currentStep, setCurrentStep] = useState(0)
  const totalSteps = 6

  // ページ遷移関数
  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, totalSteps - 1))
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

  // Z値から3要素のスコアを計算
  const radarData = useMemo(() => {
    if (!zScoreData) {
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

    // Z値を100点満点スコアに変換（Z=0が100点、Z>=10が0点）
    const zToScore = (z: number): number => {
      if (z === 0) return 100
      if (z >= 10) return 0
      return Math.max(0, Math.round(100 - (z / 10) * 100))
    }

    const postureScore = zToScore(postureZ)
    const landingScore = zToScore(landingZ)
    const swingScore = zToScore(swingZ)

    return [
      {
        category: '姿勢',
        score: postureScore,
        fullMark: 100
      },
      {
        category: '着地',
        score: landingScore,
        fullMark: 100
      },
      {
        category: 'スイング',
        score: swingScore,
        fullMark: 100
      }
    ]
  }, [zScoreData])

  // 総合スコア計算（3要素の平均）
  const totalScore = useMemo(() => {
    if (radarData.length === 0) return 0
    const sum = radarData.reduce((acc, item) => acc + item.score, 0)
    return Math.round(sum / radarData.length)
  }, [radarData])

  // One Big Thing（最優先課題）- Z値が最も大きい課題を1つだけ選択
  const oneBigThing = useMemo(() => {
    if (!adviceData) {
      return null
    }

    const rawIssues = adviceData.raw_issues || []
    if (rawIssues.length === 0) {
      return null
    }

    // Z値データから各課題のZ値を取得して、最も大きいものを選択
    let maxZScore = 0
    let targetIssue = rawIssues[0]

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

    // ドリルのポイントを抽出（actionから）
    const drillPoints: string[] = []
    if (targetIssue.action) {
      // actionから箇条書きを抽出
      const lines = targetIssue.action.split('\n').filter(line => line.trim())
      lines.forEach(line => {
        // 「・」「-」「1.」などの箇条書き記号を除去
        const cleaned = line.replace(/^[・\-\d\.\s]+/, '').trim()
        if (cleaned && cleaned.length > 0) {
          drillPoints.push(cleaned)
        }
      })
    }

    // ドリル名がactionに含まれている場合は抽出
    let drillName = targetIssue.drill?.name || ''
    if (!drillName && targetIssue.action) {
      // actionの最初の行をドリル名として使用
      const firstLine = targetIssue.action.split('\n')[0]?.trim()
      if (firstLine && firstLine.length < 50) {
        drillName = firstLine
      }
    }

    return {
      name: targetIssue.name,
      observation: targetIssue.observation || '',
      cause: targetIssue.cause || '',
      action: targetIssue.action || '',
      drillName: drillName || '改善トレーニング',
      drillPoints: drillPoints.length > 0 ? drillPoints : [
        '姿勢を意識する',
        'ゆっくりと動作を行う',
        '呼吸を整える'
      ],
      drillUrl: targetIssue.drill?.url || null
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
    <div className="flex flex-col w-full h-screen bg-gray-50 overflow-hidden text-slate-800 font-sans selection:bg-red-100">
      
      {/* メインカードエリア */}
      <div className="flex-1 px-6 pt-6 pb-2 flex items-center justify-center">
        <div className="w-full max-w-7xl h-full bg-white rounded-[2rem] shadow-xl overflow-hidden relative flex flex-col border border-gray-200">
          
          {/* --- Header Decoration (Xebio Line) --- */}
          <div className="h-2 w-full flex">
            <div className="h-full w-1/3 bg-blue-900"></div>
            <div className="h-full w-2/3 bg-red-600"></div>
          </div>

          {/* --- Page 1: イントロダクション & 総合スコア - iPad最適化 --- */}
          {currentStep === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center p-6 animate-fade-in overflow-y-auto">
              <h1 className="text-3xl font-extrabold text-blue-900 mb-2 tracking-tight shrink-0">あなたのランニングスコア</h1>
              <p className="text-lg text-gray-500 mb-6 font-medium shrink-0">AI解析による総合診断結果</p>
              
              {/* レーダーチャート表示エリア */}
              <div className="w-full max-w-lg h-[380px] bg-slate-50 rounded-2xl flex items-center justify-center mb-6 relative border border-slate-200 p-4">
                {radarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis 
                        dataKey="category" 
                        tick={{ fill: '#1e3a8a', fontSize: 16, fontWeight: 700 }}
                      />
                      <PolarRadiusAxis 
                        angle={90} 
                        domain={[0, 100]} 
                        tick={{ fill: '#64748b', fontSize: 12 }}
                      />
                      <Radar
                        name="スコア"
                        dataKey="score"
                        stroke="#dc2626"
                        fill="#dc2626"
                        fillOpacity={0.6}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center text-gray-400">
                    <p className="mb-2 font-bold text-base">レーダーチャート表示エリア</p>
                    <div className="flex gap-3 text-sm justify-center mt-4">
                      <span className="px-4 py-1 bg-blue-900 text-white rounded-full font-bold">姿勢</span>
                      <span className="px-4 py-1 bg-red-600 text-white rounded-full font-bold">着地</span>
                      <span className="px-4 py-1 bg-sky-500 text-white rounded-full font-bold">スイング</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-baseline gap-2 shrink-0">
                <span className="text-blue-900 text-xl font-bold">総合スコア</span>
                <span className="text-6xl font-extrabold text-red-600 tracking-tighter drop-shadow-sm">{totalScore}</span>
                <span className="text-2xl font-bold text-red-600">点</span>
              </div>
            </div>
          )}

          {/* --- Page 2: 指標の説明 (Xebio Color Scheme) - iPad最適化（縦並び） --- */}
          {currentStep === 1 && (
            <div className="flex-1 px-8 py-6 animate-fade-in flex flex-col overflow-y-auto">
              <h2 className="text-3xl font-bold text-blue-900 mb-6 text-center">3つの指標について</h2>
              
              <div className="space-y-5 max-w-4xl mx-auto w-full">
                {/* ① 姿勢 (Navy/Blue - Stability) */}
                <div className="bg-white p-5 rounded-2xl flex items-start gap-5 border-2 border-blue-100 shadow-sm hover:shadow-lg hover:border-blue-300 transition-all">
                  <div className="w-12 h-12 bg-blue-900 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-md shrink-0">1</div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-blue-900 mb-2">姿勢</h3>
                    <p className="text-lg font-bold text-slate-700 mb-2 leading-snug">
                      「走りの土台となる、上半身の角度」
                    </p>
                    <p className="text-base text-slate-500 leading-relaxed">
                      走っている時の背筋が伸びているか、前かがみや後ろ反りになりすぎていないかを分析します。適切な前傾姿勢は、重心移動をスムーズにし、省エネで走るための鍵となります。
                    </p>
                  </div>
                </div>

                {/* ② 着地 (Red - Power/Impact) */}
                <div className="bg-white p-5 rounded-2xl flex items-start gap-5 border-2 border-red-100 shadow-sm hover:shadow-lg hover:border-red-300 transition-all">
                  <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-md shrink-0">2</div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-red-700 mb-2">着地</h3>
                    <p className="text-lg font-bold text-slate-700 mb-2 leading-snug">
                      「ブレーキをかけない、スムーズな接地」
                    </p>
                    <p className="text-base text-slate-500 leading-relaxed">
                      足が地面に着く瞬間の「すねの角度」を見ます。足が体の重心より前に出すぎているとブレーキがかかってしまいます。スムーズに次の一歩へつなげるための重要な指標です。
                    </p>
                  </div>
                </div>

                {/* ③ スイング (Sky Blue/Light Blue - Speed) */}
                <div className="bg-white p-5 rounded-2xl flex items-start gap-5 border-2 border-sky-100 shadow-sm hover:shadow-lg hover:border-sky-300 transition-all">
                  <div className="w-12 h-12 bg-sky-500 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-md shrink-0">3</div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-sky-700 mb-2">スイング</h3>
                    <p className="text-lg font-bold text-slate-700 mb-2 leading-snug">
                      「ダイナミックな脚の運び」
                    </p>
                    <p className="text-base text-slate-500 leading-relaxed">
                      太ももがしっかりと上がり、脚が前に出ているかを分析します。ここが弱いと歩幅（ストライド）が伸び悩みます。アクセル全開で走るための「脚の振り出し」の強さを表します。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* --- Page 3: 角度基準 --- */}
          {currentStep === 2 && (
            <div className="flex-1 flex flex-col items-center justify-center p-10 animate-fade-in">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-blue-900 mb-2">解析の基準となる角度</h2>
                <p className="text-xl text-slate-500">AIは以下のポイントを測定してスコアを算出しています</p>
              </div>
              
              <div className="w-full max-w-5xl h-[550px] bg-slate-50 rounded-3xl flex items-center justify-center border-2 border-dashed border-slate-300 relative overflow-hidden">
                <Image
                  src="/angle_reference_diagram.png"
                  alt="角度測定基準"
                  width={800}
                  height={600}
                  className="w-full h-full object-contain"
                  priority
                />
              </div>
            </div>
          )}

          {/* --- Page 4: One Big Thing (Red Emphasis) - 現象・原因・改善策を表示（縦並び） --- */}
          {currentStep === 3 && (
            <div className="flex-1 flex flex-col items-center p-6 animate-fade-in bg-gradient-to-br from-white via-red-50/30 to-white overflow-y-auto">
              {oneBigThing ? (
                <>
                  <div className="bg-red-600 text-white px-6 py-2 rounded-full text-base font-bold mb-5 shadow-lg flex items-center gap-2 ring-4 ring-red-100 shrink-0">
                    <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                    あなたの最優先課題 (One Big Thing)
                  </div>
                  
                  <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-6 tracking-tight text-center px-4 shrink-0">
                    {oneBigThing.name}
                  </h2>
                  
                  <div className="w-full max-w-4xl space-y-4 px-4 pb-4">
                    {/* 現象 */}
                    {oneBigThing.observation && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-blue-900">
                        <h3 className="text-xl font-bold text-blue-900 mb-3 flex items-center gap-2">
                          <span className="text-2xl">🔍</span> 現象
                        </h3>
                        <p className="text-base leading-relaxed text-slate-700 font-medium">
                          {oneBigThing.observation}
                        </p>
                      </div>
                    )}
                    
                    {/* 原因 */}
                    {oneBigThing.cause && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-red-600">
                        <h3 className="text-xl font-bold text-red-700 mb-3 flex items-center gap-2">
                          <span className="text-2xl">🧐</span> 原因
                        </h3>
                        <p className="text-base leading-relaxed text-slate-700 font-medium">
                          {oneBigThing.cause}
                        </p>
                      </div>
                    )}
                    
                    {/* 改善策 */}
                    {oneBigThing.action && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-sky-500">
                        <h3 className="text-xl font-bold text-sky-700 mb-3 flex items-center gap-2">
                          <span className="text-2xl">💡</span> 改善策
                        </h3>
                        <div className="text-base leading-relaxed text-slate-700 font-medium whitespace-pre-line">
                          {oneBigThing.action}
                        </div>
                      </div>
                    )}
                    
                    {/* データがない場合のフォールバック */}
                    {!oneBigThing.observation && !oneBigThing.cause && !oneBigThing.action && (
                      <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-gray-400">
                        <p className="text-base text-slate-500 text-center">
                          詳細なアドバイスデータがありません
                        </p>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center">
                  <p className="text-xl text-gray-500">課題データが見つかりません</p>
                </div>
              )}
            </div>
          )}

          {/* --- Page 5: 具体的なドリル (Action: Red/Blue) - iPad最適化 --- */}
          {currentStep === 4 && (
            <div className="flex-1 px-10 py-8 animate-fade-in flex flex-col overflow-y-auto">
              <h2 className="text-3xl font-bold text-blue-900 mb-8 flex items-center gap-4 justify-center">
                <span className="bg-red-600 text-white px-6 py-2 rounded-lg text-xl font-bold shadow-md tracking-wider">ACTION</span>
                改善のためのトレーニング
              </h2>
              
              {oneBigThing ? (
                <div className="flex-1 grid grid-cols-2 gap-10 items-start max-w-6xl mx-auto w-full">
                  {/* Left: Text */}
                  <div className="space-y-6">
                    <div className="bg-white border-2 border-blue-100 p-6 rounded-2xl shadow-sm">
                      <span className="text-blue-900 font-extrabold tracking-wider text-xs uppercase mb-2 block">Drill Name</span>
                      <h3 className="text-3xl font-bold text-slate-900 mb-3">{oneBigThing.drillName}</h3>
                      <p className="text-lg text-slate-700 leading-relaxed">
                        {oneBigThing.action || oneBigThing.cause || '背筋を伸ばし、一歩踏み出すごとに骨盤を「グッ」と前に押し出す意識で歩きます。'}
                      </p>
                    </div>
                    
                    <div className="bg-slate-50 p-6 rounded-2xl">
                      <h4 className="text-lg font-bold text-slate-800 mb-5 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-red-600" />
                        意識するポイント
                      </h4>
                      <ul className="space-y-3">
                        {oneBigThing.drillPoints.map((point, idx) => (
                          <li key={idx} className="flex items-center gap-3 text-lg text-slate-700 font-medium bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                            <span className="w-7 h-7 bg-blue-900 text-white rounded-full flex items-center justify-center font-bold text-xs shrink-0">
                              {idx + 1}
                            </span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Right: Video Player */}
                  <div className="h-full max-h-[450px] w-full bg-black rounded-2xl overflow-hidden relative group cursor-pointer shadow-2xl ring-4 ring-slate-100">
                    {oneBigThing.drillUrl ? (
                      <video 
                        src={oneBigThing.drillUrl} 
                        className="w-full h-full object-cover" 
                        controls
                        playsInline
                      />
                    ) : (
                      <>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-28 h-28 bg-red-600/90 backdrop-blur-md rounded-full flex items-center justify-center border-4 border-white transition-transform group-hover:scale-105 shadow-xl">
                            <Play className="w-12 h-12 text-white ml-2 fill-white" />
                          </div>
                        </div>
                        <div className="absolute bottom-8 left-8 text-white">
                          <span className="px-3 py-1 bg-blue-900 rounded-lg text-xs font-bold mb-2 inline-block shadow-lg border border-blue-700">WATCH</span>
                          <p className="text-2xl font-bold">ドリル実演動画</p>
                          <p className="text-gray-300 mt-1 text-base">動画URLが設定されていません</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-2xl text-gray-500">ドリルデータが見つかりません</p>
                </div>
              )}
            </div>
          )}

          {/* --- Page 6: おすすめのシューズ (Title Only) --- */}
          {currentStep === 5 && (
            <div className="flex-1 flex flex-col items-center justify-center p-10 animate-fade-in bg-slate-50">
              <div className="text-center">
                <h2 className="text-5xl font-extrabold text-blue-900 mb-6 tracking-tight">あなたに最適のランニングシューズ</h2>
                <div className="w-24 h-2 bg-red-600 mx-auto rounded-full"></div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* --- Footer Navigation (Xebio Style) --- */}
      <div className="h-24 bg-white border-t border-slate-200 px-12 flex items-center justify-between shadow-lg z-10">
        
        {/* Back Button (Neutral/Navy) */}
        <button 
          onClick={prevStep} 
          disabled={currentStep === 0}
          className={`flex items-center gap-3 px-8 py-4 rounded-full text-xl font-bold transition-all transform active:scale-95 ${
            currentStep === 0 
              ? 'opacity-0 pointer-events-none' 
              : 'text-slate-500 hover:bg-slate-100 hover:text-blue-900'
          }`}
        >
          <ChevronLeft className="w-7 h-7" />
          戻る
        </button>

        {/* Progress Bar (Blue & Red) */}
        <div className="flex gap-4">
          {[...Array(totalSteps)].map((_, i) => (
            <div 
              key={i} 
              className={`h-3 rounded-full transition-all duration-500 ease-out ${
                i === currentStep 
                  ? 'w-16 bg-red-600'  // Active is Red
                  : i < currentStep 
                    ? 'w-3 bg-blue-900' // Passed is Navy
                    : 'w-3 bg-slate-200' // Future is Gray
              }`}
            />
          ))}
        </div>

        {/* Next Button (Primary Red) */}
        <button 
          onClick={nextStep} 
          disabled={currentStep === totalSteps - 1}
          className={`flex items-center gap-3 px-10 py-4 rounded-full text-xl font-bold shadow-lg transition-all transform active:scale-95 ${
            currentStep === totalSteps - 1 
              ? 'bg-slate-300 text-white cursor-default shadow-none' 
              : 'bg-red-600 text-white hover:bg-red-700 hover:shadow-xl ring-4 ring-red-100'
          }`}
        >
          {currentStep === totalSteps - 1 ? '完了' : '次へ'}
          {currentStep !== totalSteps - 1 && <ChevronRight className="w-7 h-7" />}
        </button>
      </div>
    </div>
  )
}
