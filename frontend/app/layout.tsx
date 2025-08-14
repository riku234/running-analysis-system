import './globals.css'
import { Toaster } from '@/components/ui/toaster'

export const metadata = {
  title: 'ランニングフォーム自動解析',
  description: 'AIがランニングフォームを自動解析し、改善アドバイスを提供するシステム',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
} 