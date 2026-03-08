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
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
}

export default function SuggestionsTable({ suggestions }: SuggestionsTableProps) {
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="rounded-lg bg-white p-8 text-center text-gray-500">
        No suggestions generated yet.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg bg-white shadow">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Blog Title</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Category</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Approved By</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {suggestions.map((s) => (
            <tr key={s.id} className="hover:bg-gray-50">
              <td className="max-w-sm truncate px-4 py-3 text-sm font-medium text-gray-900">
                {s.blog_title || s.id}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{s.content_category}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${statusBadge[s.approval_status] || 'bg-gray-100'}`}>
                  {s.approval_status}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{s.approved_by || '-'}</td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                {new Date(s.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
