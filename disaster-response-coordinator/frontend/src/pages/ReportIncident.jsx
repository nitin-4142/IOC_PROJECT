import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  AlertTriangle, Send, CheckCircle2, XCircle, 
  Clock, ShieldAlert, Cpu, ArrowRight, Info 
} from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader } from '../components/UI'

const SAMPLE_REPORTS = [
  {
    label: 'Chennai Flood (Standard)',
    text: 'Severe flooding near Anna Nagar Bridge in Chennai. Approximately 150 people are stranded on rooftops. The water level is rising, and several elderly people need medical assistance.',
    location: 'Anna Nagar Bridge, Chennai',
    lat: '13.0878',
    lng: '80.2085',
  },
  {
    label: 'Coimbatore Earthquake',
    text: 'Major earthquake magnitude 6.5 reported in Coimbatore district. Multiple residential buildings have collapsed in the Gandhipuram area. At least 80 people are injured and 30 are missing. Rescue teams needed urgently.',
    location: 'Gandhipuram, Coimbatore',
    lat: '11.0168',
    lng: '76.9558',
  },
  {
    label: 'Manali Chemical Fire',
    text: 'Large fire broke out at a chemical storage facility near Manali industrial area, Chennai. Thick black smoke visible for kilometres. Workers trapped inside. Fire is spreading to adjacent buildings.',
    location: 'Manali Industrial Area, Chennai',
    lat: '13.1667',
    lng: '80.2500',
  },
]

const AGENTS = [
  { id: 'intelligence_agent', name: 'Agent 1: Emergency Intelligence', desc: 'Disaster categorization, entity extraction, fact & missing info detection' },
  { id: 'risk_agent', name: 'Agent 2: Risk Assessment', desc: 'Deterministic transparent scoring (0-100), severity classification, rationale' },
  { id: 'resource_agent', name: 'Agent 3: Resource Planning', desc: 'Playbook matching, population scaling, demo inventory availability check' },
  { id: 'logistics_agent', name: 'Agent 4: Logistics & Routing', desc: 'Coordinates validation, base routes estimation, shelter/hospital discovery' },
  { id: 'coordination_agent', name: 'Agent 5: Coordination & Monitoring', desc: 'Response plan synthesis, conflict checking, follow-up generation, audit log' },
]

