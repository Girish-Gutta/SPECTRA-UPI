import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Rehydrate from localStorage on app load, then refresh the profile so an
  // existing session picks up a newly granted moderator/admin role.
  useEffect(() => {
    const token = localStorage.getItem('spectra_token')
    const saved = localStorage.getItem('spectra_user')
    if (token && saved) {
      try { setUser(JSON.parse(saved)) } catch {}
    }
    setLoading(false)

    if (token) {
      authAPI.me()
        .then(res => {
          const updated = { ...(saved ? JSON.parse(saved) : {}), ...res.data }
          localStorage.setItem('spectra_user', JSON.stringify(updated))
          setUser(updated)
        })
        .catch(() => { /* offline or expired: keep the cached session */ })
    }
  }, [])

  const login = async (identifier, password) => {
    const res = await authAPI.login({ identifier, password })
    const { access_token, ...userData } = res.data
    localStorage.setItem('spectra_token', access_token)
    localStorage.setItem('spectra_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const register = async (formData) => {
    const res = await authAPI.register(formData)
    const { access_token, ...userData } = res.data
    localStorage.setItem('spectra_token', access_token)
    localStorage.setItem('spectra_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = () => {
    localStorage.removeItem('spectra_token')
    localStorage.removeItem('spectra_user')
    setUser(null)
  }

  const refreshUser = async () => {
    const res = await authAPI.me()
    const updated = { ...user, ...res.data }
    localStorage.setItem('spectra_user', JSON.stringify(updated))
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
