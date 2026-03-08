'use client'

interface StatCardProps {
  title: string
  value: number | string
  subtitle?: string
  color?: string
}

export default function StatCard({ title, value, subtitle, color = 'blue' }: StatCardProps) {
  const colors: Record<string, string> = {
    blue: 'border-blue-500 bg-blue-50',
    green: 'border-green-500 bg-green-50',
    red: 'border-red-500 bg-red-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    purple: 'border-purple-500 bg-purple-50',
    gray: 'border-gray-500 bg-gray-50',
  }

  return (
    <div className={`rounded-lg border-l-4 p-4 ${colors[color] || colors.blue}`}>
      <p className="text-sm font-medium text-gray-600">{title}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}
