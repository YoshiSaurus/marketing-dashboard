'use client'

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
}

const platformBadge: Record<string, string> = {
  website: 'bg-blue-100 text-blue-800',
  linkedin: 'bg-sky-100 text-sky-800',
  twitter: 'bg-gray-100 text-gray-800',
}

const categoryBadge: Record<string, string> = {
  ai_pricing: 'bg-purple-100 text-purple-800',
  fuel_distribution: 'bg-orange-100 text-orange-800',
  cx_innovation: 'bg-green-100 text-green-800',
  fleet_management: 'bg-yellow-100 text-yellow-800',
  supply_chain: 'bg-red-100 text-red-800',
  market_intelligence: 'bg-indigo-100 text-indigo-800',
  sustainability: 'bg-emerald-100 text-emerald-800',
  general: 'bg-gray-100 text-gray-800',
}

export default function PostsTable({ posts }: PostsTableProps) {
  if (!posts || posts.length === 0) {
    return (
      <div className="rounded-lg bg-white p-8 text-center text-gray-500">
        No published posts yet. Approve suggestions in Slack to see them here.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg bg-white shadow">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Title</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Platform</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Category</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Published</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Likes</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Comments</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Shares</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Impressions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {posts.map((post) => (
            <tr key={post.id} className="hover:bg-gray-50">
              <td className="max-w-xs truncate px-4 py-3 text-sm font-medium text-gray-900">
                {post.url ? (
                  <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {post.title || post.content_preview?.slice(0, 60) || post.suggestion_id}
                  </a>
                ) : (
                  post.title || post.content_preview?.slice(0, 60) || post.suggestion_id
                )}
              </td>
              <td className="px-4 py-3">
                <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${platformBadge[post.platform] || 'bg-gray-100'}`}>
                  {post.platform}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${categoryBadge[post.content_category] || categoryBadge.general}`}>
                  {post.content_category}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {new Date(post.published_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3 text-right text-sm font-medium">{post.likes}</td>
              <td className="px-4 py-3 text-right text-sm font-medium">{post.comments}</td>
              <td className="px-4 py-3 text-right text-sm font-medium">{post.shares}</td>
              <td className="px-4 py-3 text-right text-sm font-medium">{post.impressions}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
