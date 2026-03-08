'use client'

import { useState } from 'react'

interface Post {
  id: number
  suggestion_id: string
  platform: string
  post_type: string
  content_category: string
  title: string
  content_preview: string
  url: string | null
  published_at: string
  likes: number
  comments: number
  shares: number
  impressions: number
  clicks: number
}

interface PostsTableProps {
  posts: Post[]
  onPreview?: (post: Post) => void
}

const platformBadge: Record<string, string> = {
  website: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  linkedin: 'bg-sky-500/20 text-sky-400 border border-sky-500/30',
  twitter: 'bg-gray-500/20 text-gray-300 border border-gray-500/30',
}

const categoryBadge: Record<string, string> = {
  ai_pricing: 'bg-purple-500/20 text-purple-400',
  fuel_distribution: 'bg-orange-500/20 text-orange-400',
  cx_innovation: 'bg-green-500/20 text-green-400',
  fleet_management: 'bg-yellow-500/20 text-yellow-400',
  supply_chain: 'bg-red-500/20 text-red-400',
  market_intelligence: 'bg-indigo-500/20 text-indigo-400',
  sustainability: 'bg-emerald-500/20 text-emerald-400',
  general: 'bg-slate-500/20 text-slate-400',
}

const platformIcon: Record<string, string> = {
  website: '\uD83C\uDF10',
  linkedin: '\uD83D\uDCBC',
  twitter: '\uD835\uDD4F',
}

export default function PostsTable({ posts, onPreview }: PostsTableProps) {
  if (!posts || posts.length === 0) {
    return (
      <div className="glass-card p-8 text-center text-gray-500">
        No published posts yet. Approve suggestions in Slack to see them here.
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-dark-border">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Platform</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Published</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Likes</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Comments</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Shares</th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-400">Impr.</th>
              {onPreview && <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400">Preview</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border/50">
            {posts.map((post) => (
              <tr key={post.id} className="transition-colors hover:bg-dark-card-hover">
                <td className="max-w-xs truncate px-4 py-3 text-sm font-medium text-gray-200">
                  {post.url ? (
                    <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 hover:underline">
                      {post.title || post.content_preview?.slice(0, 60) || post.suggestion_id}
                    </a>
                  ) : (
                    post.title || post.content_preview?.slice(0, 60) || post.suggestion_id
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${platformBadge[post.platform] || 'bg-gray-500/20 text-gray-400'}`}>
                    <span>{platformIcon[post.platform] || ''}</span>
                    {post.platform}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${categoryBadge[post.content_category] || categoryBadge.general}`}>
                    {post.content_category?.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-400">
                  {new Date(post.published_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right text-sm font-medium text-emerald-400">{post.likes}</td>
                <td className="px-4 py-3 text-right text-sm font-medium text-blue-400">{post.comments}</td>
                <td className="px-4 py-3 text-right text-sm font-medium text-purple-400">{post.shares}</td>
                <td className="px-4 py-3 text-right text-sm font-medium text-amber-400">{post.impressions}</td>
                {onPreview && (
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => onPreview(post)}
                      className="rounded-lg bg-dark-elevated px-3 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-dark-border hover:text-white"
                    >
                      Preview
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
