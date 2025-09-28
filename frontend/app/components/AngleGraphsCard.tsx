'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, Settings2 } from 'lucide-react'

// MediaPipeランドマークのインデックス定義
const LANDMARK_INDICES = {
  left_shoulder: 11,
  right_shoulder: 12,
  left_elbow: 13,
  right_elbow: 14,
  left_wrist: 15,
  right_wrist: 16,
  left_hip: 23,
  right_hip: 24,
  left_knee: 25,
  right_knee: 26,
  left_ankle: 27,
  right_ankle: 28,
  left_foot_index: 31,
  right_foot_index: 32
}

// 角度計算関数
const calculateAbsoluteAngleWithVertical = (vector: [number, number], forwardPositive: boolean): number => {
  const [dx, dy] = vector
  
  // ベクトルの角度（ラジアン）
  let angle = Math.atan2(dx, -dy) // Y軸が画像座標系では上向きが負のため
  
  // ラジアンから度に変換
  angle = angle * (180 / Math.PI)
  
  // forward_positive = false の場合（体幹角度）は符号を反転
  if (!forwardPositive) {
    angle = -angle
  }
  
  return angle
}

const calculateAbsoluteTrunkAngle = (keypoints: KeyPoint[]): number | null => {
  try {
    const leftShoulder = keypoints[LANDMARK_INDICES.left_shoulder]
    const rightShoulder = keypoints[LANDMARK_INDICES.right_shoulder]
    const leftHip = keypoints[LANDMARK_INDICES.left_hip]
    const rightHip = keypoints[LANDMARK_INDICES.right_hip]
    
    if (!leftShoulder || !rightShoulder || !leftHip || !rightHip ||
        leftShoulder.visibility < 0.5 || rightShoulder.visibility < 0.5 ||
        leftHip.visibility < 0.5 || rightHip.visibility < 0.5) {
      return null
    }

    const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2
    const shoulderCenterY = (leftShoulder.y + rightShoulder.y) / 2
    const hipCenterX = (leftHip.x + rightHip.x) / 2
    const hipCenterY = (leftHip.y + rightHip.y) / 2
    
    // 体幹ベクトル（股関節中点→肩中点）
    const trunkVector: [number, number] = [shoulderCenterX - hipCenterX, shoulderCenterY - hipCenterY]
    
    return calculateAbsoluteAngleWithVertical(trunkVector, false)
  } catch (error) {
    return null
  }
}

const calculateAbsoluteThighAngle = (hip: KeyPoint, knee: KeyPoint): number | null => {
  try {
    if (hip.visibility < 0.5 || knee.visibility < 0.5) {
      return null
    }
    
    // 大腿ベクトル（膝→股関節）
    const thighVector: [number, number] = [hip.x - knee.x, hip.y - knee.y]
    
    return calculateAbsoluteAngleWithVertical(thighVector, true)
  } catch (error) {
    return null
  }
}

const calculateAbsoluteLowerLegAngle = (knee: KeyPoint, ankle: KeyPoint): number | null => {
  try {
    if (knee.visibility < 0.5 || ankle.visibility < 0.5) {
      return null
    }
    
    // 下腿ベクトル（足首→膝）
    const lowerLegVector: [number, number] = [knee.x - ankle.x, knee.y - ankle.y]
    
    return calculateAbsoluteAngleWithVertical(lowerLegVector, true)
  } catch (error) {
    return null
  }
}

// データ型定義
interface KeyPoint {
  x: number
  y: number
  z: number
  visibility: number
}

interface FramePoseData {
  frame_number: number
  timestamp: number
  keypoints: KeyPoint[]
  landmarks_detected: boolean
  confidence_score?: number // オプショナルに変更
}

interface VideoInfo {
  fps: number
  total_frames: number
  duration_seconds: number
  width: number
  height: number
}

interface AngleGraphsCardProps {
  poseData: FramePoseData[]
  videoInfo: VideoInfo
}

interface AngleData {
  time: number
  frame: number
  trunk: number | null
  leftThigh: number | null
  rightThigh: number | null
  leftLowerLeg: number | null
  rightLowerLeg: number | null
}

interface LegAngleSelection {
  leftThigh: boolean
  rightThigh: boolean
  leftLowerLeg: boolean
  rightLowerLeg: boolean
}

