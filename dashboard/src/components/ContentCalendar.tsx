'use client'

import { useState, useMemo } from 'react'
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
  isToday,
  addMonths,
  subMonths,
  parseISO,
} from 'date-fns'

interface CalendarPost {
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

interface ContentCalendarProps {
  posts: CalendarPost[]
  onSelectPost?: (post: CalendarPost) => void
}

const platformColors: Record<string, { dot: string; bg: string; text: string }> = {
  linkedin: { dot: 'bg-sky-400', bg: 'bg-sky-500/15', text: 'text-sky-300' },
  website: { dot: 'bg-blue-400', bg: 'bg-blue-500/15', text: 'text-blue-300' },
  twitter: { dot: 'bg-gray-400', bg: 'bg-gray-500/15', text: 'text-gray-300' },
}

export default function ContentCalendar({ posts, onSelectPost }: ContentCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState<Date | null>(null)

  const postsByDate = useMemo(() => {
    const map: Record<string, CalendarPost[]> = {}
    posts.forEach((post) => {
      const dateKey = format(parseISO(post.published_at), 'yyyy-MM-dd')
      if (!map[dateKey]) map[dateKey] = []
      map[dateKey].push(post)
    })
    return map
  }, [posts])

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 0 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 0 })
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const selectedDateKey = selectedDay ? format(selectedDay, 'yyyy-MM-dd') : null
  const selectedPosts = selectedDateKey ? (postsByDate[selectedDateKey] || []) : []

  return (
    <div className="space-y-4">
      <div className="glass-card overflow-hidden">
        {/* Month navigation */}
        <div className="flex items-center justify-between border-b border-dark-border px-5 py-4">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-dark-elevated hover:text-white"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
            </svg>
          </button>
          <h3 className="text-lg font-bold text-gray-100">
            {format(currentMonth, 'MMMM yyyy')}
          </h3>
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-dark-elevated hover:text-white"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
            </svg>
          </button>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 border-b border-dark-border">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="py-2 text-center text-xs font-semibold uppercase tracking-wider text-gray-500">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7">
          {calendarDays.map((day) => {
            const dateKey = format(day, 'yyyy-MM-dd')
            const dayPosts = postsByDate[dateKey] || []
            const isCurrentMonth = isSameMonth(day, currentMonth)
            const isSelected = selectedDay && isSameDay(day, selectedDay)
            const today = isToday(day)

            return (
              <button
                key={dateKey}
                onClick={() => setSelectedDay(day)}
                className={`calendar-day relative min-h-[80px] border-b border-r border-dark-border/50 p-2 text-left transition-all
                  ${!isCurrentMonth ? 'opacity-30' : ''}
                  ${isSelected ? 'bg-dark-elevated ring-1 ring-blue-500/50' : ''}
                  ${today && !isSelected ? 'bg-blue-500/5' : ''}
                `}
              >
                <span className={`text-xs font-medium ${today ? 'flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-white' : 'text-gray-400'}`}>
                  {format(day, 'd')}
                </span>

                {/* Post indicators */}
                {dayPosts.length > 0 && (
                  <div className="mt-1 space-y-0.5">
                    {dayPosts.slice(0, 3).map((post, i) => {
                      const colors = platformColors[post.platform] || platformColors.website
                      return (
                        <div
                          key={i}
                          className={`flex items-center gap-1 rounded px-1 py-0.5 ${colors.bg}`}
                        >
                          <span className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${colors.dot}`} />
                          <span className={`truncate text-[10px] font-medium ${colors.text}`}>
                            {post.title?.slice(0, 20) || post.platform}
                          </span>
                        </div>
                      )
                    })}
                    {dayPosts.length > 3 && (
                      <span className="block text-center text-[10px] text-gray-500">
                        +{dayPosts.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Selected day detail panel */}
      {selectedDay && (
        <div className="glass-card p-5">
          <h4 className="mb-3 text-sm font-semibold text-gray-200">
            {format(selectedDay, 'EEEE, MMMM d, yyyy')}
            <span className="ml-2 text-gray-500">
              {selectedPosts.length} post{selectedPosts.length !== 1 ? 's' : ''}
            </span>
          </h4>

          {selectedPosts.length === 0 ? (
            <p className="py-4 text-center text-sm text-gray-500">No posts scheduled for this day</p>
          ) : (
            <div className="space-y-3">
              {selectedPosts.map((post) => {
                const colors = platformColors[post.platform] || platformColors.website
                return (
                  <div
                    key={post.id}
                    onClick={() => onSelectPost?.(post)}
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border border-dark-border p-3 transition-all hover:border-dark-border-bright hover:bg-dark-card-hover ${onSelectPost ? 'cursor-pointer' : ''}`}
                  >
                    <div className={`mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg ${colors.bg}`}>
                      <span className={`text-xs font-bold ${colors.text}`}>
                        {post.platform === 'linkedin' ? 'in' : post.platform === 'twitter' ? 'X' : 'W'}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-200">{post.title || post.content_preview?.slice(0, 80)}</p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {post.platform} · {post.content_category?.replace(/_/g, ' ')}
                      </p>
                      <div className="mt-1.5 flex gap-3 text-xs text-gray-500">
                        <span className="text-emerald-400">{post.likes} likes</span>
                        <span className="text-blue-400">{post.comments} comments</span>
                        <span className="text-purple-400">{post.shares} shares</span>
                      </div>
                    </div>
                    {onSelectPost && (
                      <button className="flex-shrink-0 rounded-lg bg-dark-elevated px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white">
                        Preview
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
