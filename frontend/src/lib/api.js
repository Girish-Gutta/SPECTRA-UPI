import axios from 'axios'

// In dev: Vite proxy forwards /api → localhost:8000
// In prod: set VITE_API_URL to your deployed backend URL (e.g. https://spectra-upi-backend.onrender.com)
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('spectra_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('spectra_token')
      localStorage.removeItem('spectra_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  me:       ()     => api.get('/auth/me'),
}

// ── Transactions ──────────────────────────────────────────────────────────
export const txAPI = {
  check:    (data)                   => api.post('/transactions/check', data),
  history:  (limit = 50, offset = 0) => api.get(`/transactions?limit=${limit}&offset=${offset}`),
  stats:    ()                       => api.get('/transactions/stats'),
  delete:   (id)                     => api.delete(`/transactions/${id}`),
  patterns: ()                       => api.get('/fraud-patterns'),
}

export default api
