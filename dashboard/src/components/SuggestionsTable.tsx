'use client'

interface Suggestion {
  id: string
  created_at: string
  content_category: string
  blog_title: string
  approval_status: string
  approved_by: string | null
  approved_at: string | null
}

interface SuggestionsTableProps {
  suggestions: Suggestion[]
}

const statusBadge: Record<string, string> = {
  pending: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  approved: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  rejected: 'bg-red-500/20 text-red-400 border border-red-500/30',
}

const statusDot: Record<string, string> = {
  pending: 'bg-amber-400',
  approved: 'bg-emerald-400',
  rejected: 'bg-red-400',
}

export default function SuggestionsTable({ suggestions }: SuggestionsTableProps) {
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="glass-card p-8 text-center text-gray-500">
        No suggestions generated yet.
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-dark-border">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Blog Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Approved By</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border/50">
            {suggestions.map((s) => (
              <tr key={s.id} className="transition-colors hover:bg-dark-card-hover">
                <td className="max-w-sm truncate px-4 py-3 text-sm font-medium text-gray-200">
                  {s.blog_title || s.id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">{s.content_category?.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge[s.approval_status] || 'bg-gray-500/20 text-gray-400'}`}>
                    <span className={`inline-block h-1.5 w-1.5 rounded-full ${statusDot[s.approval_status] || 'bg-gray-400'}`} />
                    {s.approval_status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">{s.approved_by || '\u2014'}</td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                  {new Date(s.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
