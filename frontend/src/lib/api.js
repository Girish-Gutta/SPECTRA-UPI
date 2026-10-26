import axios from 'axios'

// In dev: Vite proxy forwards /api → localhost:8000
// In prod: set VITE_API_URL to your deployed backend URL (e.g. https://spectra-upi-backend.onrender.com)
const ROOT = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const API_V1 = ROOT ? `${ROOT}/api/v1` : '/api/v1'
const API_PUBLIC = ROOT ? `${ROOT}/api` : '/api'

const attachToken = (config) => {
  const token = localStorage.getItem('spectra_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}

// Authenticated app API (auth, transactions).
const api = axios.create({
  baseURL: API_V1,
  headers: { 'Content-Type': 'application/json' },
})
api.interceptors.request.use(attachToken)

// Auto-logout on 401 for the authenticated app, but never for the optional
// /auth/me refresh (which is allowed to fail quietly).
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = err.config?.url || ''
    if (err.response?.status === 401 && !url.includes('/auth/me')) {
      localStorage.removeItem('spectra_token')
      localStorage.removeItem('spectra_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Public lookup / reporting / admin / keys. Attaches a JWT when present but
// never redirects on 401: most of these endpoints are anonymous by design.
export const publicApi = axios.create({
  baseURL: API_PUBLIC,
  headers: { 'Content-Type': 'application/json' },
})
publicApi.interceptors.request.use(attachToken)

// ── Auth ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  me:       ()     => api.get('/auth/me'),
}

// ── Transactions (authenticated) ──────────────────────────────────────────
export const txAPI = {
  check:    (data)                   => api.post('/transactions/check', data),
  history:  (limit = 50, offset = 0) => api.get(`/transactions?limit=${limit}&offset=${offset}`),
  stats:    ()                       => api.get('/transactions/stats'),
  delete:   (id)                     => api.delete(`/transactions/${id}`),
  patterns: ()                       => api.get('/fraud-patterns'),
}

// ── Public scam lookup ────────────────────────────────────────────────────
export const lookupAPI = {
  lookup: (q, type = 'auto', extra = {}) =>
    publicApi.get('/lookup', { params: { q, type, ...extra } }),
}

export const reportAPI = {
  create:  (data) => publicApi.post('/reports', data),
  dispute: (data) => publicApi.post('/disputes', data),
}

export const publicContentAPI = {
  stats:     () => publicApi.get('/stats'),
  awareness: () => publicApi.get('/awareness'),
}

// ── Moderator/admin ───────────────────────────────────────────────────────
export const adminAPI = {
  reports: (status = 'pending', priority) =>
    publicApi.get('/admin/reports', { params: { status, ...(priority === undefined ? {} : { priority }) } }),
  moderate: (id, action, note = '') =>
    publicApi.patch(`/admin/reports/${id}`, { action, note }),
  disputes: (status = 'open') => publicApi.get('/admin/disputes', { params: { status } }),
  resolveDispute: (id, status = 'resolved') =>
    publicApi.patch(`/admin/disputes/${id}`, { status }),
}

// ── Developer API keys ────────────────────────────────────────────────────
export const keysAPI = {
  list:   ()         => publicApi.get('/keys'),
  create: (name)     => publicApi.post('/keys', { name }),
  revoke: (id)       => publicApi.delete(`/keys/${id}`),
}

export default api
