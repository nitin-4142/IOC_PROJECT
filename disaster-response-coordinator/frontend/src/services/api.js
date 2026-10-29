import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor for uniform errors ──────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error ||
      error.response?.data?.message ||
      error.message ||
      'Unknown error occurred'
    return Promise.reject({ message, status: error.response?.status, raw: error })
  }
)

export const api = {
  // Health
  health: () => client.get('/api/health'),

  // Incidents
  createIncident: (data) => client.post('/api/incidents', data),
  listIncidents: (params) => client.get('/api/incidents', { params }),
  getIncident: (id) => client.get(`/api/incidents/${id}`),
  updateStatus: (id, status) => client.patch(`/api/incidents/${id}/status`, { status }),
  approveIncident: (id, data) => client.post(`/api/incidents/${id}/approve`, data),
  getEvents: (id) => client.get(`/api/incidents/${id}/events`),

  // Queue
  getQueue: () => client.get('/api/queue'),

  // Resources
  getResources: () => client.get('/api/resources'),

  // Analytics
  getAnalytics: () => client.get('/api/analytics'),

  // Demo
  resetDemo: () => client.post('/api/demo/reset'),
}

export default api
