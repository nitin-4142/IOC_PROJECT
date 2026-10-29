import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Radio, List, Map, Package, BarChart3,
  Activity, AlertTriangle
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import ReportIncident from './pages/ReportIncident'
import IncidentList from './pages/IncidentList'
import IncidentDetail from './pages/IncidentDetail'
import IncidentMap from './pages/IncidentMap'
import ResourceInventory from './pages/ResourceInventory'
import Analytics from './pages/Analytics'
import SystemActivity from './pages/SystemActivity'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/report', icon: Radio, label: 'Report Emergency' },
  { to: '/incidents', icon: List, label: 'Incidents' },
  { to: '/map', icon: Map, label: 'Map' },
  { to: '/resources', icon: Package, label: 'Resources' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/activity', icon: Activity, label: 'System Activity' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-navy-900">
        {/* Sidebar */}
        <nav className="w-56 flex-shrink-0 bg-navy-800 border-r border-blue-900/40 flex flex-col">
          <div className="p-4 border-b border-blue-900/40">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-orange-400" size={20} />
              <div>
                <div className="text-xs font-bold text-white leading-tight">AI DISASTER</div>
                <div className="text-xs text-blue-400 leading-tight">RESPONSE COORDINATOR</div>
              </div>
            </div>
            <div className="mt-2 text-xs text-yellow-400 bg-yellow-900/20 rounded px-2 py-1">
              ⚠ DEMO SYSTEM
            </div>
          </div>
          <div className="flex-1 p-2 space-y-0.5 overflow-y-auto">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                    isActive
                      ? 'bg-blue-600/30 text-blue-300 border border-blue-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </div>
          <div className="p-3 border-t border-blue-900/40 text-xs text-slate-600">
            v0.1.0 — Decision-support prototype only. No real dispatch.
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/report" element={<ReportIncident />} />
            <Route path="/incidents" element={<IncidentList />} />
            <Route path="/incidents/:id" element={<IncidentDetail />} />
            <Route path="/map" element={<IncidentMap />} />
            <Route path="/resources" element={<ResourceInventory />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/activity" element={<SystemActivity />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
