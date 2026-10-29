import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'
import { MapPin, Navigation, Eye, AlertTriangle, Shield, RefreshCw } from 'lucide-react'
import api from '../services/api'
import { Card, PageHeader, SeverityBadge, Spinner, ErrorState, DemoTag } from '../components/UI'

// Create custom colored markers using SVG data URIs
function createMarkerIcon(color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="${color}" stroke="#ffffff" stroke-width="1.5"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>`
  return L.icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(svg)}`,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
    popupAnchor: [0, -28],
  })
}

const SEVERITY_ICONS = {
  CRITICAL: createMarkerIcon('#ef4444'),
  HIGH: createMarkerIcon('#f97316'),
  MEDIUM: createMarkerIcon('#eab308'),
  LOW: createMarkerIcon('#22c55e'),
  BASE: createMarkerIcon('#3b82f6'),
  SHELTER: createMarkerIcon('#a855f7'),
}

export default function IncidentMap() {
  const [incidents, setIncidents] = useState([])
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [incRes, resRes] = await Promise.all([
        api.listIncidents({ per_page: 50 }),
        api.getResources(),
      ])
      // Filter ONLY incidents with valid real coordinates
      const validIncidents = (incRes.data.incidents || []).filter(
        (i) => i.latitude != null && i.longitude != null && !isNaN(i.latitude) && !isNaN(i.longitude)
      )
      setIncidents(validIncidents)
      setResources(resRes.data.resources || [])
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load map data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={fetchData} />

  // Default center: Chennai area (coordinates of sample incidents)
  const center = [13.0827, 80.2707]

  return (
    <div className="pb-12">
      <PageHeader
        title="Tactical Geospatial Operations Map"
        subtitle="Geographic tracking for incidents with verified GPS coordinates and demo bases"
      >
        <button
          onClick={fetchData}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 text-slate-300 rounded text-xs border border-blue-900/40"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </PageHeader>

      <div className="p-6 space-y-4">
        {/* Map Legend */}
        <Card className="p-3 bg-navy-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-slate-400 font-semibold text-[11px] uppercase tracking-wide">Legend:</span>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-slate-300">Critical Incident</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-orange-500 inline-block" />
              <span className="text-slate-300">High Priority</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" />
              <span className="text-slate-300">Medium Priority</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
              <span className="text-slate-300">Demo Resource Base</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-purple-500 inline-block" />
              <span className="text-slate-300">Demo Shelter Facility</span>
            </div>
          </div>
          <div className="text-[11px] text-yellow-400 bg-yellow-900/20 px-2 py-0.5 rounded border border-yellow-800/40">
            ⚠ Only displaying coordinates with explicit confirmation. No invented GPS locations.
          </div>
        </Card>

        {/* Leaflet Map */}
        <Card className="overflow-hidden border-blue-800/50 h-[560px] relative">
          <MapContainer
            center={center}
            zoom={11}
            style={{ width: '100%', height: '100%' }}
            className="z-10"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Incident Markers */}
            {incidents.map((inc) => {
              const icon = SEVERITY_ICONS[inc.severity] || SEVERITY_ICONS.MEDIUM
              return (
                <Marker
                  key={`inc-${inc.id}`}
                  position={[inc.latitude, inc.longitude]}
                  icon={icon}
                  eventHandlers={{
                    click: () => setSelectedItem({ type: 'incident', data: inc }),
                  }}
                >
                  <Popup>
                    <div className="p-1 max-w-xs text-slate-900">
                      <div className="font-bold text-xs uppercase mb-1">{inc.incident_type} Incident</div>
                      <p className="text-[11px] text-slate-700 line-clamp-2">{inc.raw_report}</p>
                      <div className="mt-2 flex items-center justify-between text-[11px]">
                        <span className="font-semibold text-red-700">Risk: {inc.risk_score ? inc.risk_score.toFixed(1) : '—'}/100</span>
                        <Link to={`/incidents/${inc.id}`} className="text-blue-600 underline font-medium">
                          Open Dossier →
                        </Link>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              )
            })}

            {/* Resource Bases (Demo) */}
            {resources.filter(r => r.latitude && r.longitude).map((res) => {
              const isShelter = res.resource_type === 'shelter'
              const icon = isShelter ? SEVERITY_ICONS.SHELTER : SEVERITY_ICONS.BASE
              return (
                <Marker
                  key={`res-${res.id}`}
                  position={[res.latitude, res.longitude]}
                  icon={icon}
                  eventHandlers={{
                    click: () => setSelectedItem({ type: 'resource', data: res }),
                  }}
                >
                  <Popup>
                    <div className="p-1 text-slate-900">
                      <span className="bg-yellow-100 text-yellow-800 text-[10px] px-1 py-0.5 rounded font-bold">
                        DEMO RESOURCE
                      </span>
                      <div className="font-bold text-xs mt-1">{res.name || res.resource_type}</div>
                      <div className="text-[11px] text-slate-600">{res.base_location}</div>
                      <div className="text-[11px] text-blue-700 font-medium mt-1">
                        Available: {res.available_quantity} / {res.total_quantity}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              )
            })}
          </MapContainer>
        </Card>

        {/* Verified Coordinates Notice */}
        <div className="text-xs text-slate-500 text-center">
          Showing {incidents.length} incidents with confirmed geographic coordinates. Incidents submitted without latitude/longitude are omitted from the map until verified by operators.
        </div>
      </div>
    </div>
  )
}