// カスタムTooltipコンポーネント
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-300 rounded-lg shadow-lg">
        <p className="text-sm text-gray-600">{`時間: ${Number(label).toFixed(2)}秒`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${entry.value !== null ? `${Number(entry.value).toFixed(1)}°` : '未検出'}`}
          </p>
        ))}
      </div>
    )
  }
  return null
}

// チェックボックスコンポーネント
const AngleCheckbox = ({ 
  label, 
  checked, 
  onChange, 
  color 
}: { 
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  color: string
}) => (
  <label className="flex items-center space-x-2 cursor-pointer">
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
    />
    <div className="flex items-center space-x-1">
      <div 
        className="w-3 h-3 rounded-full" 
        style={{ backgroundColor: color }}
      />
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </div>
  </label>
)

export default function AngleGraphsCard({ poseData, videoInfo }: AngleGraphsCardProps) {
  // 下肢角度の表示設定
  const [legAngleSelection, setLegAngleSelection] = useState<LegAngleSelection>({
    leftThigh: true,
    rightThigh: true,
    leftLowerLeg: true,
    rightLowerLeg: true,
  })

  // データ前処理とメモ化
  const angleData = useMemo(() => {
    if (!poseData || poseData.length === 0) return []
    
    return poseData.map((frame) => {
      // keypointsから角度を計算
      const keypoints = frame.keypoints || []
      
      // 体幹角度を計算
      const trunkAngle = calculateAbsoluteTrunkAngle(keypoints)
      
      // 大腿角度を計算
      const leftHip = keypoints[LANDMARK_INDICES.left_hip]
      const rightHip = keypoints[LANDMARK_INDICES.right_hip]
      const leftKnee = keypoints[LANDMARK_INDICES.left_knee]
      const rightKnee = keypoints[LANDMARK_INDICES.right_knee]
      
      const leftThighAngle = (leftHip && leftKnee) ? calculateAbsoluteThighAngle(leftHip, leftKnee) : null
      const rightThighAngle = (rightHip && rightKnee) ? calculateAbsoluteThighAngle(rightHip, rightKnee) : null
      
      // 下腿角度を計算
      const leftAnkle = keypoints[LANDMARK_INDICES.left_ankle]
      const rightAnkle = keypoints[LANDMARK_INDICES.right_ankle]
      
      const leftLowerLegAngle = (leftKnee && leftAnkle) ? calculateAbsoluteLowerLegAngle(leftKnee, leftAnkle) : null
      const rightLowerLegAngle = (rightKnee && rightAnkle) ? calculateAbsoluteLowerLegAngle(rightKnee, rightAnkle) : null
      
      return {
        time: frame.timestamp || (frame.frame_number / videoInfo.fps),
        frame: frame.frame_number,
        trunk: trunkAngle,
        leftThigh: leftThighAngle,
        rightThigh: rightThighAngle,
        leftLowerLeg: leftLowerLegAngle,
        rightLowerLeg: rightLowerLegAngle,
      }
    })
  }, [poseData, videoInfo.fps])

  // 統計計算
  const statistics = useMemo(() => {
    const validTrunkAngles = angleData.filter(d => d.trunk !== null).map(d => d.trunk!)
    const validLeftThighAngles = angleData.filter(d => d.leftThigh !== null).map(d => d.leftThigh!)
    const validRightThighAngles = angleData.filter(d => d.rightThigh !== null).map(d => d.rightThigh!)
    const validLeftLowerLegAngles = angleData.filter(d => d.leftLowerLeg !== null).map(d => d.leftLowerLeg!)
    const validRightLowerLegAngles = angleData.filter(d => d.rightLowerLeg !== null).map(d => d.rightLowerLeg!)

    return {
      trunk: {
        mean: validTrunkAngles.length > 0 ? validTrunkAngles.reduce((a, b) => a + b, 0) / validTrunkAngles.length : 0,
        min: validTrunkAngles.length > 0 ? Math.min(...validTrunkAngles) : 0,
        max: validTrunkAngles.length > 0 ? Math.max(...validTrunkAngles) : 0,
      },
      leg: {
        leftThighMean: validLeftThighAngles.length > 0 ? validLeftThighAngles.reduce((a, b) => a + b, 0) / validLeftThighAngles.length : 0,
        rightThighMean: validRightThighAngles.length > 0 ? validRightThighAngles.reduce((a, b) => a + b, 0) / validRightThighAngles.length : 0,
        leftLowerLegMean: validLeftLowerLegAngles.length > 0 ? validLeftLowerLegAngles.reduce((a, b) => a + b, 0) / validLeftLowerLegAngles.length : 0,
        rightLowerLegMean: validRightLowerLegAngles.length > 0 ? validRightLowerLegAngles.reduce((a, b) => a + b, 0) / validRightLowerLegAngles.length : 0,
      }
    }
  }, [angleData])

  // チェックボックス更新ハンドラー
  const handleAngleSelectionChange = (angleType: keyof LegAngleSelection, checked: boolean) => {
    setLegAngleSelection(prev => ({
      ...prev,
      [angleType]: checked
    }))
  }

  // データが不足している場合
  if (!poseData || poseData.length === 0) {
    return (
      <Card className="shadow-lg mt-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            📈 角度推移分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <p>角度データが利用できません</p>
            <p className="text-sm mt-2">動画解析が完了していない可能性があります</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="shadow-lg mt-6">
      <CardHeader>
        <CardTitle className="flex items-center">
          <TrendingUp className="h-5 w-5 mr-2" />
          📈 角度推移分析
        </CardTitle>
        <p className="text-sm text-gray-600 mt-1">
          実際の動画データに基づく関節角度の時系列変化
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* 左側: 体幹角度グラフ */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-800">🏃‍♂️ 体幹角度推移</h3>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                平均: {statistics.trunk.mean.toFixed(1)}°
              </span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={angleData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="time" 
                  type="number"
                  scale="linear"
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => `${value.toFixed(1)}s`}
                  stroke="#666"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  tickFormatter={(value) => `${value}°`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line 
                  type="monotone" 
                  dataKey="trunk" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                  name="体幹角度"
                />
                {/* 基準線 */}
                <Line 
                  type="monotone" 
                  dataKey={() => 0} 
                  stroke="#94A3B8" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="基準線"
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
              <strong>符号規則:</strong> 前傾=負値, 後傾=正値 | 
              <strong>範囲:</strong> {statistics.trunk.min.toFixed(1)}° ～ {statistics.trunk.max.toFixed(1)}°
            </div>
          </div>

          {/* 右側: 下肢角度グラフ */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-semibold text-gray-800">🦵 下肢角度推移</h3>
              <Settings2 className="h-4 w-4 text-gray-500" />
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={angleData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="time" 
                  type="number"
                  scale="linear"
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => `${value.toFixed(1)}s`}
                  stroke="#666"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  tickFormatter={(value) => `${value}°`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ fontSize: '12px' }}
                  iconType="line"
                />
                
                {/* 条件付き Line コンポーネント */}
                {legAngleSelection.leftThigh && (
                  <Line 
                    type="monotone" 
                    dataKey="leftThigh" 
                    stroke="#8B5CF6" 
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                    name="左大腿"
                  />
                )}
                {legAngleSelection.rightThigh && (
                  <Line 
                    type="monotone" 
                    dataKey="rightThigh" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                    name="右大腿"
                  />
                )}
                {legAngleSelection.leftLowerLeg && (
                  <Line 
                    type="monotone" 
                    dataKey="leftLowerLeg" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                    name="左下腿"
                  />
                )}
                {legAngleSelection.rightLowerLeg && (
                  <Line 
                    type="monotone" 
                    dataKey="rightLowerLeg" 
                    stroke="#F59E0B" 
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                    name="右下腿"
                  />
                )}
                
                {/* 基準線 */}
                <Line 
                  type="monotone" 
                  dataKey={() => 0} 
                  stroke="#94A3B8" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="基準線"
                />
              </LineChart>
            </ResponsiveContainer>
            
            <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
              <strong>符号規則:</strong> 膝/足首が後方=正値, 前方=負値 | 
              <strong>平均:</strong> 左大腿{statistics.leg.leftThighMean.toFixed(1)}°, 右大腿{statistics.leg.rightThighMean.toFixed(1)}°, 
              左下腿{statistics.leg.leftLowerLegMean.toFixed(1)}°, 右下腿{statistics.leg.rightLowerLegMean.toFixed(1)}°
            </div>
            
            {/* チェックボックス群 - 符号規則の下に移動 */}
            <div className="flex flex-wrap gap-4 p-3 bg-gray-50 rounded-lg">
              <AngleCheckbox
                label="左大腿"
                checked={legAngleSelection.leftThigh}
                onChange={(checked) => handleAngleSelectionChange('leftThigh', checked)}
                color="#8B5CF6"
              />
              <AngleCheckbox
                label="右大腿"
                checked={legAngleSelection.rightThigh}
                onChange={(checked) => handleAngleSelectionChange('rightThigh', checked)}
                color="#3B82F6"
              />
              <AngleCheckbox
                label="左下腿"
                checked={legAngleSelection.leftLowerLeg}
                onChange={(checked) => handleAngleSelectionChange('leftLowerLeg', checked)}
                color="#10B981"
              />
              <AngleCheckbox
                label="右下腿"
                checked={legAngleSelection.rightLowerLeg}
                onChange={(checked) => handleAngleSelectionChange('rightLowerLeg', checked)}
                color="#F59E0B"
              />
            </div>
          </div>
        </div>

        {/* データ概要 */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-3 rounded-lg text-center">
            <div className="text-lg font-bold text-blue-700">{angleData.length}</div>
            <div className="text-xs text-blue-600">総フレーム数</div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg text-center">
            <div className="text-lg font-bold text-green-700">{videoInfo.fps}</div>
            <div className="text-xs text-green-600">FPS</div>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg text-center">
            <div className="text-lg font-bold text-purple-700">{videoInfo.duration_seconds.toFixed(1)}s</div>
            <div className="text-xs text-purple-600">動画時間</div>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg text-center">
            <div className="text-lg font-bold text-orange-700">
              {angleData.filter(d => d.trunk !== null).length}
            </div>
            <div className="text-xs text-orange-600">有効データ</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
