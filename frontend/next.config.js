/** @type {import('next').NextConfig} */
const nextConfig = {
  // 開発・本番両対応の設定
  images: {
    unoptimized: true
  },
  
  // API プロキシ設定（Docker Compose内のサービスに直接ルーティング）
  async rewrites() {
    const isProd = process.env.NODE_ENV === 'production'
    
    return [
      // feature_extraction サービス（標準モデルキーポイント等）
      {
        source: '/api/feature_extraction/:path*',
        destination: isProd 
          ? 'http://feature_extraction:8003/:path*'
          : 'http://127.0.0.1:8003/:path*',
      },
      // video_processing サービス
      {
        source: '/api/video/:path*',
        destination: isProd
          ? 'http://video_processing:8001/:path*'
          : 'http://127.0.0.1:8001/:path*',
      },
      {
        source: '/api/video_processing/:path*',
        destination: isProd
          ? 'http://video_processing:8001/:path*'
          : 'http://127.0.0.1:8001/:path*',
      },
      // analysis サービス
      {
        source: '/api/analysis/:path*',
        destination: isProd
          ? 'http://analysis:8004/:path*'
          : 'http://127.0.0.1:8004/:path*',
      },
      // その他のAPIは API Gateway 経由
      {
        source: '/api/:path*',
        destination: isProd
          ? 'http://api_gateway:80/api/:path*'
          : 'http://127.0.0.1:80/api/:path*',
      },
    ]
  },
  
  // より長いタイムアウト設定
  experimental: {
    proxyTimeout: 300000, // 5分
  },
}

module.exports = nextConfig 