import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [form, setForm]       = useState({ identifier: '', password: '' })
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors]   = useState({})

  const validate = () => {
    const e = {}
    if (!form.identifier.trim()) e.identifier = 'Email or phone is required'
    if (!form.password)          e.password    = 'Password is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await login(form.identifier.trim(), form.password)
      toast.success('Welcome back!')
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid credentials'
      toast.error(msg)
      setErrors({ password: msg })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-brand-600 items-center justify-center mb-4">
            <Zap size={26} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold">Welcome back</h1>
          <p className="text-white/40 mt-1 text-sm">Sign in to SPECTRA-UPI</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-5">
          {/* Identifier */}
          <div>
            <label className="label">Email or Phone</label>
            <input
              className={`input ${errors.identifier ? 'border-red-500' : ''}`}
              placeholder="you@example.com or +91..."
              value={form.identifier}
              onChange={(e) => { setForm(f => ({ ...f, identifier: e.target.value })); setErrors(v => ({ ...v, identifier: '' })) }}
              autoComplete="username"
            />
            {errors.identifier && <p className="text-red-400 text-xs mt-1">{errors.identifier}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="label">Password</label>
            <div className="relative">
              <input
                type={showPw ? 'text' : 'password'}
                className={`input pr-10 ${errors.password ? 'border-red-500' : ''}`}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => { setForm(f => ({ ...f, password: e.target.value })); setErrors(v => ({ ...v, password: '' })) }}
                autoComplete="current-password"
              />
              <button type="button" onClick={() => setShowPw(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password}</p>}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Signing in…
            </span> : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-sm text-white/40 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
            Create one
          </Link>
        </p>
        <p className="text-center mt-2">
          <Link to="/" className="text-xs text-white/30 hover:text-white/50">← Back to home</Link>
        </p>
      </div>
    </div>
  )
}
