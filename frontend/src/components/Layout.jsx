import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, ShieldCheck, History,
  User, LogOut, Zap, Menu, X, ShieldAlert
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/check',     icon: ShieldCheck,     label: 'Fraud Check' },
  { to: '/history',   icon: History,         label: 'History' },
  { to: '/awareness', icon: ShieldAlert,     label: 'Awareness' },
  { to: '/profile',   icon: User,            label: 'Profile' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const Sidebar = ({ mobile = false }) => (
    <aside className={clsx(
      'flex flex-col bg-gray-900 border-r border-white/5',
      mobile
        ? 'fixed inset-y-0 left-0 z-50 w-64 animate-slide-up'
        : 'hidden lg:flex w-64 min-h-screen sticky top-0'
    )}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
        <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center">
          <Zap size={18} className="text-white" />
        </div>
        <div>
          <div className="font-bold text-white text-sm tracking-wide">SPECTRA-UPI</div>
          <div className="text-xs text-white/40">Fraud Detection</div>
        </div>
        {mobile && (
          <button onClick={() => setMobileOpen(false)} className="ml-auto text-white/40 hover:text-white">
            <X size={20} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => mobile && setMobileOpen(false)}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
              isActive
                ? 'bg-brand-600/20 text-brand-400 border border-brand-500/20'
                : 'text-white/50 hover:text-white hover:bg-white/5'
            )}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-white/5 space-y-1">
        <div className="flex items-center gap-3 px-3 py-2.5">
          <div className="w-8 h-8 rounded-full bg-brand-600/30 flex items-center justify-center text-brand-400 text-xs font-bold">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">{user?.full_name}</div>
            <div className="text-xs text-white/40 truncate">{user?.email}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-red-400 hover:bg-red-500/10 transition-all"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  )

  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar />

      {/* Mobile overlay */}
      {mobileOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setMobileOpen(false)} />
          <Sidebar mobile />
        </>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile topbar */}
        <header className="lg:hidden flex items-center gap-4 px-4 py-4 border-b border-white/5 bg-gray-900">
          <button onClick={() => setMobileOpen(true)} className="text-white/60 hover:text-white">
            <Menu size={22} />
          </button>
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-brand-400" />
            <span className="font-bold text-sm">SPECTRA-UPI</span>
          </div>
        </header>

        <main className="flex-1 p-6 lg:p-8 animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
