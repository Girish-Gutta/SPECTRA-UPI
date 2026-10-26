import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

import Landing        from './pages/Landing'
import LookupResult   from './pages/LookupResult'
import ReportPage     from './pages/ReportPage'
import DisputePage    from './pages/DisputePage'
import Login          from './pages/Login'
import Register       from './pages/Register'
import Dashboard      from './pages/Dashboard'
import FraudCheck     from './pages/FraudCheck'
import History        from './pages/History'
import Profile        from './pages/Profile'
import FraudAwareness from './pages/FraudAwareness'
import AdminPage      from './pages/AdminPage'
import ApiKeysPage    from './pages/ApiKeysPage'
import NotFound       from './pages/NotFound'
import Layout         from './components/Layout'
import PublicLayout   from './components/PublicLayout'

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  return user ? children : <Navigate to="/login" replace />
}

function RoleRoute({ roles, children }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role || 'user')) return <Navigate to="/dashboard" replace />
  return children
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/dashboard" replace /> : children
}

function ScrollToTop() {
  const { pathname, search } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname, search])
  return null
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ScrollToTop />
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#1f2937', color: '#f9fafb', border: '1px solid rgba(255,255,255,0.1)' },
            success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
          }}
        />
        <Routes>
          {/* Public lookup, reporting and awareness — no account required. */}
          <Route element={<PublicLayout />}>
            <Route path="/"          element={<Landing />} />
            <Route path="/lookup"    element={<LookupResult />} />
            <Route path="/report"    element={<ReportPage />} />
            <Route path="/dispute"   element={<DisputePage />} />
            <Route path="/awareness" element={<FraudAwareness />} />
          </Route>

          <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

          {/* Signed-in transaction tools and developer keys. */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/check"     element={<FraudCheck />} />
            <Route path="/history"   element={<History />} />
            <Route path="/profile"   element={<Profile />} />
            <Route path="/developer" element={<ApiKeysPage />} />
          </Route>

          {/* Moderator/admin only. */}
          <Route element={<RoleRoute roles={['moderator', 'admin']}><Layout /></RoleRoute>}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
