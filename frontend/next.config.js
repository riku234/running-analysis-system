/** @type {import('next').NextConfig} */
const nextConfig = {
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