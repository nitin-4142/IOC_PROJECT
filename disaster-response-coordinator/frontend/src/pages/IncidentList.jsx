import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Filter, Search, ArrowUpDown, ChevronLeft, ChevronRight, 
  AlertTriangle, RefreshCw, Eye 
} from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, SeverityBadge, StatusBadge, Spinner, ErrorState } from '../components/UI'

export default function IncidentList() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')

  const fetchIncidents = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        per_page: 15,
      }
      if (severityFilter) params.severity = severityFilter
      if (statusFilter) params.status = statusFilter

      const res = await api.listIncidents(params)
      setIncidents(res.data.incidents || [])
      setTotalPages(res.data.pages || 1)
      setTotalCount(res.data.total || 0)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load incidents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIncidents()
  }, [page, severityFilter, statusFilter])

  const filteredIncidents = incidents.filter((inc) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      (inc.location_text && inc.location_text.toLowerCase().includes(q)) ||
      (inc.raw_report && inc.raw_report.toLowerCase().includes(q)) ||
      (inc.incident_type && inc.incident_type.toLowerCase().includes(q)) ||
      inc.id.toLowerCase().includes(q)
    )
  })

  return (
    <div className="pb-12">
      <PageHeader
        title="Incident Directory"
        subtitle={`Audit register of all recorded disaster events (${totalCount} total)`}
      >
        <button
          onClick={fetchIncidents}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </PageHeader>

      <div className="p-6 space-y-4">
        {/* Filter bar */}
        <Card className="p-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px] relative">
              <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by keywords, location, or incident ID..."
                className="w-full pl-8 pr-3 py-1.5 bg-navy-900 border border-blue-900/40 rounded text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter size={14} className="text-slate-400" />
              <select
                value={severityFilter}
                onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
                className="bg-navy-900 border border-blue-900/40 text-xs text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="bg-navy-900 border border-blue-900/40 text-xs text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="NEW">NEW</option>
                <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                <option value="PLAN_READY">PLAN_READY</option>
                <option value="APPROVED">APPROVED</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="RESOLVED">RESOLVED</option>
              </select>
            </div>
          </div>
        </Card>

        {loading ? (
          <Spinner />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchIncidents} />
        ) : filteredIncidents.length === 0 ? (
          <Card className="p-12 text-center text-slate-500 text-xs">
            No incidents matched your query.
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-navy-900/80 text-slate-400 border-b border-blue-900/30 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3">Risk Score</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3">Logged At</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-blue-900/20 text-slate-300">
                  {filteredIncidents.map((inc) => (
                    <tr key={inc.id} className="hover:bg-navy-700/40 transition-colors">
                      <td className="px-4 py-3">
                        <SeverityBadge severity={inc.severity} />
                      </td>
                      <td className="px-4 py-3 font-medium uppercase text-slate-200">
                        {inc.incident_type || '—'}
                      </td>
                      <td className="px-4 py-3 max-w-[200px] truncate">
                        {inc.location_text || (inc.latitude ? `${inc.latitude.toFixed(2)}, ${inc.longitude.toFixed(2)}` : 'Unverified')}
                      </td>
                      <td className="px-4 py-3 font-mono font-semibold">
                        {inc.risk_score ? inc.risk_score.toFixed(1) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={inc.status} />
                      </td>
                      <td className="px-4 py-3 text-slate-400 capitalize">
                        {inc.processing_source || 'fallback'}
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-[11px]">
                        {inc.created_at ? new Date(inc.created_at).toLocaleString() : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/incidents/${inc.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded border border-blue-600/30 transition-colors"
                        >
                          <Eye size={12} /> View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-blue-900/30 flex items-center justify-between text-xs text-slate-400">
                <span>Page {page} of {totalPages}</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1 rounded bg-navy-700 disabled:opacity-40"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1 rounded bg-navy-700 disabled:opacity-40"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}
