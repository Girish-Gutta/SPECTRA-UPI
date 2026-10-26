import { useEffect, useState } from 'react'
import { ShieldAlert, ChevronDown, ChevronUp, Phone, ExternalLink, RefreshCw, Gavel } from 'lucide-react'
import { publicContentAPI } from '../lib/api'

const RISK_STYLE = {
  CRITICAL: { border: 'border-red-500/30',    bg: 'bg-red-950/20',    badge: 'bg-red-500/15 text-red-400 border-red-500/30',    dot: 'bg-red-500' },
  HIGH:     { border: 'border-orange-500/30', bg: 'bg-orange-950/20', badge: 'bg-orange-500/15 text-orange-400 border-orange-500/30', dot: 'bg-orange-500' },
  MEDIUM:   { border: 'border-amber-500/30',  bg: 'bg-amber-950/20',  badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',   dot: 'bg-amber-500' },
}

const PATTERN_ICONS = {
  'FP-001': '📱', 'FP-002': '💸', 'FP-003': '🎭', 'FP-004': '🎣',
  'FP-005': '🛒', 'FP-006': '🏦', 'FP-007': '💰', 'FP-008': '⚡'
}

function PatternCard({ pattern }) {
  const [open, setOpen] = useState(false)
  const s = RISK_STYLE[pattern.risk_level] || RISK_STYLE.MEDIUM

  return (
    <div className={`rounded-2xl border ${s.border} ${s.bg} overflow-hidden transition-all`}>
      <button className="w-full flex items-center gap-4 px-5 py-4 text-left"
        onClick={() => setOpen(v => !v)}>
        <div className="w-11 h-11 rounded-xl bg-white/5 flex items-center justify-center text-2xl flex-shrink-0">
          {PATTERN_ICONS[pattern.icon] || '⚠️'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-sm">{pattern.name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${s.badge}`}>
              {pattern.risk_level}
            </span>
            <span className="text-xs text-white/30">{pattern.id}</span>
          </div>
          <p className="text-xs text-white/50 mt-0.5 leading-relaxed line-clamp-1">{pattern.short_desc}</p>
        </div>
        {open ? <ChevronUp size={16} className="text-white/40 shrink-0" /> : <ChevronDown size={16} className="text-white/40 shrink-0" />}
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-white/5 space-y-4">
          <div className="pt-4">
            <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2">How It Works</div>
            <p className="text-sm text-white/70 leading-relaxed">{pattern.full_desc}</p>
          </div>

          {pattern.how_it_happens?.length > 0 && (
            <div>
              <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2">Step by Step</div>
              <ol className="space-y-1.5">
                {pattern.how_it_happens.map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-white/60">
                    <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i+1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {pattern.warning_signs?.length > 0 && (
            <div>
              <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2">⚠ Warning Signs</div>
              <ul className="space-y-1.5">
                {pattern.warning_signs.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                    <span className="text-amber-400 shrink-0">›</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-red-950/40 border border-red-500/20 rounded-xl p-3">
            <div className="text-xs font-bold text-red-400 mb-1">🚨 If This Happens</div>
            <p className="text-sm text-white/70">{pattern.immediate_action}</p>
          </div>

          {pattern.prevention && (
            <div className="bg-brand-950/40 border border-brand-500/20 rounded-xl p-3">
              <div className="text-xs font-bold text-brand-400 mb-1">🛡 Prevention</div>
              <p className="text-sm text-white/70">{pattern.prevention}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function FraudAwareness() {
  const [patterns, setPatterns] = useState([])
  const [laws, setLaws] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let alive = true
    publicContentAPI.awareness()
      .then(res => {
        if (!alive) return
        setPatterns(res.data.patterns || [])
        setLaws(res.data.laws || [])
      })
      .catch(() => { if (alive) setLoadError('Could not load the awareness library. Please refresh.') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const byCriticality = [...patterns].sort((a, b) => {
    const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2 }
    return (order[a.risk_level] ?? 3) - (order[b.risk_level] ?? 3)
  })

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <ShieldAlert size={24} className="text-red-400" />
          Fraud Awareness
        </h1>
        <p className="text-white/40 mt-1 text-sm">
          8 documented UPI fraud patterns from RBI/NPCI advisories — know them before you encounter them
        </p>
      </div>

      {loadError && (
        <div className="rounded-xl border border-red-500/25 bg-red-950/20 px-4 py-3 text-sm text-red-300">{loadError}</div>
      )}

      {/* Helpline banner */}
      <div className="card bg-gradient-to-r from-brand-900/30 to-amber-900/20 border-brand-500/20">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="text-xs font-bold text-brand-400 uppercase tracking-wide mb-1">Emergency Helplines</div>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <Phone size={14} className="text-emerald-400" />
                <span className="text-sm">National Cyber Helpline: <strong className="text-white">1930</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Phone size={14} className="text-brand-400" />
                <span className="text-sm">NPCI: <strong className="text-white">1800-120-1740</strong></span>
              </div>
            </div>
          </div>
          <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer"
            className="flex items-center gap-2 text-sm text-brand-400 hover:text-brand-300 btn-ghost py-2 px-4">
            <ExternalLink size={14} /> Report Cybercrime
          </a>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'CRITICAL patterns', value: patterns.filter(p => p.risk_level === 'CRITICAL').length, color: 'text-red-400' },
          { label: 'HIGH risk patterns', value: patterns.filter(p => p.risk_level === 'HIGH').length,     color: 'text-orange-400' },
          { label: 'Total patterns',     value: patterns.length,                                           color: 'text-brand-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card text-center">
            <div className={`text-3xl font-extrabold ${color}`}>{loading ? '—' : value}</div>
            <div className="text-xs text-white/40 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Pattern list */}
      {loading
        ? <div className="flex items-center justify-center h-40">
            <RefreshCw size={22} className="text-brand-400 animate-spin" />
          </div>
        : <div className="space-y-3">
            {byCriticality.map(p => <PatternCard key={p.id} pattern={p} />)}
          </div>
      }

      {/* Laws */}
      {laws.length > 0 && (
        <div className="card">
          <div className="text-sm font-bold text-brand-400 mb-3 flex items-center gap-2"><Gavel size={15} /> Legal framework</div>
          <div className="space-y-3">
            {laws.map(law => (
              <div key={law.id}>
                <div className="text-sm font-medium text-white/80">{law.act} · {law.section}</div>
                <p className="text-xs text-white/40 mt-0.5 leading-relaxed">{law.summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Golden rules */}
      <div className="card border-amber-500/20 bg-amber-950/10">
        <div className="text-sm font-bold text-amber-400 mb-3">🔑 The Golden Rules (memorize these)</div>
        <ul className="space-y-2">
          {[
            'You ONLY enter UPI PIN to SEND money — never to receive.',
            'No bank, NPCI, or government official ever asks for your OTP or PIN.',
            'Never install AnyDesk, TeamViewer, or QuickSupport for "bank support".',
            'Always check your actual bank balance — never trust screenshots.',
            'KYC is done at a bank branch — never via UPI payment or SMS link.',
          ].map((rule, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-white/70">
              <span className="text-amber-400 font-bold shrink-0">{i+1}.</span>{rule}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
