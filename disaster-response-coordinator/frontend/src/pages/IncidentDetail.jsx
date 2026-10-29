import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  ArrowLeft, CheckCircle2, XCircle, AlertTriangle, 
  Clock, ShieldAlert, Cpu, MapPin, Truck, HelpCircle, 
  UserCheck, ShieldCheck, FileText, CornerDownRight 
} from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, SeverityBadge, StatusBadge, Spinner, ErrorState, DemoTag } from '../components/UI'

export default function IncidentDetail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [approving, setApproving] = useState(false)
  const [operatorName, setOperatorName] = useState('Commander John Smith')
  const [approvalNotes, setApprovalNotes] = useState('')
  const [approvalFeedback, setApprovalFeedback] = useState(null)

  const fetchIncident = async () => {
    try {
      setLoading(true)
      const res = await api.getIncident(id)
      setData(res.data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load incident detail.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIncident()
  }, [id])

  const handleApproval = async (decision) => {
    if (!operatorName.trim()) {
      alert('Operator name is required to record approval audit.')
      return
    }
    try {
      setApproving(true)
      const res = await api.approveIncident(id, {
        operator_name: operatorName.trim(),
        decision,
        notes: approvalNotes.trim() || undefined,
      })
      setApprovalFeedback(res.data)
      // Refresh local incident data
      await fetchIncident()
    } catch (err) {
      alert(err.message || 'Approval action failed.')
    } finally {
      setApproving(false)
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchIncident} />
  if (!data || !data.incident) return <ErrorState message="Incident not found" />

  const { incident, risk_assessment: risk, resources = [], response_plan: plan, agent_executions: execs = [] } = data

  return (
    <div className="pb-16">
      <PageHeader
        title={`Incident Dossier: ${incident.incident_type ? incident.incident_type.toUpperCase() : 'INCIDENT'}`}
        subtitle={`ID: ${incident.id} | Correlation ID: ${incident.correlation_id}`}
      >
        <div className="flex items-center gap-3">
          <Link
            to="/incidents"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
          >
            <ArrowLeft size={13} />
            Back to Directory
          </Link>
        </div>
      </PageHeader>

      <div className="p-6 space-y-6">
        {/* Status & Priority Banner */}
        <Card className="p-4 bg-navy-800/80 border-blue-800/40 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
            <span className="text-xs text-slate-400">
              Risk Score: <strong className="text-white font-mono">{incident.risk_score ? incident.risk_score.toFixed(1) : '—'}/100</strong>
            </span>
            <span className="text-xs text-slate-400">
              Extraction Source: <strong className="text-blue-300 capitalize">{incident.processing_source || 'deterministic'}</strong>
            </span>
          </div>

          <div className="text-xs text-slate-400">
            Registered: {incident.created_at ? new Date(incident.created_at).toLocaleString() : '—'}
          </div>
        </Card>

        {/* Section 1: Raw Report & Intelligence Extraction (Agent 1) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5 space-y-3">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <FileText size={15} className="text-blue-400" />
              Original Emergency Transmission
            </h2>
            <div className="p-3 bg-navy-900 rounded border border-blue-900/40 text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">
              {incident.raw_report}
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Location text:</span>
                <span className="text-slate-200 font-medium">{incident.location_text || 'Not reported'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Reported time:</span>
                <span className="text-slate-200 font-medium">{incident.reported_time || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">GPS Coordinates:</span>
                <span className="text-slate-200 font-medium">
                  {incident.latitude ? `${incident.latitude.toFixed(4)}, ${incident.longitude.toFixed(4)}` : 'Unverified (no GPS)'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Affected Population:</span>
                <span className="text-slate-200 font-medium">
                  {incident.affected_population ? `${incident.affected_population} individuals` : 'Unknown'}
                </span>
              </div>
            </div>
          </Card>

          <Card className="p-5 space-y-3">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Cpu size={15} className="text-blue-400" />
              Agent 1: Intelligence Analysis
            </h2>

            <div>
              <span className="text-[11px] text-slate-400 font-semibold block mb-1">Immediate Threats Flagged:</span>
              {incident.immediate_threats && incident.immediate_threats.length > 0 ? (
                <ul className="space-y-1">
                  {incident.immediate_threats.map((threat, idx) => (
                    <li key={idx} className="text-xs text-red-300 flex items-start gap-1.5">
                      <AlertTriangle size={13} className="text-red-400 flex-shrink-0 mt-0.5" />
                      <span>{threat}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">None explicitly flagged in text</p>
              )}
            </div>

            <div className="pt-2">
              <span className="text-[11px] text-slate-400 font-semibold block mb-1">Missing / Unverified Information:</span>
              {incident.missing_information && incident.missing_information.length > 0 ? (
                <ul className="space-y-1">
                  {incident.missing_information.map((miss, idx) => (
                    <li key={idx} className="text-xs text-yellow-300/80 flex items-start gap-1.5">
                      <HelpCircle size={13} className="text-yellow-400 flex-shrink-0 mt-0.5" />
                      <span>{miss}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">No critical missing items flagged</p>
              )}
            </div>
          </Card>
        </div>

        {/* Section 2: Agent 2 Risk Assessment */}
        {risk && (
          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert size={15} className="text-orange-400" />
                Agent 2: Risk Assessment & Scoring Model
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Confidence: {(risk.confidence * 100).toFixed(0)}%</span>
                {risk.requires_human_review && (
                  <span className="px-2 py-0.5 bg-yellow-900/30 text-yellow-400 border border-yellow-700/40 rounded text-xs">
                    ⚠ Human Review Recommended
                  </span>
                )}
              </div>
            </div>

            <div className="p-3 bg-navy-900 rounded border border-blue-900/40 text-xs text-slate-300">
              <strong>Rationale:</strong> {risk.rationale}
            </div>

            <div>
              <span className="text-[11px] text-slate-400 font-semibold block mb-1.5">Contributing Scoring Factors:</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {risk.contributing_factors && risk.contributing_factors.map((factor, idx) => (
                  <div key={idx} className="p-2 bg-navy-700/40 rounded border border-blue-900/20 text-xs text-slate-300 flex items-center gap-2">
                    <CornerDownRight size={13} className="text-blue-400 flex-shrink-0" />
                    <span>{factor}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {/* Section 3: Agent 3 Resource Recommendations */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Truck size={15} className="text-green-400" />
              Agent 3: Resource Mobilization Recommendations
            </h2>
            <DemoTag />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-900/60 text-slate-400 border-b border-blue-900/30 text-[11px] uppercase">
                <tr>
                  <th className="px-3 py-2">Resource Type</th>
                  <th className="px-3 py-2">Recommended Qty</th>
                  <th className="px-3 py-2">Tactical Justification</th>
                  <th className="px-3 py-2">Sample Availability</th>
                  <th className="px-3 py-2">Data Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-900/20 text-slate-300">
                {resources.map((r) => (
                  <tr key={r.id} className="hover:bg-navy-700/30">
                    <td className="px-3 py-2.5 font-medium uppercase text-blue-300">
                      {r.resource_type.replace('_', ' ')}
                    </td>
                    <td className="px-3 py-2.5 font-bold font-mono text-white">
                      {r.recommended_quantity}
                    </td>
                    <td className="px-3 py-2.5 text-slate-400 max-w-xs">{r.reason}</td>
                    <td className="px-3 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-yellow-400 border border-yellow-700/30">
                        {r.availability_status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-slate-500 text-[11px]">
                      {r.source_of_availability_data}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Section 4: Agent 5 Response Plan & Approval Controls */}
        {plan && (
          <Card className="p-5 space-y-4 border-blue-700/50 bg-gradient-to-br from-navy-800 to-navy-900">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck size={16} className="text-blue-400" />
                Agent 5: Coordinated Incident Response Plan
              </h2>
              <StatusBadge status={plan.approval_status} />
            </div>

            <div className="p-3 bg-navy-900/80 rounded border border-blue-900/40 text-xs text-slate-200">
              <p className="font-semibold text-blue-300 mb-1">Executive Summary:</p>
              <p className="leading-relaxed">{plan.summary}</p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-300 mb-2">Priority Action Checklist:</p>
              <div className="space-y-1.5">
                {plan.priority_actions && plan.priority_actions.map((action, idx) => (
                  <div key={idx} className="p-2.5 bg-navy-700/30 rounded border border-blue-900/30 text-xs text-slate-200 flex items-start gap-2">
                    <span className="font-mono text-blue-400 font-bold">{idx + 1}.</span>
                    <span>{action}</span>
                  </div>
                ))}
              </div>
            </div>

            {plan.follow_up_questions && plan.follow_up_questions.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 mb-1.5">Recommended Operator Follow-Up Inquiries:</p>
                <ul className="space-y-1 text-xs text-slate-400">
                  {plan.follow_up_questions.map((q, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <HelpCircle size={13} className="text-slate-500" />
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Operator Approval Interface */}
            <div className="mt-4 pt-4 border-t border-blue-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-2">
                  <UserCheck size={15} className="text-blue-400" />
                  Mandatory Operator Approval Authorization
                </h3>
                <span className="text-[11px] text-yellow-400 bg-yellow-900/20 px-2 py-0.5 rounded border border-yellow-800/40">
                  Strict Human-in-the-Loop Safeguard
                </span>
              </div>

              <div className="p-3 bg-yellow-950/20 border border-yellow-800/40 rounded text-[11px] text-yellow-300">
                ⚠ The application is a decision-support prototype. Approving this plan logs an authorized decision in the audit trail. No real emergency dispatch or communication is triggered.
              </div>

              {plan.approval_status === 'APPROVED' ? (
                <div className="p-3 bg-green-950/30 border border-green-800/50 rounded flex items-center justify-between text-xs text-green-300">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 size={16} />
                    <span>Plan APPROVED by <strong>{plan.approved_by}</strong> on {new Date(plan.approved_at).toLocaleString()}</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 bg-navy-900/60 p-4 rounded border border-blue-900/30">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Authorizing Operator Name *</label>
                      <input
                        type="text"
                        value={operatorName}
                        onChange={(e) => setOperatorName(e.target.value)}
                        className="w-full bg-navy-800 border border-blue-900/50 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Approval Notes / Modifications</label>
                      <input
                        type="text"
                        value={approvalNotes}
                        onChange={(e) => setApprovalNotes(e.target.value)}
                        placeholder="e.g. Approved with priority to northern embankment"
                        className="w-full bg-navy-800 border border-blue-900/50 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => handleApproval('REJECTED')}
                      disabled={approving}
                      className="px-3 py-1.5 bg-red-950 hover:bg-red-900 text-red-300 border border-red-800/50 rounded text-xs font-medium transition-colors"
                    >
                      Reject Plan
                    </button>
                    <button
                      onClick={() => handleApproval('APPROVED')}
                      disabled={approving}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded text-xs font-semibold transition-colors"
                    >
                      <CheckCircle2 size={14} />
                      Authorize & Approve Plan
                    </button>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Section 5: Agent Execution Timeline */}
        <Card className="p-5 space-y-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Clock size={15} className="text-blue-400" />
            Agent Execution & Audit Log
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-900/60 text-slate-400 border-b border-blue-900/30 text-[11px] uppercase">
                <tr>
                  <th className="px-3 py-2">Agent Name</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Fallback Used</th>
                  <th className="px-3 py-2">Execution Latency</th>
                  <th className="px-3 py-2">Execution Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-900/20 text-slate-300">
                {execs.map((exec) => (
                  <tr key={exec.id}>
                    <td className="px-3 py-2 font-mono text-blue-300">{exec.agent_name}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] ${
                        exec.status === 'SUCCESS' ? 'bg-green-950 text-green-300 border border-green-800/50' : 'bg-red-950 text-red-300'
                      }`}>
                        {exec.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-400">
                      {exec.used_fallback ? 'Yes (Local Rules)' : 'No (Gemini AI)'}
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-300">
                      {exec.duration_ms ? `${exec.duration_ms.toFixed(1)} ms` : '—'}
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-[11px]">
                      {exec.created_at ? new Date(exec.created_at).toLocaleTimeString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
