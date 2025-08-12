'use client'

import { useState } from 'react'
import { Upload, Play, FileVideo, AlertCircle } from 'lucide-react'

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // 動画ファイルの検証
      if (file.type.startsWith('video/')) {
        setSelectedFile(file)
      } else {
        alert('動画ファイルを選択してください。')
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // FormDataオブジェクトを作成
      const formData = new FormData()
      formData.append('file', selectedFile)

      console.log('アップロード開始:', selectedFile.name)

      // 進捗シミュレーション
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // API Gateway経由でバックエンドのvideo_processing serviceにPOSTリクエスト
      const response = await fetch('/api/video/upload', {
        method: 'POST',
        body: formData,
      })

      // 進捗完了
      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: アップロードに失敗しました`
        
        try {
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json()
            errorMessage = errorData.detail || errorMessage
          } else {
            // JSONでない場合はテキストとして読み取る
            const errorText = await response.text()
            if (errorText) {
              errorMessage = `${errorMessage}\n詳細: ${errorText}`
            }
          }
        } catch (parseError) {
          // JSONパースに失敗した場合はデフォルトメッセージを使用
          console.warn('エラーレスポンスのパースに失敗:', parseError)
        }
        
        throw new Error(errorMessage)
      }

      const result = await response.json()
      console.log('アップロード成功:', result)

      // 結果データをlocalStorageに保存（結果ページで使用）
      localStorage.setItem(`analysis_result_${result.upload_info.file_id}`, JSON.stringify(result))

      // 成功メッセージを表示
      if (result.status === 'success' && result.pose_analysis) {
        alert(`解析完了！\nファイル: ${result.upload_info.original_filename}\n検出率: ${(result.pose_analysis.summary.detection_rate * 100).toFixed(1)}%`)
      } else {
        alert(`アップロード成功（骨格解析は部分的）\nファイル: ${result.upload_info.original_filename}\nエラー: ${result.error || 'N/A'}`)
      }
      
      // 結果ページへリダイレクト
      setTimeout(() => {
        window.location.href = `/result/${result.upload_info.file_id}`
      }, 1500)

    } catch (error) {
      console.error('アップロードエラー:', error)
      alert(`アップロードに失敗しました:\n${error instanceof Error ? error.message : 'Unknown error'}`)
      setUploadProgress(0)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* ヘッダーセクション */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          ランニング動画自動解析システム
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          あなたのランニング動画をアップロードして、AIによる詳細なフォーム分析と改善アドバイスを受け取りましょう
        </p>
        
        {/* 特徴の説明 */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="card text-center">
            <div className="text-primary-600 mb-4">
              <FileVideo className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold mb-2">骨格検出</h3>
            <p className="text-gray-600">
              最新のAI技術でランニングフォームの骨格を精密に検出
            </p>
          </div>
          <div className="card text-center">
            <div className="text-primary-600 mb-4">
              <Play className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold mb-2">特徴量解析</h3>
            <p className="text-gray-600">
              ストライド、ケイデンス、関節角度などを詳細に分析
            </p>
          </div>
          <div className="card text-center">
            <div className="text-primary-600 mb-4">
              <AlertCircle className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold mb-2">改善アドバイス</h3>
            <p className="text-gray-600">
              個人に最適化された具体的な改善提案とエクササイズ
            </p>
          </div>
        </div>
      </div>

      {/* アップロードセクション */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">動画をアップロード</h2>
        
        {/* ファイル選択エリア */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center mb-6">
          <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <div className="mb-4">
            <label htmlFor="video-upload" className="btn-primary cursor-pointer inline-block">
              動画ファイルを選択
            </label>
            <input
              id="video-upload"
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
          <p className="text-gray-500 mb-2">
            またはファイルをここにドラッグ&ドロップしてください
          </p>
          <p className="text-sm text-gray-400">
            対応形式: MP4, AVI, MOV (最大100MB)
          </p>
        </div>

        {/* 選択されたファイル情報 */}
        {selectedFile && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <FileVideo className="w-6 h-6 text-blue-600 mr-3" />
              <div className="flex-1">
                <p className="font-medium text-blue-900">{selectedFile.name}</p>
                <p className="text-sm text-blue-600">
                  サイズ: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>
        )}

        {/* アップロード進捗 */}
        {isUploading && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">アップロード中...</span>
              <span className="text-sm text-gray-500">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* アップロードボタン */}
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className={`w-full py-3 px-6 rounded-lg font-medium transition-colors duration-200 ${
            selectedFile && !isUploading
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isUploading ? '解析中...' : '解析を開始'}
        </button>
      </div>

      {/* 注意事項 */}
      <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-yellow-800 mb-2">ご利用時の注意</h3>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>• 横から撮影した動画が最も解析精度が高くなります</li>
          <li>• ランナーが画面中央に映っている動画をご使用ください</li>
          <li>• 10秒以上の動画を推奨します</li>
          <li>• 解析には2-3分程度かかる場合があります</li>
        </ul>
      </div>
    </div>
  )
} 