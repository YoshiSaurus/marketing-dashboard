'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface CategoryData {
  content_category: string
  post_count: number
  total_likes: number
  total_comments: number
  total_shares: number
  avg_likes: number
  avg_comments: number
}

interface CategoryChartProps {
  data: CategoryData[]
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload) return null
  return (
    <div className="rounded-lg border border-dark-border bg-dark-card p-3 shadow-xl">
      <p className="mb-1 text-sm font-semibold text-gray-200">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  )
}

export default function CategoryChart({ data }: CategoryChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-card flex h-64 items-center justify-center text-gray-500">
        No category data yet
      </div>
    )
  }

  return (
    <div className="glass-card p-5">
      <h3 className="mb-4 text-lg font-semibold text-gray-100">Performance by Category</h3>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a45" />
          <XAxis dataKey="content_category" tick={{ fontSize: 11, fill: '#9090b0' }} />
          <YAxis tick={{ fill: '#9090b0' }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ color: '#9090b0', fontSize: 12 }} />
          <Bar dataKey="post_count" name="Posts" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          <Bar dataKey="total_likes" name="Likes" fill="#10b981" radius={[4, 4, 0, 0]} />
          <Bar dataKey="total_comments" name="Comments" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
