/** @type {import('next').NextConfig} */
const nextConfig = {
  // 開発・本番両対応の設定
  images: {
    unoptimized: true
  },
  
  // API プロキシ設定（本番では同じサーバー内なので localhost を使用）
  async rewrites() {
    // 本番環境（Docker Compose）では同じネットワーク内のサービス名を使用
    // 開発環境ではlocalhostを使用
    const apiBaseUrl = process.env.NODE_ENV === 'production' 
      ? 'http://api_gateway:80' 
      : 'http://127.0.0.1:80';
      
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ]
  },
  
  // より長いタイムアウト設定
  experimental: {
    proxyTimeout: 300000, // 5分
  },
}

module.exports = nextConfig 