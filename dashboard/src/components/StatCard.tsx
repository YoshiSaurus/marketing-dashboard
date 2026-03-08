'use client'

interface StatCardProps {
  title: string
  value: number | string
  subtitle?: string
  color?: string
  icon?: string
}

const colorMap: Record<string, { border: string; bg: string; glow: string; text: string }> = {
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-500/10',
    glow: 'shadow-[0_0_15px_rgba(59,130,246,0.1)]',
    text: 'text-blue-400',
  },
  green: {
    border: 'border-emerald-500',
    bg: 'bg-emerald-500/10',
    glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]',
    text: 'text-emerald-400',
  },
  red: {
    border: 'border-red-500',
    bg: 'bg-red-500/10',
    glow: 'shadow-[0_0_15px_rgba(239,68,68,0.1)]',
    text: 'text-red-400',
  },
  yellow: {
    border: 'border-amber-500',
    bg: 'bg-amber-500/10',
    glow: 'shadow-[0_0_15px_rgba(245,158,11,0.1)]',
    text: 'text-amber-400',
  },
  purple: {
    border: 'border-purple-500',
    bg: 'bg-purple-500/10',
    glow: 'shadow-[0_0_15px_rgba(139,92,246,0.1)]',
    text: 'text-purple-400',
  },
  gray: {
    border: 'border-slate-500',
    bg: 'bg-slate-500/10',
    glow: 'shadow-[0_0_15px_rgba(100,116,139,0.1)]',
    text: 'text-slate-400',
  },
  cyan: {
    border: 'border-cyan-500',
    bg: 'bg-cyan-500/10',
    glow: 'shadow-[0_0_15px_rgba(6,182,212,0.1)]',
    text: 'text-cyan-400',
  },
}

export default function StatCard({ title, value, subtitle, color = 'blue' }: StatCardProps) {
  const c = colorMap[color] || colorMap.blue

  return (
    <div className={`rounded-xl border-l-4 ${c.border} ${c.bg} ${c.glow} p-4 transition-all hover:scale-[1.02]`}>
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{title}</p>
      <p className={`mt-1 text-3xl font-bold ${c.text}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
    </div>
  )
}
