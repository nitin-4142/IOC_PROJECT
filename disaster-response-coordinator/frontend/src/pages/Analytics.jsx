import React, { useState, useEffect } from 'react'
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Cell, PieChart, Pie, Legend 
} from 'recharts'
import { BarChart3, Activity, Cpu, Clock, RefreshCw, AlertCircle } from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, Spinner, ErrorState, DemoTag } from '../components/UI'

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
}

const STATUS_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#64748b']

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const res = await api.getAnalytics()
      setData(res.data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load system analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchAnalytics} />

  const { total_incidents = 0, by_severity = {}, by_status = {}, by_type = {}, agent_stats = [] } = data || {}

  const severityData = Object.entries(by_severity).map(([name, count]) => ({
    name,
    count,
    color: SEVERITY_COLORS[name] || '#3b82f6',
  }))

  const statusData = Object.entries(by_status).map(([name, count], idx) => ({
    name: name.replace('_', ' '),
    count,
    color: STATUS_COLORS[idx % STATUS_COLORS.length],
  }))

  const typeData = Object.entries(by_type).map(([name, count]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    count,
  }))

  return (
    <div className="pb-12">
      <PageHeader
        title="Operational Analytics & Agent Telemetry"
        subtitle="Processing performance, severity patterns, and AI fallback metrics"
      >
        <button
          onClick={fetchAnalytics}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </PageHeader>

      <div className="p-6 space-y-6">
        {/* Demonstration Disclaimer Banner */}
        <Card className="p-3 bg-navy-800/60 border-blue-900/40 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-400">
            <AlertCircle size={15} className="text-blue-400" />
            <span>Telemetry data derived strictly from the active local SQLite database session.</span>
          </div>
          <DemoTag />
        </Card>

        {/* Top Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Severity Chart */}
          <Card className="p-5">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 size={15} className="text-blue-400" />
              Incidents by Severity
            </h2>
            <div className="h-60">
              {severityData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No severity records logged</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={severityData}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0d1427', borderColor: '#1e293b', borderRadius: '6px' }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {severityData.map((entry, index) => (
                        <Cell key={`sev-cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>

          {/* Incident Type Chart */}
          <Card className="p-5">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Activity size={15} className="text-blue-400" />
              Disaster Categories
            </h2>
            <div className="h-60">
              {typeData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No category records logged</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={typeData} layout="vertical">
                    <XAxis type="number" stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={100} />
                    <Tooltip contentStyle={{ backgroundColor: '#0d1427', borderColor: '#1e293b', borderRadius: '6px' }} />
                    <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </div>

        {/* Agent Telemetry & Latency Table */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Cpu size={15} className="text-blue-400" />
              Multi-Agent Telemetry & Fallback Analytics
            </h2>
            <span className="text-[11px] text-slate-500">Real-time agent execution benchmarks</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-900/60 text-slate-400 border-b border-blue-900/30 text-[11px] uppercase">
                <tr>
                  <th className="px-4 py-2.5">Agent Module</th>
                  <th className="px-4 py-2.5">Total Executions</th>
                  <th className="px-4 py-2.5">Fallback Counts</th>
                  <th className="px-4 py-2.5">Average Latency (ms)</th>
                  <th className="px-4 py-2.5">Reliability Indicator</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-900/20 text-slate-300">
                {agent_stats.map((stat) => {
                  const fallbackPercent = stat.total_executions > 0 
                    ? Math.round((stat.fallback_count / stat.total_executions) * 100) 
                    : 0
                  return (
                    <tr key={stat.agent_name} className="hover:bg-navy-700/30">
                      <td className="px-4 py-3 font-mono text-blue-300 font-medium">
                        {stat.agent_name}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-white">
                        {stat.total_executions}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-yellow-400">{stat.fallback_count}</span>
                        <span className="text-[10px] text-slate-500 ml-1.5">({fallbackPercent}% fallback)</span>
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-200">
                        {stat.avg_duration_ms ? `${stat.avg_duration_ms.toFixed(1)} ms` : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-green-950 text-green-300 border border-green-800/40">
                          OPERATIONAL
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
