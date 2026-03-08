import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Foliox Marketing Command Center',
  description: 'AI Marketing Lead - Content Calendar & Performance Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-dark-primary text-gray-100 antialiased">{children}</body>
    </html>
  )
}
