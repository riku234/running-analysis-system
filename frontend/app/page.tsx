'use client'

import { useState, useCallback } from 'react'
import { Upload, FileVideo, CheckCircle, Loader2, PlayCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleFile = (file: File) => {
    // 動画ファイルの検証
    if (file.type.startsWith('video/')) {
      setSelectedFile(file)
    } else {
      alert('動画ファイルを選択してください。')
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [])

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
    <div className="min-h-screen bg-gradient-running flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* ヘッダー */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight text-primary-gradient">
            ランニングフォーム自動解析
          </h1>
          <p className="text-xl text-muted-foreground max-w-lg mx-auto">
            動画ファイルをアップロードして、あなたの走り方を分析しましょう
          </p>
        </div>

        {/* メインカード */}
        <Card className="shadow-xl border-0">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-2xl">動画をアップロード</CardTitle>
            <CardDescription>
              AIが自動的にランニングフォームを解析し、改善点をアドバイスします
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* ドラッグ&ドロップエリア */}
            <div
              className={`
                relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 cursor-pointer
                ${isDragOver 
                  ? 'border-primary bg-primary/5 scale-105' 
                  : selectedFile 
                    ? 'border-green-500 bg-green-50' 
                    : 'border-muted-foreground/25 hover:border-primary hover:bg-primary/5'
                }
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('video-upload')?.click()}
            >
              <div className="space-y-4">
                {selectedFile ? (
                  <>
                    <CheckCircle className="h-16 w-16 text-green-500 mx-auto" />
                    <div>
                      <p className="text-lg font-medium text-green-700">
                        ファイルが選択されました
                      </p>
                      <p className="text-sm text-muted-foreground">
                        クリックして別のファイルを選択
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <Upload className={`h-16 w-16 mx-auto transition-colors ${isDragOver ? 'text-primary' : 'text-muted-foreground'}`} />
                    <div>
                      <p className="text-lg font-medium">
                        ここにファイルをドラッグ&ドロップ
                      </p>
                      <p className="text-sm text-muted-foreground">
                        またはクリックして選択
                      </p>
                    </div>
                  </>
                )}
              </div>
              
              <input
                id="video-upload"
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>

            {/* 選択されたファイル情報 */}
            {selectedFile && (
              <Card className="bg-green-50 border-green-200">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <FileVideo className="h-8 w-8 text-green-600 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-green-900 truncate">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-green-600">
                        サイズ: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* アップロード進捗 */}
            {isUploading && (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">解析中...</span>
                  <span className="text-sm text-muted-foreground">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* アップロードボタン */}
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              className="w-full h-12 text-base"
              size="lg"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  解析中...
                </>
              ) : (
                <>
                  <PlayCircle className="h-5 w-5 mr-2" />
                  解析を開始する
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* サポート情報 */}
        <Card className="bg-amber-50 border-amber-200">
          <CardHeader>
            <CardTitle className="text-lg text-amber-800">ご利用時の注意</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-amber-700">
            <div className="grid md:grid-cols-2 gap-2">
              <p>• 横から撮影した動画が最適</p>
              <p>• ランナーが画面中央に映っている</p>
              <p>• 10秒以上の動画を推奨</p>
              <p>• 対応形式: MP4, AVI, MOV</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 