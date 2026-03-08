'use client'

interface LinkedInPreviewProps {
  authorName?: string
  authorTitle?: string
  content: string
  hashtags?: string
  likes?: number
  comments?: number
  shares?: number
  imageUrl?: string | null
}

export default function LinkedInPreview({
  authorName = 'Foliox AI',
  authorTitle = 'AI-Powered Fuel Distribution & Customer Intelligence',
  content,
  hashtags,
  likes = 0,
  comments = 0,
  shares = 0,
  imageUrl,
}: LinkedInPreviewProps) {
  const displayContent = content.length > 300 ? content.slice(0, 300) + '...' : content

  return (
    <div className="preview-frame mx-auto max-w-[520px]">
      {/* LinkedIn header bar */}
      <div className="flex items-center justify-between border-b border-dark-border bg-dark-card px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-red-500/60" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
          <div className="h-3 w-3 rounded-full bg-green-500/60" />
        </div>
        <div className="flex items-center gap-1.5">
          <svg className="h-4 w-4 text-[#0a66c2]" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
          </svg>
          <span className="text-xs font-semibold text-[#0a66c2]">LinkedIn</span>
        </div>
      </div>

      {/* Post card */}
      <div className="bg-[#1b1f23] p-4">
        {/* Author info */}
        <div className="mb-3 flex items-start gap-3">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-lg font-bold text-white">
            F
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-[#e8e8e8]">{authorName}</p>
            <p className="text-xs text-[#a0a0a0]">{authorTitle}</p>
            <div className="mt-0.5 flex items-center gap-1 text-xs text-[#a0a0a0]">
              <span>1d</span>
              <span>·</span>
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 0a8 8 0 100 16A8 8 0 008 0zM4.5 7.5a.5.5 0 01.5-.5h6a.5.5 0 010 1H5a.5.5 0 01-.5-.5z"/>
              </svg>
            </div>
          </div>
          <button className="text-[#a0a0a0] hover:text-white">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
            </svg>
          </button>
        </div>

        {/* Post content */}
        <div className="mb-3">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#e8e8e8]">{displayContent}</p>
          {content.length > 300 && (
            <button className="mt-1 text-sm font-medium text-[#a0a0a0] hover:text-[#0a66c2]">...see more</button>
          )}
        </div>

        {/* Hashtags */}
        {hashtags && (
          <p className="mb-3 text-sm text-[#0a66c2]">{hashtags}</p>
        )}

        {/* Image placeholder */}
        {imageUrl && (
          <div className="mb-3 aspect-video w-full overflow-hidden rounded bg-[#2d3239]">
            <div className="flex h-full items-center justify-center text-sm text-gray-500">
              [Generated Image]
            </div>
          </div>
        )}

        {/* Engagement counts */}
        <div className="flex items-center justify-between border-b border-[#3d4249] pb-2 text-xs text-[#a0a0a0]">
          <div className="flex items-center gap-1">
            <span className="flex -space-x-1">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#378fe9] text-[8px]">\uD83D\uDC4D</span>
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#e16745] text-[8px]">\u2764\uFE0F</span>
            </span>
            <span>{likes || 42}</span>
          </div>
          <div className="flex gap-3">
            <span>{comments || 8} comments</span>
            <span>{shares || 3} reposts</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-1 grid grid-cols-4 gap-1">
          {[
            { icon: '\uD83D\uDC4D', label: 'Like' },
            { icon: '\uD83D\uDCAC', label: 'Comment' },
            { icon: '\uD83D\uDD01', label: 'Repost' },
            { icon: '\u2709\uFE0F', label: 'Send' },
          ].map((action) => (
            <button
              key={action.label}
              className="flex items-center justify-center gap-1.5 rounded-lg py-2.5 text-xs font-medium text-[#a0a0a0] transition-colors hover:bg-[#2d3239]"
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
