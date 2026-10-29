import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  AlertTriangle, Flame, ShieldAlert, CheckCircle2, 
  Clock, ArrowRight, RefreshCw, BarChart2 
} from 'lucide-react'
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Cell, PieChart, Pie, Legend 
} from 'recharts'
import api from '../services/api'
import { Card, StatCard, SeverityBadge, StatusBadge, PageHeader, Spinner, ErrorState } from '../components/UI'

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [queue, setQueue] = useState([])
  const [recentIncidents, setRecentIncidents] = useState([])
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      setRefreshing(true)
      const [analyticsRes, queueRes, incidentsRes] = await Promise.all([
        api.getAnalytics(),
        api.getQueue(),
        api.listIncidents({ per_page: 5 }),
      ])
      setAnalytics(analyticsRes.data)
      setQueue(queueRes.data.queue || [])
      setRecentIncidents(incidentsRes.data.incidents || [])
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchData} />

  const total = analytics?.total_incidents || 0
  const bySeverity = analytics?.by_severity || {}
  const byStatus = analytics?.by_status || {}

  const criticalCount = bySeverity.CRITICAL || 0
  const highCount = bySeverity.HIGH || 0
  const awaitingApproval = byStatus.PLAN_READY || 0
  const resolvedCount = byStatus.RESOLVED || 0
  const activeCount = queue.length

  const severityChartData = [
    { name: 'CRITICAL', count: bySeverity.CRITICAL || 0, color: SEVERITY_COLORS.CRITICAL },
    { name: 'HIGH', count: bySeverity.HIGH || 0, color: SEVERITY_COLORS.HIGH },
    { name: 'MEDIUM', count: bySeverity.MEDIUM || 0, color: SEVERITY_COLORS.MEDIUM },
    { name: 'LOW', count: bySeverity.LOW || 0, color: SEVERITY_COLORS.LOW },
  ]

  const typeChartData = Object.entries(analytics?.by_type || {}).map(([type, count]) => ({
    name: type.replace('_', ' ').toUpperCase(),
    count,
  }))

  return (
    <div className="pb-12">
      <PageHeader 
        title="Emergency Operations Command Center" 
        subtitle="Real-time multi-agent disaster coordination, triage, and response analytics"
      >
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40 transition-colors"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
          <Link
            to="/report"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors"
          >
            <AlertTriangle size={13} />
            Report Emergency
          </Link>
        </div>
      </PageHeader>

      <div className="p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            label="Active Incidents"
            value={activeCount}
            icon={ShieldAlert}
            color="orange"
            sub="Under active triage/coordination"
          />
          <StatCard
            label="Critical Priority"
            value={criticalCount}
            icon={Flame}
            color="red"
            sub="Immediate response required"
          />
          <StatCard
            label="High Priority"
            value={highCount}
            icon={AlertTriangle}
            color="yellow"
            sub="Urgent resource mobilization"
          />
          <StatCard
            label="Awaiting Approval"
            value={awaitingApproval}
            icon={Clock}
            color="purple"
            sub="Operator authorization pending"
          />
          <StatCard
            label="Resolved"
            value={resolvedCount}
            icon={CheckCircle2}
            color="green"
            sub="Incidents cleared"
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <BarChart2 size={16} className="text-blue-400" />
                Severity Breakdown
              </h2>
              <span className="text-xs text-slate-500">All registered incidents</span>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityChartData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0d1427', borderColor: '#1e293b', borderRadius: '6px' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle size={16} className="text-blue-400" />
                Incidents by Disaster Type
              </h2>
              <span className="text-xs text-slate-500">Classification count</span>
            </div>
            <div className="h-56">
              {typeChartData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  No incident category data yet
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={typeChartData} layout="vertical">
                    <XAxis type="number" stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={110} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0d1427', borderColor: '#1e293b', borderRadius: '6px' }}
                      itemStyle={{ color: '#f8fafc' }}
                    />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </div>

        {/* Priority Queue & Recent Incidents */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Priority Queue */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Flame size={16} className="text-red-400" />
                Current Priority Queue
              </h2>
              <Link to="/incidents" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                View all <ArrowRight size={12} />
              </Link>
            </div>
            {queue.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No active incidents in the priority queue.</p>
            ) : (
              <div className="space-y-2.5">
                {queue.slice(0, 5).map((inc) => (
                  <Link
                    key={inc.id}
                    to={`/incidents/${inc.id}`}
                    className="block p-3 rounded bg-navy-700/50 hover:bg-navy-700 border border-blue-900/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <SeverityBadge severity={inc.severity} />
                          <span className="text-xs font-mono text-slate-400">
                            Risk {inc.risk_score ? inc.risk_score.toFixed(1) : '—'}/100
                          </span>
                          <span className="text-xs font-semibold text-slate-300 uppercase">
                            {inc.incident_type || 'Unknown'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 line-clamp-1">{inc.raw_report}</p>
                        <p className="text-[11px] text-slate-400 mt-1">
                          📍 {inc.location_text || 'Location unverified'}
                        </p>
                      </div>
                      <StatusBadge status={inc.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* Recent Submissions */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Clock size={16} className="text-blue-400" />
                Recent Incident Logs
              </h2>
              <span className="text-xs text-slate-500">Latest entries</span>
            </div>
            {recentIncidents.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No incident reports recorded yet.</p>
            ) : (
              <div className="space-y-2.5">
                {recentIncidents.map((inc) => (
                  <Link
                    key={inc.id}
                    to={`/incidents/${inc.id}`}
                    className="block p-3 rounded bg-navy-700/50 hover:bg-navy-700 border border-blue-900/30 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <SeverityBadge severity={inc.severity} />
                        <span className="text-xs text-slate-300 font-medium">
                          {inc.location_text || 'Location unverified'}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{inc.raw_report}</p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Source: {inc.processing_source || 'deterministic'}</span>
                      <StatusBadge status={inc.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
