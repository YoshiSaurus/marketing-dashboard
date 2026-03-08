'use client'

import { useEffect, useState, useCallback } from 'react'
import StatCard from '@/components/StatCard'
import PostsTable from '@/components/PostsTable'
import CategoryChart from '@/components/CategoryChart'
import SuggestionsTable from '@/components/SuggestionsTable'
import ContentCalendar from '@/components/ContentCalendar'
import LinkedInPreview from '@/components/LinkedInPreview'
import TwitterPreview from '@/components/TwitterPreview'
import BlogPreview from '@/components/BlogPreview'

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

type Tab = 'calendar' | 'overview' | 'posts' | 'suggestions' | 'previews'

interface PreviewPost {
  id: number
  suggestion_id: string
  platform: string
  title: string
  content_preview: string
  published_at: string
  content_category: string
  likes: number
  comments: number
  shares: number
  impressions: number
  clicks: number
  url: string | null
  post_type: string
}

export default function Dashboard() {
  const { data: summary, loading: summaryLoading } = useFetch<any>('/api/dashboard', {})
  const { data: posts } = useFetch<any[]>('/api/posts?limit=50', [])
  const { data: categories } = useFetch<any[]>('/api/categories', [])
  const { data: suggestions } = useFetch<any[]>('/api/suggestions?limit=30', [])
  const { data: platforms } = useFetch<any[]>('/api/platforms', [])

  const [activeTab, setActiveTab] = useState<Tab>('calendar')
  const [previewPost, setPreviewPost] = useState<PreviewPost | null>(null)
  const [previewPlatform, setPreviewPlatform] = useState<string>('linkedin')

  const handleSelectPost = useCallback((post: PreviewPost) => {
    setPreviewPost(post)
    setPreviewPlatform(post.platform || 'linkedin')
    setActiveTab('previews')
  }, [])

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'calendar', label: 'Calendar', icon: '\uD83D\uDCC5' },
    { key: 'overview', label: 'Analytics', icon: '\uD83D\uDCCA' },
    { key: 'posts', label: 'Posts', icon: '\uD83D\uDCDD' },
    { key: 'suggestions', label: 'Pipeline', icon: '\u26A1' },
    { key: 'previews', label: 'Previews', icon: '\uD83D\uDC41' },
  ]

  return (
    <div className="min-h-screen bg-dark-primary">
      {/* Header */}
      <header className="border-b border-dark-border bg-dark-secondary/80 backdrop-blur-lg">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-bold text-white shadow-lg shadow-blue-500/20">
                F
              </div>
              <div>
                <h1 className="gradient-text text-xl font-extrabold tracking-tight">Marketing Command Center</h1>
                <p className="text-xs text-gray-500">AI Marketing Lead &middot; Content Calendar & Performance</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full bg-dark-card px-3 py-1.5">
                <span className={`inline-flex h-2.5 w-2.5 rounded-full ${summaryLoading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 pulse-live'}`} />
                <span className="text-xs font-medium text-gray-400">{summaryLoading ? 'Syncing...' : 'Live'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Summary Stats */}
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          <StatCard title="Suggestions" value={summary.total_suggestions || 0} color="blue" />
          <StatCard title="Approved" value={summary.approved || 0} color="green" />
          <StatCard title="Rejected" value={summary.rejected || 0} color="red" />
          <StatCard title="Pending" value={summary.pending || 0} color="yellow" />
          <StatCard title="Published" value={summary.total_published || 0} color="purple" />
          <StatCard title="Scans" value={summary.total_scans || 0} color="cyan" />
        </div>

        {/* Engagement Row */}
        {summary.total_engagement && (
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
            <StatCard title="Likes" value={summary.total_engagement.likes} color="green" />
            <StatCard title="Comments" value={summary.total_engagement.comments} color="blue" />
            <StatCard title="Shares" value={summary.total_engagement.shares} color="purple" />
            <StatCard title="Impressions" value={summary.total_engagement.impressions} color="yellow" />
            <StatCard title="Clicks" value={summary.total_engagement.clicks} color="red" />
          </div>
        )}

        {/* Platform Cards */}
        {platforms && platforms.length > 0 && (
          <div className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-3">
            {platforms.map((p: any) => (
              <div key={p.platform} className="glass-card glass-card-hover p-4 transition-all">
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {p.platform === 'linkedin' ? '\uD83D\uDCBC' : p.platform === 'twitter' ? '\uD835\uDD4F' : '\uD83C\uDF10'}
                  </span>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">{p.platform}</h3>
                </div>
                <p className="mt-2 text-2xl font-bold text-gray-100">{p.count} <span className="text-sm font-normal text-gray-500">posts</span></p>
                <div className="mt-1 flex gap-3 text-xs text-gray-500">
                  <span className="text-emerald-400">{p.total_likes} likes</span>
                  <span className="text-blue-400">{p.total_comments} comments</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 border-b border-dark-border">
          <nav className="-mb-px flex space-x-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-1.5 whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors
                  ${activeTab === tab.key
                    ? 'tab-active text-blue-400'
                    : 'text-gray-500 hover:text-gray-300'
                  }`}
              >
                <span className="text-base">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'calendar' && (
          <ContentCalendar posts={posts} onSelectPost={handleSelectPost} />
        )}

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <CategoryChart data={categories} />
          </div>
        )}

        {activeTab === 'posts' && (
          <PostsTable posts={posts} onPreview={handleSelectPost} />
        )}

        {activeTab === 'suggestions' && <SuggestionsTable suggestions={suggestions} />}

        {activeTab === 'previews' && (
          <div className="space-y-6">
            {/* Preview Platform Selector */}
            <div className="glass-card p-4">
              <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-gray-200">Post Preview</h3>
                  <p className="text-xs text-gray-500">See how your content looks on each platform</p>
                </div>
                <div className="flex gap-2">
                  {[
                    { key: 'linkedin', label: 'LinkedIn', icon: '\uD83D\uDCBC' },
                    { key: 'twitter', label: 'X / Twitter', icon: '\uD835\uDD4F' },
                    { key: 'website', label: 'Blog', icon: '\uD83C\uDF10' },
                  ].map((p) => (
                    <button
                      key={p.key}
                      onClick={() => setPreviewPlatform(p.key)}
                      className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-medium transition-all
                        ${previewPlatform === p.key
                          ? 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/40'
                          : 'bg-dark-elevated text-gray-400 hover:text-gray-200'
                        }`}
                    >
                      <span>{p.icon}</span>
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Post selector */}
              {posts.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {posts.slice(0, 10).map((post: any) => (
                    <button
                      key={post.id}
                      onClick={() => setPreviewPost(post)}
                      className={`max-w-[200px] truncate rounded-lg px-3 py-1.5 text-xs font-medium transition-all
                        ${previewPost?.id === post.id
                          ? 'bg-purple-500/20 text-purple-400 ring-1 ring-purple-500/40'
                          : 'bg-dark-elevated text-gray-400 hover:text-gray-200'
                        }`}
                    >
                      {post.title?.slice(0, 30) || post.suggestion_id}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Preview Render */}
            {previewPost ? (
              <div className="flex justify-center py-4">
                {previewPlatform === 'linkedin' && (
                  <LinkedInPreview
                    content={previewPost.content_preview || previewPost.title}
                    likes={previewPost.likes}
                    comments={previewPost.comments}
                    shares={previewPost.shares}
                  />
                )}
                {previewPlatform === 'twitter' && (
                  <TwitterPreview
                    content={previewPost.content_preview || previewPost.title}
                    likes={previewPost.likes}
                    comments={previewPost.comments}
                    shares={previewPost.shares}
                  />
                )}
                {previewPlatform === 'website' && (
                  <BlogPreview
                    title={previewPost.title || 'Untitled Post'}
                    content={previewPost.content_preview || ''}
                    category={previewPost.content_category}
                    publishedAt={previewPost.published_at}
                  />
                )}
              </div>
            ) : (
              <div className="glass-card flex h-64 flex-col items-center justify-center text-gray-500">
                <span className="mb-2 text-3xl opacity-50">{'\uD83D\uDC41'}</span>
                <p className="text-sm">Select a post above to preview it, or click &quot;Preview&quot; from the Posts or Calendar tab</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-dark-border bg-dark-secondary/50 py-4 text-center text-xs text-gray-600">
        Foliox AI Marketing Lead &middot; Data refreshes every 60s &middot; {new Date().getFullYear()}
      </footer>
    </div>
  )
}
