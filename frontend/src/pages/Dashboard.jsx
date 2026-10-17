import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { txAPI } from '../lib/api'
import {
  ShieldCheck, AlertTriangle, TrendingUp, Activity,
  ArrowRight, RefreshCw, ShieldAlert, XCircle
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import VerdictBadge from '../components/VerdictBadge'

export default function Dashboard() {
  const { user } = useAuth()
  const [txs, setTxs]       = useState([])
  const [stats, setStats]   = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      txAPI.history(100).then(r => setTxs(r.data)),
      txAPI.stats().then(r => setStats(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  const total    = stats?.total_transactions ?? txs.length
  const frauds   = stats?.fraud_count        ?? txs.filter(t => t.verdict === 'FRAUD').length
  const safe     = stats?.safe_count         ?? txs.filter(t => t.verdict === 'SAFE').length
  const suspects = stats?.suspicious_count   ?? txs.filter(t => t.verdict === 'SUSPICIOUS').length
  const atRisk   = stats?.total_amount_at_risk ?? 0

  // 7-day chart
  const last7 = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (6 - i))
    const label = d.toLocaleDateString('en-IN', { weekday: 'short' })
    const day   = d.toISOString().slice(0, 10)
    const dayTxs = txs.filter(t => new Date(t.created_at).toISOString().slice(0, 10) === day)
    return { day: label, total: dayTxs.length, fraud: dayTxs.filter(t => t.is_fraud).length }
  })

  const pieData = [
    { name: 'Safe',       value: safe,     color: '#10b981' },
    { name: 'Suspicious', value: suspects, color: '#f59e0b' },
    { name: 'Fraud',      value: frauds,   color: '#ef4444' },
  ].filter(d => d.value > 0)

  const statCards = [
    { label: 'Total Checks',      value: total,                        icon: Activity,      color: 'text-brand-400',   bg: 'bg-brand-600/10' },
    { label: 'Fraud Detected',    value: frauds,                       icon: XCircle,       color: 'text-red-400',     bg: 'bg-red-500/10' },
    { label: 'Safe Transactions', value: safe,                         icon: ShieldCheck,   color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Amount at Risk',    value: atRisk > 0 ? `₹${atRisk.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '₹0',
      icon: TrendingUp, color: 'text-red-400', bg: 'bg-red-500/10' },
  ]

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <RefreshCw size={24} className="text-brand-400 animate-spin" />
    </div>
  )

  const greeting = new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Good {greeting}, {user?.full_name?.split(' ')[0]} 👋</h1>
          <p className="text-white/40 mt-1 text-sm">Here's your fraud detection overview</p>
        </div>
        <Link to="/check" className="btn-primary flex items-center gap-2">
          <ShieldCheck size={16} /> Check Transaction
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="card">
            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-3`}>
              <Icon size={20} className={color} />
            </div>
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-sm text-white/40 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Fraud rate alert */}
      {total > 0 && frauds > 0 && (
        <div className="flex items-center gap-3 bg-red-950/30 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertTriangle size={16} className="text-red-400 shrink-0" />
          <span className="text-sm text-white/70">
            <strong className="text-red-400">{((frauds / total) * 100).toFixed(1)}%</strong> fraud rate detected across your checks.
            {stats?.top_fraud_patterns?.[0] && (
              <span> Most common pattern: <strong className="text-white">{stats.top_fraud_patterns[0].name}</strong></span>
            )}
          </span>
          <Link to="/awareness" className="ml-auto text-xs text-brand-400 hover:text-brand-300 whitespace-nowrap flex items-center gap-1">
            Learn more <ArrowRight size={12} />
          </Link>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="font-semibold mb-5 text-white/80">Activity (Last 7 Days)</h2>
          {total === 0
            ? <div className="h-48 flex items-center justify-center text-white/30 text-sm">No data yet</div>
            : <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={last7}>
                  <defs>
                    <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gFraud" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#84cc16" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#84cc16" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fill: '#a8a29e', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#a8a29e', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#1c1917', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#fff' }} />
                  <Area type="monotone" dataKey="total" stroke="#10b981" fill="url(#gTotal)" strokeWidth={2} name="Total" />
                  <Area type="monotone" dataKey="fraud" stroke="#ef4444" fill="url(#gFraud)" strokeWidth={2} name="Fraud" />
                </AreaChart>
              </ResponsiveContainer>
          }
        </div>

        <div className="card">
          <h2 className="font-semibold mb-5 text-white/80">Risk Distribution</h2>
          {total === 0
            ? <div className="h-48 flex items-center justify-center text-white/30 text-sm text-center">No checks yet</div>
            : <>
                <ResponsiveContainer width="100%" height={140}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2 mt-2">
                  {pieData.map(d => (
                    <div key={d.name} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                        <span className="text-white/60">{d.name}</span>
                      </div>
                      <span className="font-medium">{((d.value / total) * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </>
          }
        </div>
      </div>

      {/* Top fraud patterns seen */}
      {stats?.top_fraud_patterns?.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white/80 flex items-center gap-2">
              <ShieldAlert size={16} className="text-red-400" /> Fraud Patterns Detected
            </h2>
            <Link to="/awareness" className="text-sm text-brand-400 hover:text-brand-300 flex items-center gap-1">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="space-y-2">
            {stats.top_fraud_patterns.map(p => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div>
                  <div className="text-sm font-medium">{p.name}</div>
                  <div className="text-xs text-white/30">{p.id}</div>
                </div>
                <span className="text-sm font-bold text-red-400">{p.count}x detected</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent transactions */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-white/80">Recent Checks</h2>
          <Link to="/history" className="text-sm text-brand-400 hover:text-brand-300 flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        {txs.length === 0
          ? <div className="text-center py-10 text-white/30">
              <ShieldCheck size={40} className="mx-auto mb-3 opacity-30" />
              <p>No transactions checked yet.</p>
              <Link to="/check" className="text-brand-400 text-sm mt-2 inline-block">Run your first check →</Link>
            </div>
          : <div className="space-y-1">
              {txs.slice(0, 5).map(tx => (
                <div key={tx.id} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center text-xs font-bold text-white/40">
                      {tx.platform.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium text-sm">{tx.platform}</div>
                      <div className="text-xs text-white/30">
                        {tx.tx_date} · {tx.tx_time}
                        {tx.matched_pattern_name && <span className="ml-1 text-red-400"> · {tx.matched_pattern_name}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-sm">₹{tx.amount.toLocaleString('en-IN')}</span>
                    <VerdictBadge verdict={tx.verdict} />
                  </div>
                </div>
              ))}
            </div>
        }
      </div>
    </div>
  )
}
