'use client'

import { useEffect, useState } from 'react'
import StatCard from '@/components/StatCard'
import PostsTable from '@/components/PostsTable'
import CategoryChart from '@/components/CategoryChart'
import SuggestionsTable from '@/components/SuggestionsTable'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

function useFetch<T>(path: string, fallback: T): { data: T; loading: boolean; error: string | null } {
  const [data, setData] = useState<T>(fallback)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}${path}`)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status}`)
        return res.json()
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [path])

  return { data, loading, error }
}

export default function Dashboard() {
  const { data: summary, loading: summaryLoading } = useFetch<any>('/api/dashboard', {})
  const { data: posts } = useFetch<any[]>('/api/posts?limit=20', [])
  const { data: categories } = useFetch<any[]>('/api/categories', [])
  const { data: suggestions } = useFetch<any[]>('/api/suggestions?limit=30', [])
  const { data: platforms } = useFetch<any[]>('/api/platforms', [])

  const [activeTab, setActiveTab] = useState<'overview' | 'posts' | 'suggestions'>('overview')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Foliox Marketing Dashboard</h1>
              <p className="text-sm text-gray-500">AI Marketing Lead Performance Tracker</p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex h-3 w-3 rounded-full ${summaryLoading ? 'bg-yellow-400' : 'bg-green-400'}`} />
              <span className="text-sm text-gray-500">{summaryLoading ? 'Loading...' : 'Connected'}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Summary Stats */}
        <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <StatCard title="Total Suggestions" value={summary.total_suggestions || 0} color="blue" />
          <StatCard title="Approved" value={summary.approved || 0} color="green" />
          <StatCard title="Rejected" value={summary.rejected || 0} color="red" />
          <StatCard title="Pending" value={summary.pending || 0} color="yellow" />
          <StatCard title="Published" value={summary.total_published || 0} color="purple" />
          <StatCard title="Scan Cycles" value={summary.total_scans || 0} color="gray" />
        </div>

        {/* Engagement Summary */}
        {summary.total_engagement && (
          <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-5">
            <StatCard title="Total Likes" value={summary.total_engagement.likes} color="green" />
            <StatCard title="Total Comments" value={summary.total_engagement.comments} color="blue" />
            <StatCard title="Total Shares" value={summary.total_engagement.shares} color="purple" />
            <StatCard title="Total Impressions" value={summary.total_engagement.impressions} color="yellow" />
            <StatCard title="Total Clicks" value={summary.total_engagement.clicks} color="red" />
          </div>
        )}

        {/* Platform Stats */}
        {platforms && platforms.length > 0 && (
          <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
            {platforms.map((p: any) => (
              <div key={p.platform} className="rounded-lg bg-white p-4 shadow">
                <h3 className="text-sm font-medium uppercase text-gray-500">{p.platform}</h3>
                <p className="mt-1 text-2xl font-bold">{p.count} posts</p>
                <p className="text-sm text-gray-500">{p.total_likes} likes / {p.total_comments} comments</p>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {(['overview', 'posts', 'suggestions'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`border-b-2 px-1 py-3 text-sm font-medium ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            <CategoryChart data={categories} />
          </div>
        )}

        {activeTab === 'posts' && <PostsTable posts={posts} />}

        {activeTab === 'suggestions' && <SuggestionsTable suggestions={suggestions} />}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t bg-white py-4 text-center text-sm text-gray-500">
        Foliox AI Marketing Lead &middot; Data refreshes every 60 seconds
      </footer>
    </div>
  )
}
