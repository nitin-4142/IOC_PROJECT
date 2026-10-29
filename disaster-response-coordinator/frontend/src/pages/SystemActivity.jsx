import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Activity, Clock, ShieldCheck, CheckCircle2, 
  XCircle, UserCheck, RefreshCw, Cpu 
} from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, Spinner, ErrorState, StatusBadge } from '../components/UI'

export default function SystemActivity() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchActivity = async () => {
    try {
      setLoading(true)
      const res = await api.listIncidents({ per_page: 30 })
      setIncidents(res.data.incidents || [])
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load system events.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivity()
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchActivity} />

  return (
    <div className="pb-12">
      <PageHeader
        title="System Event & Agent Audit Stream"
        subtitle="Complete chronological transaction log of pipeline executions and operator actions"
      >
        <button
          onClick={fetchActivity}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </PageHeader>

      <div className="p-6 space-y-4">
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-blue-900/30 flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Activity size={15} className="text-blue-400" />
              Event Ledger & Operator Actions
            </h2>
            <span className="text-xs text-slate-500">{incidents.length} events logged</span>
          </div>

          <div className="divide-y divide-blue-900/20">
            {incidents.map((inc) => (
              <div key={inc.id} className="p-4 hover:bg-navy-700/30 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-white uppercase">
                        [{inc.incident_type || 'INCIDENT'}]
                      </span>
                      <span className="text-xs text-slate-400">
                        {inc.location_text || 'Unverified Location'}
                      </span>
                      <StatusBadge status={inc.status} />
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-1">{inc.raw_report}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                      <span>Incident ID: <strong className="font-mono text-slate-300">{inc.id.slice(0, 8)}...</strong></span>
                      <span>Source: <strong className="text-blue-300 capitalize">{inc.processing_source || 'deterministic'}</strong></span>
                      <span>Priority Score: <strong className="font-mono text-orange-400">{inc.risk_score ? inc.risk_score.toFixed(1) : '—'}/100</strong></span>
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <div className="text-[11px] text-slate-400">
                      {inc.created_at ? new Date(inc.created_at).toLocaleString() : '—'}
                    </div>
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="inline-block mt-2 text-xs text-blue-400 hover:text-blue-300 underline font-medium"
                    >
                      Audit Trail →
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
