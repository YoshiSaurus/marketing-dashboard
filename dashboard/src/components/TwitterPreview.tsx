'use client'

interface TwitterPreviewProps {
  authorName?: string
  handle?: string
  content: string
  hashtags?: string
  likes?: number
  comments?: number
  shares?: number
  imageUrl?: string | null
}

export default function TwitterPreview({
  authorName = 'Foliox AI',
  handle = '@foliox_ai',
  content,
  hashtags,
  likes = 0,
  comments = 0,
  shares = 0,
  imageUrl,
}: TwitterPreviewProps) {
  const fullContent = hashtags ? `${content}\n\n${hashtags}` : content

  return (
    <div className="preview-frame mx-auto max-w-[520px]">
      {/* X header bar */}
      <div className="flex items-center justify-between border-b border-dark-border bg-dark-card px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-red-500/60" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
          <div className="h-3 w-3 rounded-full bg-green-500/60" />
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-base font-bold text-white">{'\uD835\uDD4F'}</span>
          <span className="text-xs font-semibold text-gray-400">/ Post</span>
        </div>
      </div>

      {/* Tweet card */}
      <div className="bg-black p-4">
        {/* Author row */}
        <div className="mb-2 flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-blue-500 text-sm font-bold text-white">
            F
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-1">
              <span className="text-sm font-bold text-white">{authorName}</span>
              <svg className="h-4 w-4 text-[#1d9bf0]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z"/>
              </svg>
            </div>
            <p className="text-sm text-[#71767b]">{handle}</p>
          </div>
          <svg className="h-5 w-5 text-[#71767b]" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
          </svg>
        </div>

        {/* Tweet content */}
        <div className="mb-3 pl-[52px]">
          <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-[#e7e9ea]">{fullContent}</p>
        </div>

        {/* Image placeholder */}
        {imageUrl && (
          <div className="mb-3 ml-[52px] aspect-video overflow-hidden rounded-2xl border border-[#2f3336] bg-[#16181c]">
            <div className="flex h-full items-center justify-center text-sm text-gray-600">
              [Generated Image]
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="mb-3 pl-[52px] text-sm text-[#71767b]">
          <span>2:30 PM · Mar 8, 2026</span>
          <span className="mx-1">·</span>
          <span className="font-semibold text-white">{(likes || 24) * 12}</span>
          <span> Views</span>
        </div>

        {/* Engagement counts */}
        <div className="ml-[52px] flex gap-5 border-y border-[#2f3336] py-3 text-sm">
          <span><span className="font-semibold text-white">{shares || 5}</span> <span className="text-[#71767b]">Reposts</span></span>
          <span><span className="font-semibold text-white">{Math.floor((likes || 24) * 0.3)}</span> <span className="text-[#71767b]">Quotes</span></span>
          <span><span className="font-semibold text-white">{likes || 24}</span> <span className="text-[#71767b]">Likes</span></span>
          <span><span className="font-semibold text-white">{Math.floor((likes || 24) * 0.2)}</span> <span className="text-[#71767b]">Bookmarks</span></span>
        </div>

        {/* Action bar */}
        <div className="ml-[52px] mt-1 flex justify-between py-2 pr-16">
          {[
            { icon: (
              <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 20.25c4.97 0 9-3.694 9-8.25s-4.03-8.25-9-8.25S3 7.444 3 12c0 2.104.859 4.023 2.273 5.48.432.447.74 1.04.586 1.641a4.483 4.483 0 01-.923 1.785A5.969 5.969 0 006 21c1.282 0 2.47-.402 3.445-1.087.81.22 1.668.337 2.555.337z"/>
              </svg>
            ), label: comments || 8 },
            { icon: (
              <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3l-3-3m-12 3c0 1.232.046 2.453.138 3.662a4.006 4.006 0 003.7 3.7 48.656 48.656 0 007.324 0 4.006 4.006 0 003.7-3.7c.017-.22.032-.441.046-.662M4.5 12l3 3m-3-3l-3 3"/>
              </svg>
            ), label: shares || 5 },
            { icon: (
              <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"/>
              </svg>
            ), label: likes || 24 },
            { icon: (
              <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
              </svg>
            ), label: '' },
          ].map((action, i) => (
            <button key={i} className="flex items-center gap-1.5 text-[#71767b] transition-colors hover:text-[#1d9bf0]">
              {action.icon}
              {action.label !== '' && <span className="text-xs">{action.label}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
