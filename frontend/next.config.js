/** @type {import('next').NextConfig} */
const nextConfig = {
  // 開発・本番両対応の設定
  images: {
    unoptimized: true
  },
  
  // API プロキシ設定を復活（本番では外部URLに変更）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:80/api/:path*',
      },
    ]
  },
  
  // より長いタイムアウト設定
  experimental: {
    proxyTimeout: 300000, // 5分
  },
}

module.exports = nextConfig 