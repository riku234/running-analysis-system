/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://api_gateway:80/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig 