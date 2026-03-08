'use client'

interface BlogPreviewProps {
  title: string
  content: string
  category?: string
  publishedAt?: string
  authorName?: string
  imageUrl?: string | null
}

export default function BlogPreview({
  title,
  content,
  category = 'Industry Insights',
  publishedAt,
  authorName = 'Foliox AI Team',
  imageUrl,
}: BlogPreviewProps) {
  const displayDate = publishedAt
    ? new Date(publishedAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : 'March 8, 2026'

  const readTime = Math.max(2, Math.ceil(content.split(' ').length / 200))

  return (
    <div className="preview-frame mx-auto max-w-[640px]">
      {/* Browser chrome */}
      <div className="flex items-center justify-between border-b border-dark-border bg-dark-card px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-red-500/60" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
          <div className="h-3 w-3 rounded-full bg-green-500/60" />
        </div>
        <div className="mx-4 flex-1 rounded-full bg-dark-elevated px-4 py-1 text-center text-[10px] text-gray-500">
          foliox.ai/blog/{title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40)}
        </div>
        <div className="w-12" />
      </div>

      {/* Site navbar */}
      <div className="flex items-center justify-between border-b border-[#1e1e2e] bg-[#0d0d15] px-6 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white">F</div>
          <span className="text-sm font-bold text-white">Foliox</span>
        </div>
        <div className="flex gap-6 text-xs text-gray-400">
          <span className="hover:text-white">Solutions</span>
          <span className="hover:text-white">Pricing</span>
          <span className="font-medium text-blue-400">Blog</span>
          <span className="hover:text-white">About</span>
        </div>
      </div>

      {/* Blog article */}
      <div className="bg-[#0d0d15] px-8 py-8">
        {/* Category & read time */}
        <div className="mb-4 flex items-center gap-3">
          <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs font-medium text-blue-400">
            {category.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-gray-500">{readTime} min read</span>
        </div>

        {/* Title */}
        <h1 className="mb-4 text-2xl font-bold leading-tight text-white">
          {title}
        </h1>

        {/* Author & date */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-xs font-bold text-white">
            {authorName.charAt(0)}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-200">{authorName}</p>
            <p className="text-xs text-gray-500">{displayDate}</p>
          </div>
        </div>

        {/* Hero image placeholder */}
        <div className="mb-6 aspect-[2/1] w-full overflow-hidden rounded-xl bg-gradient-to-br from-dark-card to-dark-elevated">
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mb-2 text-3xl opacity-30">{'\uD83D\uDCDD'}</div>
              <span className="text-xs text-gray-600">Featured Image</span>
            </div>
          </div>
        </div>

        {/* Content preview */}
        <div className="prose prose-invert max-w-none">
          <p className="text-sm leading-relaxed text-gray-300">
            {content.length > 500 ? content.slice(0, 500) + '...' : content}
          </p>
        </div>

        {/* Read more fade */}
        <div className="relative mt-4">
          <div className="h-16 bg-gradient-to-b from-transparent to-[#0d0d15]" />
          <div className="flex justify-center">
            <button className="rounded-full bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500">
              Continue Reading
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
