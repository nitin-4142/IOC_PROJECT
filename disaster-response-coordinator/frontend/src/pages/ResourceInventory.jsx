import React, { useState, useEffect } from 'react'
import { Package, ShieldAlert, AlertCircle, RefreshCw, Layers } from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, Spinner, ErrorState, DemoTag } from '../components/UI'

export default function ResourceInventory() {
  const [resources, setResources] = useState([])
  const [provenance, setProvenance] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchResources = async () => {
    try {
      setLoading(true)
      const res = await api.getResources()
      setResources(res.data.resources || [])
      setProvenance(res.data.data_provenance || 'DEMO_DATA')
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load resource inventory.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchResources()
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchResources} />

  return (
    <div className="pb-12">
      <PageHeader
        title="Emergency Resource Stockpile & Logistics Inventory"
        subtitle="Sample depot allocations, availability status, and provenance records"
      >
        <button
          onClick={fetchResources}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </PageHeader>

      <div className="p-6 space-y-4">
        {/* Data Provenance Warning Banner */}
        <Card className="p-4 bg-yellow-950/20 border-yellow-800/40 text-xs space-y-1">
          <div className="flex items-center gap-2 text-yellow-400 font-semibold">
            <AlertCircle size={15} />
            <span>Operational Integrity Notice: Demo Resource Provenance</span>
          </div>
          <p className="text-yellow-300/80 leading-relaxed text-[11px]">
            {provenance}
            Never assume a unit or vehicle is actually deployed or reachable without independent confirmation via local command channels.
          </p>
        </Card>

        {/* Resources Table */}
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-900/80 text-slate-400 border-b border-blue-900/30 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-4 py-3">Resource Type</th>
                  <th className="px-4 py-3">Asset Designation</th>
                  <th className="px-4 py-3">Base Location</th>
                  <th className="px-4 py-3">Total Demo Stock</th>
                  <th className="px-4 py-3">Available Demo Stock</th>
                  <th className="px-4 py-3">Availability Status</th>
                  <th className="px-4 py-3">Provenance Label</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-900/20 text-slate-300">
                {resources.map((res) => {
                  const percentAvailable = res.total_quantity > 0 
                    ? Math.round((res.available_quantity / res.total_quantity) * 100) 
                    : 0
                  return (
                    <tr key={res.id} className="hover:bg-navy-700/40 transition-colors">
                      <td className="px-4 py-3 font-semibold uppercase text-blue-300">
                        {res.resource_type.replace('_', ' ')}
                      </td>
                      <td className="px-4 py-3 text-slate-200">
                        {res.name || '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {res.base_location || '—'}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-slate-200">
                        {res.total_quantity}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-white">{res.available_quantity}</span>
                          <span className="text-[10px] text-slate-500">({percentAvailable}%)</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                          res.available_quantity > 0 
                            ? 'bg-green-950/40 text-green-300 border border-green-800/40' 
                            : 'bg-red-950/40 text-red-300 border border-red-800/40'
                        }`}>
                          {res.available_quantity > 0 ? 'DEMO_AVAILABLE' : 'DEMO_DEPLETED'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[11px] font-mono text-yellow-400/90">
                        {res.data_provenance}
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
