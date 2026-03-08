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

export default function CategoryChart({ data }: CategoryChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg bg-white text-gray-500">
        No category data yet
      </div>
    )
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">Performance by Category</h3>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="content_category" tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="post_count" name="Posts" fill="#3b82f6" />
          <Bar dataKey="total_likes" name="Likes" fill="#10b981" />
          <Bar dataKey="total_comments" name="Comments" fill="#f59e0b" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
