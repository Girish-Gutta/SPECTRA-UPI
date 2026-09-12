import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Register() {
  const { register } = useAuth()
  const navigate     = useNavigate()
  const [form, setForm]       = useState({ full_name: '', email: '', phone: '', password: '' })
  const [showPw, setShowPw]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors]   = useState({})

  const validate = () => {
    const e = {}
    if (!form.full_name.trim() || form.full_name.trim().length < 2)
      e.full_name = 'Enter your full name'
    if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      e.email = 'Enter a valid email'
    if (!form.phone || !/^\+?\d{7,15}$/.test(form.phone.replace(/[()\s-]/g, '')))
      e.phone = 'Enter a valid phone number'
    if (!form.password || form.password.length < 6)
      e.password = 'Password must be at least 6 characters'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await register(form)
      toast.success('Account created! Welcome to SPECTRA-UPI 🎉')
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-brand-600 items-center justify-center mb-4">
            <Zap size={26} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-white/40 mt-1 text-sm">Start detecting UPI fraud today</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {/* Full Name */}
          <div>
            <label className="label">Full Name</label>
            <input className={`input ${errors.full_name ? 'border-red-500' : ''}`}
              placeholder="Girish Gutta" value={form.full_name}
              onChange={e => { setForm(f => ({ ...f, full_name: e.target.value })); setErrors(v => ({ ...v, full_name: '' })) }} />
            {errors.full_name && <p className="text-red-400 text-xs mt-1">{errors.full_name}</p>}
          </div>

          {/* Email */}
          <div>
            <label className="label">Email Address</label>
            <input type="email" className={`input ${errors.email ? 'border-red-500' : ''}`}
              placeholder="you@example.com" value={form.email}
              onChange={e => { setForm(f => ({ ...f, email: e.target.value })); setErrors(v => ({ ...v, email: '' })) }} />
            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email}</p>}
          </div>

          {/* Phone */}
          <div>
            <label className="label">Phone Number</label>
            <input type="tel" className={`input ${errors.phone ? 'border-red-500' : ''}`}
              placeholder="+91 98765 43210" value={form.phone}
              onChange={e => { setForm(f => ({ ...f, phone: e.target.value })); setErrors(v => ({ ...v, phone: '' })) }} />
            {errors.phone && <p className="text-red-400 text-xs mt-1">{errors.phone}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="label">Password</label>
            <div className="relative">
              <input type={showPw ? 'text' : 'password'}
                className={`input pr-10 ${errors.password ? 'border-red-500' : ''}`}
                placeholder="Min. 6 characters" value={form.password}
                autoComplete="new-password"
                onChange={e => { setForm(f => ({ ...f, password: e.target.value })); setErrors(v => ({ ...v, password: '' })) }} />
              <button type="button" onClick={() => setShowPw(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password}</p>}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3 mt-2">
            {loading
              ? <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account…
                </span>
              : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-white/40 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign in</Link>
        </p>
        <p className="text-center mt-2">
          <Link to="/" className="text-xs text-white/30 hover:text-white/50">← Back to home</Link>
        </p>
      </div>
    </div>
  )
}
