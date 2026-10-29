import React from 'react'

export function SeverityBadge({ severity }) {
  const colors = {
    CRITICAL: 'bg-red-600/20 text-red-400 border border-red-600/40',
    HIGH: 'bg-orange-600/20 text-orange-400 border border-orange-600/40',
    MEDIUM: 'bg-yellow-600/20 text-yellow-400 border border-yellow-600/40',
    LOW: 'bg-green-600/20 text-green-400 border border-green-600/40',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${colors[severity] || 'bg-slate-700 text-slate-300'}`}>
      {severity || 'UNKNOWN'}
    </span>
  )
}

export function StatusBadge({ status }) {
  const colors = {
    NEW: 'bg-blue-600/20 text-blue-300',
    UNDER_REVIEW: 'bg-purple-600/20 text-purple-300',
    AWAITING_INFORMATION: 'bg-yellow-600/20 text-yellow-300',
    PLAN_READY: 'bg-cyan-600/20 text-cyan-300',
    APPROVED: 'bg-green-600/20 text-green-300',
    IN_PROGRESS: 'bg-orange-600/20 text-orange-300',
    RESOLVED: 'bg-slate-600/20 text-slate-400',
    CANCELLED: 'bg-red-900/20 text-red-600',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] || 'bg-slate-700 text-slate-300'}`}>
      {status || '—'}
    </span>
  )
}

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-navy-800 border border-blue-900/30 rounded-lg ${className}`}>
      {children}
    </div>
  )
}

export function StatCard({ label, value, icon: Icon, color = 'blue', sub }) {
  const colorMap = {
    blue: 'text-blue-400',
    red: 'text-red-400',
    orange: 'text-orange-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    purple: 'text-purple-400',
  }
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${colorMap[color]}`}>{value ?? '—'}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        {Icon && <Icon className={`${colorMap[color]} opacity-60`} size={28} />}
      </div>
    </Card>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="px-6 py-4 border-b border-blue-900/30 bg-navy-800/50 flex items-center justify-between">
      <div>
        <h1 className="text-lg font-semibold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center h-32">
      <div className="w-8 h-8 border-4 border-blue-600/30 border-t-blue-500 rounded-full animate-spin" />
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-32 gap-3">
      <p className="text-red-400 text-sm">⚠ {message}</p>
      {onRetry && (
        <button onClick={onRetry} className="px-3 py-1 text-xs bg-blue-600/20 text-blue-300 rounded hover:bg-blue-600/30">
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message }) {
  return (
    <div className="flex items-center justify-center h-32">
      <p className="text-slate-500 text-sm">{message}</p>
    </div>
  )
}

export function DemoTag() {
  return (
    <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-900/30 text-yellow-500 border border-yellow-700/30 ml-1">
      DEMO
    </span>
  )
}
