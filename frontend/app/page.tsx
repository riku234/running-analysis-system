'use client'

import { useState, useCallback } from 'react'
import { Upload, FileVideo, CheckCircle, Loader2, PlayCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useResultStore } from '@/lib/store'
import { useToast } from '@/hooks/use-toast'

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  
  // Zustandストアのアクション
  const { setPoseData, setVideoInfo, setUploadInfo, clearData } = useResultStore()
  
  // Toast通知用フック
  const { toast } = useToast()

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
      toast({
        title: "ファイル選択完了",
        description: `${file.name} を選択しました`,
      })
    } else {
      toast({
        title: "ファイル形式エラー",
        description: "動画ファイル（MP4, AVI, MOV など）を選択してください。",
        variant: "destructive",
      })
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
    if (!selectedFile) {
      toast({
        title: "ファイル未選択",
        description: "動画ファイルを選択してから解析を開始してください。",
        variant: "destructive",
      })
      return
    }

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
      // タイムアウト設定（5分）
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5分
      
      const response = await fetch('/api/video/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)

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
      
      // ★★★ デバッグ: レスポンス構造を確認 & localStorage保存 ★★★
      const debugInfo = {
        timestamp: new Date().toISOString(),
        availableKeys: Object.keys(result),
        pose_analysis_pose_data_length: result.pose_analysis?.pose_data?.length || 0,
        pose_data_pose_data_length: result.pose_data?.pose_data?.length || 0,
        pose_analysis_keys: result.pose_analysis ? Object.keys(result.pose_analysis) : [],
        pose_data_keys: result.pose_data ? Object.keys(result.pose_data) : [],
        // サンプルデータ（最初の2フレームのみ）
        pose_analysis_sample: result.pose_analysis?.pose_data ? result.pose_analysis.pose_data.slice(0, 2) : null,
        pose_data_sample: result.pose_data?.pose_data ? result.pose_data.pose_data.slice(0, 2) : null,
        video_info: result.pose_analysis?.video_info || result.video_info,
        has_pose_analysis: !!result.pose_analysis,
        has_pose_data: !!result.pose_data
      }
      
      // localStorageに保存（軽量版）
      try {
        localStorage.setItem('lastUploadDebug', JSON.stringify(debugInfo, null, 2))
      } catch (storageError) {
        console.log("📤 ストレージエラー - さらに軽量化します:", storageError)
        // 更に軽量化
        const minimalDebugInfo = {
          timestamp: debugInfo.timestamp,
          availableKeys: debugInfo.availableKeys,
          pose_analysis_pose_data_length: debugInfo.pose_analysis_pose_data_length,
          pose_data_pose_data_length: debugInfo.pose_data_pose_data_length,
          has_pose_analysis: debugInfo.has_pose_analysis,
          has_pose_data: debugInfo.has_pose_data
        }
        localStorage.setItem('lastUploadDebug', JSON.stringify(minimalDebugInfo))
      }
      
      console.log("📤 バックエンドレスポンス構造調査:")
      console.log("📤 利用可能なキー:", debugInfo.availableKeys)
      console.log("📤 pose_analysis有無:", debugInfo.has_pose_analysis)
      console.log("📤 pose_data有無:", debugInfo.has_pose_data)
      console.log("📤 pose_analysis.pose_data フレーム数:", debugInfo.pose_analysis_pose_data_length)
      console.log("📤 pose_data.pose_data フレーム数:", debugInfo.pose_data_pose_data_length)
      console.log("📤 pose_analysis キー:", debugInfo.pose_analysis_keys)
      console.log("📤 pose_data キー:", debugInfo.pose_data_keys)
      console.log("📤 デバッグ情報をlocalStorageに保存しました！")
      // ★★★ デバッグここまで ★★★

      // 巨大なpose_dataはZustandストアに保存
      console.log("💾 Zustand保存チェック開始")
      console.log("💾 result.pose_analysis?.pose_data:", !!result.pose_analysis?.pose_data, result.pose_analysis?.pose_data?.length)
      console.log("💾 result.pose_data?.pose_data:", !!result.pose_data?.pose_data, result.pose_data?.pose_data?.length)
      
      let zustandSaveLog = ""
      if (result.pose_analysis?.pose_data && result.pose_analysis.pose_data.length > 0) {
        zustandSaveLog = `💾 Zustandに保存: pose_analysis.pose_data ${result.pose_analysis.pose_data.length}`
        console.log(zustandSaveLog)
        setPoseData(result.pose_analysis.pose_data)
      } else if (result.pose_data?.pose_data && result.pose_data.pose_data.length > 0) {
        zustandSaveLog = `💾 Zustandに保存: pose_data.pose_data ${result.pose_data.pose_data.length}`
        console.log(zustandSaveLog)
        setPoseData(result.pose_data.pose_data)
      } else {
        zustandSaveLog = "⚠️ pose_dataが見つかりません - Zustandに保存されませんでした"
        console.warn(zustandSaveLog)
        console.warn("⚠️ デバッグ:", {
          pose_analysis_exists: !!result.pose_analysis,
          pose_analysis_pose_data_exists: !!result.pose_analysis?.pose_data,
          pose_analysis_pose_data_length: result.pose_analysis?.pose_data?.length,
          pose_data_exists: !!result.pose_data,
          pose_data_pose_data_exists: !!result.pose_data?.pose_data,
          pose_data_pose_data_length: result.pose_data?.pose_data?.length
        })
      }
      
      // Zustand保存ログをlocalStorageに保存
      localStorage.setItem('lastZustandSaveLog', zustandSaveLog)
      if (result.pose_analysis?.video_info) {
        setVideoInfo(result.pose_analysis.video_info)
      }
      if (result.upload_info) {
        setUploadInfo(result.upload_info)
      }

      // 軽量なデータのみをlocalStorageに保存
      const lightWeightResult = {
        status: result.status,
        message: result.message,
        upload_info: result.upload_info,
        pose_analysis: {
          status: result.pose_analysis?.status,
          message: result.pose_analysis?.message,
          video_info: result.pose_analysis?.video_info,
          summary: result.pose_analysis?.summary,
          // pose_dataは除外（Zustandに保存済み）
        },
        feature_analysis: result.feature_analysis, // 特徴量データは軽量なので保存
        issue_analysis: result.issue_analysis, // 課題分析結果も軽量なので保存
        error: result.error
      }
      
      localStorage.setItem(`light_analysis_result_${result.upload_info.file_id}`, JSON.stringify(lightWeightResult))

      // 成功メッセージを表示
      if (result.status === 'success') {
        toast({
          title: "解析完了！",
          description: `${result.upload_info.original_filename} の解析が完了しました。結果ページに移動します。`,
        })
      } else {
        toast({
          title: "部分的な成功",
          description: `アップロードは成功しましたが、一部の解析でエラーが発生しました。`,
          variant: "destructive",
        })
      }
      
      // 結果ページへリダイレクト
      setTimeout(() => {
        window.location.href = `/result/${result.upload_info.file_id}`
      }, 1500)

    } catch (error) {
      console.error('アップロードエラー:', error)
      
      let errorTitle = '解析に失敗しました'
      let errorDescription = '不明なエラーが発生しました。時間をおいて再度お試しください。'
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorTitle = 'タイムアウト'
          errorDescription = 'アップロードがタイムアウトしました。ファイルサイズが大きい場合は時間がかかることがあります。'
        } else {
          errorDescription = error.message
        }
      }
      
      toast({
        title: errorTitle,
        description: errorDescription,
        variant: "destructive",
      })
      
      setUploadProgress(0)
    } finally {
      // ★ 必ず実行される処理：ボタンを再度有効化
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