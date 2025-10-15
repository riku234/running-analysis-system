'use client'

import { useState, useCallback } from 'react'
import { Upload, FileVideo, CheckCircle, Loader2, PlayCircle } from 'lucide-react'
import { useResultStore } from '@/lib/store'
import { useToast } from '@/hooks/use-toast'

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedUser, setSelectedUser] = useState<string>('vf_yaji') // ユーザー選択
  
  // ユーザーリスト
  const users = [
    { id: 'vf_yaji', name: 'VF矢治' },
    { id: 'vf_ono', name: 'VF大野' },
    { id: 'vf_hirokawa', name: 'VF広川' },
    { id: 'vf_fukui', name: 'VF福井' },
    { id: 'x_ae', name: 'X阿江' },
    { id: 'x_masuda', name: 'X増田' },
    { id: 'x_komatsu', name: 'X小松' },
    { id: 'x_suzuki', name: 'X鈴木' },
    { id: 'x_konno', name: 'X近野' },
    { id: 'guest1', name: 'ゲスト1' },
    { id: 'guest2', name: 'ゲスト2' },
    { id: 'guest3', name: 'ゲスト3' },
    { id: 'guest4', name: 'ゲスト4' },
    { id: 'guest5', name: 'ゲスト5' },
  ]
  
  // プロンプト設定の取得
  const getPromptSettings = () => {
    console.log('🔧 getPromptSettings 関数開始')
    
    // カスタムプロンプトを取得
    const customPromptElement = document.getElementById('custom-prompt') as HTMLTextAreaElement
    const customPrompt = customPromptElement?.value?.trim()
    
    const temperature = parseFloat((document.getElementById('temperature') as HTMLInputElement)?.value || '0.5')
    const topP = parseFloat((document.getElementById('top-p') as HTMLInputElement)?.value || '0.8')
    const maxTokens = parseInt((document.getElementById('max-tokens') as HTMLInputElement)?.value || '1000')
    
    // カスタムプロンプトが入力されている場合は使用、なければデフォルト
    const settings = {
      custom_prompt: customPrompt || undefined,
      use_custom_prompt: !!customPrompt,
      temperature: temperature,
      top_p: topP,
      max_output_tokens: maxTokens
    }
    console.log('🔧 プロンプト設定:', settings)
    return settings
  }
  
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
      formData.append('user_id', selectedUser) // ユーザーIDを追加
      
      // プロンプト設定を取得して送信
      try {
        console.log('🔍 プロンプト設定取得開始...')
        const promptSettings = getPromptSettings()
        console.log('✅ プロンプト設定取得成功:', promptSettings)
        
        if (promptSettings) {
          const jsonString = JSON.stringify(promptSettings)
          formData.append('prompt_settings', jsonString)
          console.log('📋 プロンプト設定を適用:', promptSettings)
          console.log('📝 JSON文字列:', jsonString)
          console.log('📝 JSON文字列長:', jsonString.length)
          console.log('📤 FormData内容確認:', Array.from(formData.entries()))
          console.log('📤 FormDataにprompSettingsが含まれているか:', formData.has('prompt_settings'))
        } else {
          console.warn('⚠️ プロンプト設定がnullまたはundefined')
        }
      } catch (error) {
        console.error('❌ プロンプト設定の取得に失敗:', error)
        console.error('❌ エラー詳細:', error.stack)
      }

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
        // アドバイスデータのチェック追加
        has_advice_results: !!result.advice_results,
        has_advice_analysis: !!result.advice_analysis,
        advice_results_keys: result.advice_results ? Object.keys(result.advice_results) : [],
        advice_analysis_keys: result.advice_analysis ? Object.keys(result.advice_analysis) : [],
        has_integrated_advice: !!(result.advice_results?.integrated_advice || result.advice_analysis?.integrated_advice),
        integrated_advice_length: (result.advice_results?.integrated_advice || result.advice_analysis?.integrated_advice)?.length || 0,
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
      console.log("📤 ===== アドバイスデータチェック =====")
      console.log("📤 advice_results有無:", debugInfo.has_advice_results)
      console.log("📤 advice_analysis有無:", debugInfo.has_advice_analysis)
      console.log("📤 integrated_advice有無:", debugInfo.has_integrated_advice)
      console.log("📤 integrated_advice長:", debugInfo.integrated_advice_length)
      console.log("📤 advice_results キー:", debugInfo.advice_results_keys)
      console.log("📤 advice_analysis キー:", debugInfo.advice_analysis_keys)
      
      // アップロード直後のアドバイスデータ詳細ログ
      if (result.advice_results) {
        console.log("🎯 アップロード直後のadvice_results詳細:", result.advice_results);
        console.log("🎯 integrated_advice内容:", result.advice_results.integrated_advice);
      }
      if (result.advice_analysis) {
        console.log("🎯 アップロード直後のadvice_analysis詳細:", result.advice_analysis);
        console.log("🎯 integrated_advice内容:", result.advice_analysis.integrated_advice);
      }
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


      // 軽量なデータのみをlocalStorageに保存（詳細ログ除外）
      const lightWeightResult = {
        status: result.status,
        message: result.message,
        upload_info: result.upload_info,
        pose_analysis: {
          status: result.pose_analysis?.status,
          message: result.pose_analysis?.message,
          video_info: result.pose_analysis?.video_info,
          summary: result.pose_analysis?.summary,
          // pose_dataも保存（Z値分析で必要）
          pose_data: result.pose_analysis?.pose_data || []
        },
        feature_analysis: {
          status: result.feature_analysis?.status,
          message: result.feature_analysis?.message,
          // 新しいangle_statisticsと従来データの両方を保存
          features: result.feature_analysis?.features ? {
            // 新仕様の絶対角度データ
            angle_statistics: result.feature_analysis.features.angle_statistics,
            // 新仕様のランニングメトリクス
            running_metrics: result.feature_analysis.features.running_metrics,
            // 従来データ（後方互換性のため）
            trunk_angle: result.feature_analysis.features.trunk_angle,
            left_thigh_angle: result.feature_analysis.features.left_thigh_angle,
            right_thigh_angle: result.feature_analysis.features.right_thigh_angle,
            left_lower_leg_angle: result.feature_analysis.features.left_lower_leg_angle,
            right_lower_leg_angle: result.feature_analysis.features.right_lower_leg_angle,
            vertical_oscillation: result.feature_analysis.features.vertical_oscillation,
            cadence: result.feature_analysis.features.cadence
          } : null
        },
        z_score_analysis: result.z_score_analysis,  // Z値分析結果を追加
        issue_analysis: result.issue_analysis, // 課題分析結果も軽量なので保存
        advice_results: result.advice_results, // ★ アドバイス結果を追加
        advice_analysis: result.advice_analysis, // ★ 後方互換性のため
        error: result.error
      }
      
      // localStorage保存時のエラーハンドリング
      try {
        // localStorage保存前のアドバイスデータ確認
        console.log("💾 localStorage保存前確認:");
        console.log("💾 lightWeightResult.advice_results:", !!lightWeightResult.advice_results);
        console.log("💾 lightWeightResult.advice_analysis:", !!lightWeightResult.advice_analysis);
        if (lightWeightResult.advice_results) {
          console.log("💾 advice_results詳細:", lightWeightResult.advice_results);
        }
        if (lightWeightResult.advice_analysis) {
          console.log("💾 advice_analysis詳細:", lightWeightResult.advice_analysis);
        }
        
        const jsonString = JSON.stringify(lightWeightResult)
        const sizeInMB = new Blob([jsonString]).size / 1024 / 1024
        
        console.log("💾 localStorage保存サイズ:", `${sizeInMB.toFixed(2)}MB`);
        
        if (sizeInMB > 4) { // 4MB制限
          console.warn(`結果データが大きすぎます: ${sizeInMB.toFixed(2)}MB`)
          // 最小限の結果のみ保存
          const minimalResult = {
            status: result.status,
            message: result.message,
            upload_info: result.upload_info,
        feature_analysis: {
          features: result.feature_analysis?.features ? {
            trunk_angle: result.feature_analysis.features.trunk_angle,
            vertical_oscillation: result.feature_analysis.features.vertical_oscillation,
            cadence: result.feature_analysis.features.cadence,
            angle_statistics: result.feature_analysis.features.angle_statistics // 角度推移グラフ用データを追加
          } : null
        },
            z_score_analysis: result.z_score_analysis,  // Z値分析結果を追加
            advice_results: result.advice_results,  // アドバイス結果を追加
            error: result.error
          }
          localStorage.setItem(`light_analysis_result_${result.upload_info.file_id}`, JSON.stringify(minimalResult))
        } else {
          localStorage.setItem(`light_analysis_result_${result.upload_info.file_id}`, jsonString)
          
          // 保存後の確認
          const savedData = localStorage.getItem(`light_analysis_result_${result.upload_info.file_id}`)
          if (savedData) {
            const parsedSaved = JSON.parse(savedData)
            console.log("✅ localStorage保存後確認:");
            console.log("✅ 保存されたz_score_analysis:", !!parsedSaved.z_score_analysis);
            console.log("✅ 保存されたadvice_results:", !!parsedSaved.advice_results);
            console.log("✅ 保存されたadvice_analysis:", !!parsedSaved.advice_analysis);
            if (parsedSaved.z_score_analysis) {
              console.log("✅ z_score_analysis有効偏差数:", Object.keys(parsedSaved.z_score_analysis.analysis_summary?.significant_deviations || {}).length);
            }
            if (parsedSaved.advice_results?.integrated_advice) {
              console.log("✅ integrated_advice長:", parsedSaved.advice_results.integrated_advice.length, "文字");
            }
            if (parsedSaved.advice_analysis?.integrated_advice) {
              console.log("✅ integrated_advice長:", parsedSaved.advice_analysis.integrated_advice.length, "文字");
            }
          }
        }
        
        console.log(`結果をlocalStorageに保存しました: ${sizeInMB.toFixed(2)}MB`)
      } catch (storageError) {
        console.error('localStorage保存エラー:', storageError)
        // localStorage保存に失敗してもZustandには保存されているので処理続行
        toast({
          title: "保存警告",
          description: "結果の一部保存に失敗しましたが、解析は正常に完了しました。",
          variant: "default"
        })
      }

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
    <div className="min-h-screen bg-gray-100">
      {/* Spir風ヘッダー */}
      <header className="bg-white shadow-md border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-md flex items-center justify-center">
                <PlayCircle className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-gray-900">RunAnalyzer</span>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-600 hover:text-gray-900 text-sm font-medium">機能</a>
              <a href="#" className="text-gray-600 hover:text-gray-900 text-sm font-medium">料金</a>
              <a href="#" className="text-gray-600 hover:text-gray-900 text-sm font-medium">サポート</a>
            </nav>
          </div>
        </div>
      </header>

      {/* ヒーローセクション */}
      <section className="bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              ランニングフォームを
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600"> AI解析</span>
            </h1>
            <p className="text-xl text-gray-600 mb-6 leading-relaxed">
              動画をアップロードするだけで、AIがあなたのランニングフォームを詳細に分析し、<br />
              パフォーマンス向上のための具体的なアドバイスを提供します
            </p>
          </div>
        </div>
      </section>

      {/* アップロードセクション */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
            <div className="p-8 sm:p-12">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  動画をアップロードして開始
                </h2>
                <p className="text-gray-600">
                  数分で詳細な解析結果とアドバイスをお届けします
                </p>
              </div>

              {/* ユーザー選択 */}
              <div className="mb-6">
                <label htmlFor="user-select" className="block text-sm font-medium text-gray-700 mb-2">
                  ユーザー選択
                </label>
                <select
                  id="user-select"
                  value={selectedUser}
                  onChange={(e) => setSelectedUser(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white text-gray-900"
                >
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* アップロードエリア */}
              <div
                className={`
                  relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer
                  ${isDragOver 
                    ? 'border-blue-400 bg-blue-50 scale-[1.02]' 
                    : selectedFile 
                      ? 'border-emerald-400 bg-emerald-50' 
                      : 'border-gray-400 hover:border-blue-500 hover:bg-gray-50'
                  }
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('video-upload')?.click()}
              >
                {selectedFile ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                      <CheckCircle className="h-8 w-8 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-gray-900 mb-1">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
                      <Upload className="h-8 w-8 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-gray-900 mb-2">
                        動画ファイルをドロップ
                      </p>
                      <p className="text-sm text-gray-500">
                        またはクリックして選択してください
                      </p>
                    </div>
                  </div>
                )}

                <input
                  id="video-upload"
                  type="file"
                  accept="video/*"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer pointer-events-none"
                />
              </div>

              {/* 進捗バー */}
              {isUploading && (
                <div className="mt-8 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">解析処理中...</span>
                    <span className="text-sm font-medium text-blue-600">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* アップロードボタン */}
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="w-full mt-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3 shadow-lg hover:shadow-xl"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>解析中...</span>
                  </>
                ) : (
                  <>
                    <PlayCircle className="h-5 w-5" />
                    <span>解析を開始する</span>
                  </>
                )}
              </button>

              {/* 対応形式 */}
              <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm text-gray-500">
                <span className="bg-gray-100 px-3 py-1 rounded-full">MP4</span>
                <span className="bg-gray-100 px-3 py-1 rounded-full">AVI</span>
                <span className="bg-gray-100 px-3 py-1 rounded-full">MOV</span>
                <span className="bg-gray-100 px-3 py-1 rounded-full">最大100MB</span>
              </div>
            </div>
          </div>

          {/* プロンプト設定セクション */}
          <div className="mt-12">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
              <div className="p-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-2">
                    🎯 AIアドバイス設定
                  </h2>
                  <p className="text-gray-600 text-sm">
                    あなたに最適なコーチングスタイルを選択してください
                  </p>
                </div>

              {/* プロンプト設定 */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    カスタムプロンプト（個別課題解説用）
                  </label>
                  <p className="text-sm text-gray-600 mb-2">
                    💡 デフォルトプロンプトが入力されています。必要に応じて編集してください。空欄にするとデフォルトが使用されます。
                  </p>
                  <textarea
                    id="custom-prompt"
                    rows={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none font-mono text-sm"
                    defaultValue={`あなたは専門コーチです。「{issue}」について、プレーンテキストのみで説明してください。

重要：装飾記号は一切使用禁止です。通常の文章のみで回答してください。

説明: {issue}がランニング効率に与える影響を80文字程度で説明してください。

エクササイズ: {issue}を改善する具体的な練習方法を60文字程度で提案してください。

形式例：
説明: 下腿角度が大きいと接地時にブレーキがかかり、推進力が減少してエネルギー効率が悪化します。
エクササイズ: 壁ドリルで足の引き上げを練習し、重心の真下で着地する感覚を習得しましょう。

このような通常の文章形式で回答してください。ハッシュ、アスタリスク、ハイフンなどの記号は絶対に使わないでください。`}
                  />
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Temperature (創造性)
                    </label>
                    <input
                      type="range"
                      id="temperature"
                      min="0"
                      max="1"
                      step="0.1"
                      defaultValue="0.5"
                      className="w-full"
                    />
                    <span className="text-xs text-gray-500">0.0 (保守的) - 1.0 (創造的)</span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Top P (多様性)
                    </label>
                    <input
                      type="range"
                      id="top-p"
                      min="0"
                      max="1"
                      step="0.1"
                      defaultValue="0.8"
                      className="w-full"
                    />
                    <span className="text-xs text-gray-500">0.0 (一貫性) - 1.0 (多様性)</span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      最大トークン数
                    </label>
                    <input
                      type="number"
                      id="max-tokens"
                      min="100"
                      max="2000"
                      step="100"
                      defaultValue="1000"
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                </div>

                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800 font-medium mb-1">
                    📝 プロンプト設定の適用範囲
                  </p>
                  <p className="text-xs text-blue-700">
                    カスタムプロンプトを入力すると「個別課題の詳細解説」の生成に適用されます。空欄の場合はデフォルトプロンプトが使用されます。
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {"{issue}"}の部分には各課題名（例: 体幹前傾、左下腿角度大）が自動的に挿入されます。
                  </p>
                </div>
              </div>
              </div>
            </div>
          </div>

          {/* 推奨事項 */}
          <div className="mt-12 grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileVideo className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900">最適な撮影方法</h3>
              </div>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• 横からの撮影（側面ビュー）</li>
                <li>• ランナーが画面中央に位置</li>
                <li>• 10秒以上の動画を推奨</li>
                <li>• 明るく安定した環境での撮影</li>
              </ul>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-md border border-gray-200">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-gray-900">解析内容</h3>
              </div>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• ランニングフォーム分析</li>
                <li>• 姿勢と動作の評価</li>
                <li>• 改善点の具体的なアドバイス</li>
                <li>• パフォーマンス向上提案</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}