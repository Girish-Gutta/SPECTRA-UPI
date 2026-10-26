import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, Menu, X, Zap, ScanSearch, ShieldAlert, LogOut, LogIn, Flag, Gavel, KeyRound } from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/',          label: 'Lookup',    icon: ScanSearch, end: true },
  { to: '/report',    label: 'Report',    icon: Flag },
  { to: '/dispute',   label: 'Dispute',   icon: Gavel },
  { to: '/awareness', label: 'Awareness', icon: ShieldAlert },
  { to: '/developer', label: 'API keys',  icon: KeyRound, auth: true },
  { to: '/check',     label: 'Transaction checker', icon: ShieldCheck, auth: true },
]

export default function PublicLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = () => {
    logout()
    setOpen(false)
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-gray-950/90 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 shrink-0" onClick={() => setOpen(false)}>
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <div className="font-bold tracking-wide text-sm">SPECTRA-UPI</div>
              <div className="text-[10px] text-white/40 -mt-0.5">Scam lookup</div>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-1">
            {nav.filter(item => !item.auth || user).map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) => clsx(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive ? 'text-brand-300 bg-brand-500/10' : 'text-white/55 hover:text-white hover:bg-white/5'
                )}
              >
                <Icon size={15} /> {label}
              </NavLink>
            ))}
            {user?.role && user.role !== 'user' && (
              <NavLink to="/admin" className={({ isActive }) => clsx(
                'px-3 py-2 rounded-lg text-sm font-medium',
                isActive ? 'text-amber-300 bg-amber-500/10' : 'text-white/55 hover:text-white hover:bg-white/5'
              )}>Moderation</NavLink>
            )}
          </nav>

          <div className="hidden lg:flex items-center gap-2">
            {user ? (
              <>
                <Link to="/dashboard" className="text-sm text-white/60 hover:text-white px-3 py-2">{user.full_name?.split(' ')[0] || 'Account'}</Link>
                <button onClick={handleLogout} className="btn-ghost text-sm py-2 px-3 flex items-center gap-2">
                  <LogOut size={14} /> Sign out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-ghost text-sm py-2 px-4 flex items-center gap-2"><LogIn size={14} /> Sign in</Link>
                <Link to="/register" className="btn-primary text-sm py-2 px-4">Create account</Link>
              </>
            )}
          </div>

          <button className="lg:hidden text-white/60 hover:text-white" onClick={() => setOpen(v => !v)} aria-label="Menu">
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {open && (
          <div className="lg:hidden border-t border-white/5 bg-gray-950 px-4 py-3 space-y-1">
            {nav.filter(item => !item.auth || user).map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)}
                className={({ isActive }) => clsx('flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm',
                  isActive ? 'text-brand-300 bg-brand-500/10' : 'text-white/60')}>
                <Icon size={16} /> {label}
              </NavLink>
            ))}
            {user?.role && user.role !== 'user' && (
              <Link to="/admin" onClick={() => setOpen(false)} className="block px-3 py-2.5 text-sm text-amber-300">Moderation</Link>
            )}
            <div className="pt-2 border-t border-white/5 flex gap-2">
              {user ? (
                <>
                  <Link to="/dashboard" onClick={() => setOpen(false)} className="btn-ghost flex-1 text-sm text-center py-2">Dashboard</Link>
                  <button onClick={handleLogout} className="btn-ghost flex-1 text-sm py-2">Sign out</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)} className="btn-ghost flex-1 text-sm text-center py-2">Sign in</Link>
                  <Link to="/register" onClick={() => setOpen(false)} className="btn-primary flex-1 text-sm text-center py-2">Register</Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1"><Outlet /></main>

      <footer className="border-t border-white/5 px-4 sm:px-6 py-8 mt-12">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center text-xs text-white/35">
          <div className="space-y-1">
            <div className="font-semibold text-white/50">SPECTRA-UPI · Community UPI scam lookup</div>
            <div>Open source · MIT licensed · No report found does not guarantee safety.</div>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link to="/report" className="hover:text-white/70">Report a scam</Link>
            <Link to="/dispute" className="hover:text-white/70">Dispute</Link>
            <Link to="/awareness" className="hover:text-white/70">Awareness</Link>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="hover:text-white/70">cybercrime.gov.in</a>
            <a href="tel:1930" className="hover:text-white/70">Helpline 1930</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
