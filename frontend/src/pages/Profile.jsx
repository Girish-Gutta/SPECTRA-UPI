import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { User, Mail, Phone, Calendar, ShieldCheck, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function Profile() {
  const { user, logout, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('info')

  const handleLogout = () => {
    logout()
    navigate('/login')
    toast.success('Logged out successfully')
  }

  const joined = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'N/A'

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Your Profile</h1>
        <p className="text-white/40 mt-1 text-sm">Manage your account information</p>
      </div>

      {/* Avatar card */}
      <div className="card flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-brand-600/30 flex items-center justify-center text-2xl font-bold text-brand-400">
          {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
        </div>
        <div>
          <div className="text-lg font-bold">{user?.full_name}</div>
          <div className="text-sm text-white/40">{user?.email}</div>
          <div className="flex items-center gap-1.5 mt-1.5">
            <ShieldCheck size={13} className="text-safe" />
            <span className="text-xs text-safe font-medium">Account Active</span>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
        {[['info', 'Account Info'], ['security', 'Security']].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === key ? 'bg-brand-600 text-white' : 'text-white/40 hover:text-white'}`}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'info' && (
        <div className="card space-y-4">
          {[
            { icon: User,     label: 'Full Name',   value: user?.full_name },
            { icon: Mail,     label: 'Email',       value: user?.email },
            { icon: Phone,    label: 'Phone',       value: user?.phone },
            { icon: Calendar, label: 'Member Since',value: joined },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center gap-4 py-3 border-b border-white/5 last:border-0">
              <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center shrink-0">
                <Icon size={16} className="text-white/40" />
              </div>
              <div>
                <div className="text-xs text-white/30 mb-0.5">{label}</div>
                <div className="text-sm font-medium">{value || '—'}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'security' && (
        <div className="card space-y-5">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-white/3 border border-white/5">
            <ShieldCheck size={20} className="text-safe shrink-0" />
            <div>
              <div className="text-sm font-medium">Password Protected</div>
              <div className="text-xs text-white/40 mt-0.5">Your password is hashed with bcrypt — never stored in plain text</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 rounded-xl bg-white/3 border border-white/5">
            <ShieldCheck size={20} className="text-safe shrink-0" />
            <div>
              <div className="text-sm font-medium">JWT Authentication</div>
              <div className="text-xs text-white/40 mt-0.5">Your session uses a signed JWT token — valid for 24 hours</div>
            </div>
          </div>
          <div className="pt-2 border-t border-white/5">
            <button onClick={handleLogout}
              className="flex items-center gap-2 text-sm font-medium text-red-400 hover:text-red-300 transition-colors">
              <LogOut size={16} /> Sign out of all sessions
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