export default function ReportIncident() {
  const navigate = useNavigate()
  const [report, setReport] = useState('')
  const [locationText, setLocationText] = useState('')
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [agentProgress, setAgentProgress] = useState(null)
  const [createdIncidentId, setCreatedIncidentId] = useState(null)

  const handleApplySample = (sample) => {
    setReport(sample.text)
    setLocationText(sample.location)
    setLatitude(sample.lat)
    setLongitude(sample.lng)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!report.trim() || report.trim().length < 10) {
      setError('Emergency report must be at least 10 characters long.')
      return
    }

    setSubmitting(true)
    setError(null)
    setAgentProgress({
      intelligence_agent: 'running',
      risk_agent: 'pending',
      resource_agent: 'pending',
      logistics_agent: 'pending',
      coordination_agent: 'pending',
    })

    const payload = {
      raw_report: report.trim(),
      location_text: locationText.trim() || undefined,
      latitude: latitude ? parseFloat(latitude) : undefined,
      longitude: longitude ? parseFloat(longitude) : undefined,
      is_demo: true,
    }

    try {
      const response = await api.createIncident(payload)
      const data = response.data

      // Extract real backend agent execution results
      const results = data.agent_results || {}
      setAgentProgress({
        intelligence_agent: results.intelligence_agent?.status === 'SUCCESS' ? 'success' : 'failed',
        risk_agent: results.risk_agent?.status === 'SUCCESS' ? 'success' : 'failed',
        resource_agent: results.resource_agent?.status === 'SUCCESS' ? 'success' : 'failed',
        logistics_agent: results.logistics_agent?.status === 'SUCCESS' ? 'success' : 'failed',
        coordination_agent: results.coordination_agent?.status === 'SUCCESS' ? 'success' : 'failed',
      })

      if (data.incident_id) {
        setCreatedIncidentId(data.incident_id)
      } else {
        setError(data.error || 'Incident was not assigned an ID.')
      }
    } catch (err) {
      setError(err.message || 'Workflow execution failed. Verify backend service is running.')
      setAgentProgress({
        intelligence_agent: 'failed',
        risk_agent: 'failed',
        resource_agent: 'failed',
        logistics_agent: 'failed',
        coordination_agent: 'failed',
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="pb-12">
      <PageHeader
        title="Submit Emergency Incident Report"
        subtitle="Unstructured intake processed through five synchronized decision-support AI agents"
      />

      <div className="p-6 max-w-4xl space-y-6">
        {/* Sample Presets */}
        <Card className="p-4 border-dashed border-blue-800/60 bg-navy-800/50">
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-blue-400" />
            <span className="text-xs font-semibold text-slate-300">Quick Test Scenarios:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_REPORTS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplySample(sample)}
                className="text-xs px-2.5 py-1 bg-navy-700 hover:bg-navy-600 text-blue-300 rounded border border-blue-900/40 transition-colors"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </Card>

        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-xs text-red-300 flex items-center gap-2">
            <XCircle size={15} className="flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Card className="p-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wide mb-1.5">
                Unstructured Emergency Report *
              </label>
              <textarea
                value={report}
                onChange={(e) => setReport(e.target.value)}
                placeholder="Describe the situation, affected people, visible hazards, injuries, road access, and urgent needs..."
                rows={5}
                required
                className="w-full bg-navy-900 border border-blue-900/50 rounded p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Provide as much raw context as possible. Minimum 10 characters.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Location Text (Optional)
                </label>
                <input
                  type="text"
                  value={locationText}
                  onChange={(e) => setLocationText(e.target.value)}
                  placeholder="e.g. Anna Nagar Bridge"
                  className="w-full bg-navy-900 border border-blue-900/50 rounded px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Latitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="e.g. 13.0878"
                  className="w-full bg-navy-900 border border-blue-900/50 rounded px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Longitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="e.g. 80.2085"
                  className="w-full bg-navy-900 border border-blue-900/50 rounded px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <Cpu size={13} className="text-blue-400" />
                <span>Runs sequential 5-agent multi-agent pipeline with deterministic fallbacks</span>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded text-xs font-semibold tracking-wide transition-colors"
              >
                {submitting ? (
                  <>
                    <Clock size={14} className="animate-spin" />
                    Executing Agents...
                  </>
                ) : (
                  <>
                    <Send size={14} />
                    Run Multi-Agent Pipeline
                  </>
                )}
              </button>
            </div>
          </Card>
        </form>

        {/* 5-Agent Execution Pipeline Monitor */}
        <Card className="p-5">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldAlert size={15} className="text-blue-400" />
            Five-Agent Execution Pipeline
          </h2>

          <div className="space-y-3">
            {AGENTS.map((agent, idx) => {
              const status = agentProgress ? agentProgress[agent.id] : 'idle'
              return (
                <div
                  key={agent.id}
                  className={`p-3 rounded border transition-colors ${
                    status === 'running'
                      ? 'bg-blue-900/20 border-blue-600'
                      : status === 'success'
                      ? 'bg-green-950/20 border-green-800/60'
                      : status === 'failed'
                      ? 'bg-red-950/20 border-red-800/60'
                      : 'bg-navy-900/40 border-blue-900/20 text-slate-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="text-[11px] font-mono text-slate-400 w-4">{idx + 1}.</span>
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{agent.name}</div>
                        <div className="text-[11px] text-slate-400">{agent.desc}</div>
                      </div>
                    </div>
                    <div>
                      {status === 'running' && (
                        <span className="flex items-center gap-1.5 text-xs text-blue-400">
                          <Clock size={13} className="animate-spin" /> Processing
                        </span>
                      )}
                      {status === 'success' && (
                        <span className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
                          <CheckCircle2 size={13} /> Completed
                        </span>
                      )}
                      {status === 'failed' && (
                        <span className="flex items-center gap-1.5 text-xs text-red-400 font-medium">
                          <XCircle size={13} /> Error / Fallback
                        </span>
                      )}
                      {status === 'pending' && (
                        <span className="text-xs text-slate-500">Queued</span>
                      )}
                      {status === 'idle' && (
                        <span className="text-xs text-slate-600">Standby</span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {createdIncidentId && (
            <div className="mt-5 p-4 bg-blue-950/40 border border-blue-700/50 rounded-lg flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-blue-300">
                  ✓ Pipeline completed! Incident Registered:
                </p>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">{createdIncidentId}</p>
              </div>
              <button
                onClick={() => navigate(`/incidents/${createdIncidentId}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors"
              >
                View Incident Dossier <ArrowRight size={13} />
              </button>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
