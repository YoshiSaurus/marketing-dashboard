const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'

async function fetchAPI(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 60 } })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function getDashboardSummary() {
  return fetchAPI('/api/dashboard')
}

export async function getRecentPosts(limit = 20) {
  return fetchAPI(`/api/posts?limit=${limit}`)
}

export async function getCategoryPerformance() {
  return fetchAPI('/api/categories')
}

export async function getPlatformStats() {
  return fetchAPI('/api/platforms')
}

export async function getTimeline(days = 30) {
  return fetchAPI(`/api/timeline?days=${days}`)
}

export async function getSuggestions(limit = 50) {
  return fetchAPI(`/api/suggestions?limit=${limit}`)
}

export async function getPostsByCategory() {
  return fetchAPI('/api/posts-by-category')
}
