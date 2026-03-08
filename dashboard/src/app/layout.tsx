import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Foliox Marketing Dashboard',
  description: 'AI Marketing Lead Performance Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
