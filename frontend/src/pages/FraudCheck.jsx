import { useState, useEffect } from 'react'
import { txAPI } from '../lib/api'
import {
  ShieldCheck, AlertTriangle, XCircle, RotateCcw,
  Info, Phone, ExternalLink, ChevronDown, ChevronUp,
  Activity, User, MapPin, Smartphone, Clock, TrendingUp
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const PLATFORMS = ['Google Pay', 'PhonePe', 'Paytm', 'BHIM']

const VERDICT_CFG = {
  SAFE:       { icon: ShieldCheck,   gradient: 'from-emerald-900/40 to-emerald-950/80', border: 'border-emerald-500/30', text: 'text-emerald-400', badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: 'Transaction Appears Safe' },
  SUSPICIOUS: { icon: AlertTriangle, gradient: 'from-amber-900/40 to-amber-950/80',    border: 'border-amber-500/30',   text: 'text-amber-400',   badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',   label: 'Suspicious — Proceed with Caution' },
  FRAUD:      { icon: XCircle,       gradient: 'from-red-900/40 to-red-950/80',         border: 'border-red-500/30',     text: 'text-red-400',     badge: 'bg-red-500/15 text-red-400 border-red-500/30',         label: 'High Fraud Risk — Do Not Proceed' },
}

const RISK_COLOR = { LOW: 'bg-emerald-500', MEDIUM: 'bg-amber-500', HIGH: 'bg-red-500', CRITICAL: 'bg-red-600' }

function ScoreMeter({ score, verdict }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.65 ? '#ef4444' : score >= 0.35 ? '#f59e0b' : '#10b981'
  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-white/50">Fraud Probability</span>
        <span className="text-2xl font-extrabold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-4 bg-white/5 rounded-full overflow-hidden border border-white/5">
        <div className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}99, ${color})` }} />
      </div>
      <div className="flex justify-between text-xs text-white/20 mt-1">
        <span>0% Safe</span><span>35% Suspicious</span><span>65% Fraud</span>
      </div>
    </div>
  )
}

function FeatureBar({ label, value }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs text-white/50 w-36 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-brand-500 transition-all duration-700"
          style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-white/40 w-8 text-right">{pct}%</span>
    </div>
  )
}

function PatternCard({ result }) {
  const [open, setOpen] = useState(false)
  if (!result.matched_pattern_id) return null
  return (
    <div className="bg-red-950/30 border border-red-500/20 rounded-2xl overflow-hidden mt-4">
      <button className="w-full flex items-center justify-between px-5 py-4"
        onClick={() => setOpen(v => !v)}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
            <AlertTriangle size={16} className="text-red-400" />
          </div>
          <div className="text-left">
            <div className="text-sm font-bold text-red-300">
              Matches: {result.matched_pattern_name}
            </div>
            <div className="text-xs text-white/40">
              {result.matched_pattern_id} · {Math.round(result.pattern_similarity * 100)}% pattern match
            </div>
          </div>
        </div>
        {open ? <ChevronUp size={16} className="text-white/40" /> : <ChevronDown size={16} className="text-white/40" />}
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4 border-t border-red-500/10">
          {result.fraud_how_it_works && (
            <div>
              <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2 mt-4">How This Fraud Works</div>
              <p className="text-sm text-white/70 leading-relaxed">{result.fraud_how_it_works}</p>
            </div>
          )}
          {result.fraud_warning_signs?.length > 0 && (
            <div>
              <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2">Warning Signs</div>
              <ul className="space-y-1.5">
                {result.fraud_warning_signs.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-white/60">
                    <span className="text-amber-400 mt-0.5 shrink-0">⚠</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ActionPanel({ result }) {
  if (!result.immediate_action && !result.prevention_tip) return null
  return (
    <div className="space-y-3 mt-4">
      {result.immediate_action && (
        <div className="bg-red-950/40 border border-red-500/25 rounded-xl p-4">
          <div className="text-xs font-bold text-red-400 uppercase tracking-wide mb-2">🚨 Immediate Action</div>
          <p className="text-sm text-white/80 leading-relaxed">{result.immediate_action}</p>
        </div>
      )}
      {result.prevention_tip && (
        <div className="bg-brand-950/40 border border-brand-500/25 rounded-xl p-4">
          <div className="text-xs font-bold text-brand-400 uppercase tracking-wide mb-2">🛡 Prevention</div>
          <p className="text-sm text-white/70 leading-relaxed">{result.prevention_tip}</p>
        </div>
      )}
      {result.report_to?.length > 0 && (
        <div className="bg-white/3 border border-white/8 rounded-xl p-4">
          <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-3">Report To</div>
          <ul className="space-y-1.5">
            {result.report_to.map((r, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-white/60">
                <Phone size={12} className="text-brand-400 shrink-0" />{r}
              </li>
            ))}
          </ul>
          {result.helplines && (
            <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-3">
              <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300">
                <ExternalLink size={11} /> cybercrime.gov.in
              </a>
              <span className="text-xs text-white/40 flex items-center gap-1.5">
                <Phone size={11} className="text-emerald-400" />
                Helpline: {result.helplines.national_cyber_helpline}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function FraudCheck() {
  const today = new Date()
  const dd = `${String(today.getDate()).padStart(2,'0')}/${String(today.getMonth()+1).padStart(2,'0')}/${today.getFullYear()}`
  const hhmm = `${String(today.getHours()).padStart(2,'0')}:${String(today.getMinutes()).padStart(2,'0')}`

  const [form, setForm] = useState({
    amount: '', platform: '', tx_date: dd, tx_time: hhmm,
    location_change: false, new_recipient: true, failed_attempts: 0,
    device_count: 1, txn_freq_1h: 0, txn_freq_24h: 0,
    amount_z_score: 0.0, amount_vs_recent: 0.0, is_preferred_platform: true,
  })
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [errors, setErrors]     = useState({})
  const [showAdvanced, setShowAdvanced] = useState(false)

  const validate = () => {
    const e = {}
    if (!form.amount || isNaN(form.amount) || Number(form.amount) <= 0) e.amount = 'Enter a valid amount'
    if (!form.platform) e.platform = 'Select a platform'
    if (!form.tx_date)  e.tx_date  = 'Enter a date'
    if (!form.tx_time)  e.tx_time  = 'Enter a time'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true); setResult(null)
    try {
      const res = await txAPI.check({ ...form, amount: parseFloat(form.amount) })
      setResult(res.data)
      setTimeout(() => document.getElementById('result-anchor')?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediction failed. Is the backend running?')
    } finally { setLoading(false) }
  }

  const reset = () => { setResult(null); setForm(f => ({ ...f, amount: '', platform: '' })) }

  const cfg = result ? VERDICT_CFG[result.verdict] : null

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Fraud Check</h1>
        <p className="text-white/40 mt-1 text-sm">Behavioral ML analysis with pattern matching against 8 known UPI fraud types</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="card space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Amount (₹)</label>
            <input type="number" min="1" max="200000" step="0.01"
              className={`input ${errors.amount ? 'border-red-500' : ''}`} placeholder="e.g. 5000"
              value={form.amount}
              onChange={e => { setForm(f => ({ ...f, amount: e.target.value })); setErrors(v => ({ ...v, amount: '' })) }} />
            {errors.amount && <p className="text-red-400 text-xs mt-1">{errors.amount}</p>}
          </div>
          <div>
            <label className="label">Platform</label>
            <select className={`input ${errors.platform ? 'border-red-500' : ''}`}
              value={form.platform}
              onChange={e => { setForm(f => ({ ...f, platform: e.target.value })); setErrors(v => ({ ...v, platform: '' })) }}>
              <option value="">Select…</option>
              {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            {errors.platform && <p className="text-red-400 text-xs mt-1">{errors.platform}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Date (DD/MM/YYYY)</label>
            <input className="input" placeholder="13/09/2026" value={form.tx_date}
              onChange={e => setForm(f => ({ ...f, tx_date: e.target.value }))} />
          </div>
          <div>
            <label className="label">Time (HH:MM 24h)</label>
            <input className="input" placeholder="14:30" value={form.tx_time}
              onChange={e => setForm(f => ({ ...f, tx_time: e.target.value }))} />
          </div>
        </div>

        {/* Core context */}
        <div className="space-y-3 bg-white/2 rounded-xl p-4 border border-white/5">
          <div className="text-xs font-semibold text-white/40 uppercase tracking-wide">Risk Context</div>
          {[
            { key: 'new_recipient',   icon: User,    label: 'Sending to a new / unknown recipient' },
            { key: 'location_change', icon: MapPin,  label: 'Initiating from a different location' },
          ].map(({ key, icon: Icon, label }) => (
            <label key={key} className="flex items-center justify-between cursor-pointer group py-1">
              <div className="flex items-center gap-2">
                <Icon size={14} className="text-white/30" />
                <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">{label}</span>
              </div>
              <button type="button" onClick={() => setForm(f => ({ ...f, [key]: !f[key] }))}
                className={clsx('w-10 h-5 rounded-full transition-all relative flex-shrink-0',
                  form[key] ? 'bg-brand-600' : 'bg-white/10')}>
                <span className={clsx('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all shadow-sm',
                  form[key] ? 'left-5' : 'left-0.5')} />
              </button>
            </label>
          ))}

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div>
              <label className="label flex items-center gap-1.5"><AlertTriangle size={12} />Failed attempts</label>
              <select className="input py-2" value={form.failed_attempts}
                onChange={e => setForm(f => ({ ...f, failed_attempts: parseInt(e.target.value) }))}>
                {[0,1,2,3,4].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div>
              <label className="label flex items-center gap-1.5"><Smartphone size={12} />Devices on account</label>
              <select className="input py-2" value={form.device_count}
                onChange={e => setForm(f => ({ ...f, device_count: parseInt(e.target.value) }))}>
                {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Advanced behavioral context */}
        <button type="button" onClick={() => setShowAdvanced(v => !v)}
          className="flex items-center gap-2 text-xs text-white/40 hover:text-white/60 transition-colors">
          <Activity size={13} />
          {showAdvanced ? 'Hide' : 'Add'} behavioral context (improves accuracy)
          {showAdvanced ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>

        {showAdvanced && (
          <div className="space-y-3 bg-white/2 rounded-xl p-4 border border-white/5 animate-fade-in">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label flex items-center gap-1.5"><Clock size={12} />Txns last hour</label>
                <select className="input py-2" value={form.txn_freq_1h}
                  onChange={e => setForm(f => ({ ...f, txn_freq_1h: parseInt(e.target.value) }))}>
                  {[0,1,2,3,4,5,6].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div>
                <label className="label flex items-center gap-1.5"><TrendingUp size={12} />Txns today</label>
                <select className="input py-2" value={form.txn_freq_24h}
                  onChange={e => setForm(f => ({ ...f, txn_freq_24h: parseInt(e.target.value) }))}>
                  {[0,1,2,3,5,8,10,15].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Amount vs your usual (standard deviations above avg)</label>
              <select className="input py-2" value={form.amount_z_score}
                onChange={e => setForm(f => ({ ...f, amount_z_score: parseFloat(e.target.value) }))}>
                <option value={0}>About the same as usual (0)</option>
                <option value={1}>A bit higher than usual (1)</option>
                <option value={2}>Significantly higher (2)</option>
                <option value={3}>Much higher than usual (3)</option>
                <option value={5}>Extremely unusual amount (5)</option>
              </select>
            </div>
            <label className="flex items-center justify-between cursor-pointer group py-1">
              <span className="text-sm text-white/60 group-hover:text-white/80">Using your preferred/usual platform</span>
              <button type="button" onClick={() => setForm(f => ({ ...f, is_preferred_platform: !f.is_preferred_platform }))}
                className={clsx('w-10 h-5 rounded-full transition-all relative flex-shrink-0',
                  form.is_preferred_platform ? 'bg-brand-600' : 'bg-white/10')}>
                <span className={clsx('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all shadow-sm',
                  form.is_preferred_platform ? 'left-5' : 'left-0.5')} />
              </button>
            </label>
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-base font-bold">
          {loading
            ? <span className="flex items-center justify-center gap-2">
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing with ML + Pattern Matching…
              </span>
            : '🔍 Analyze Transaction'}
        </button>
      </form>

      {/* ── BEAST MODE RESULT ── */}
      {result && cfg && (
        <div id="result-anchor" className={`rounded-2xl border bg-gradient-to-b ${cfg.gradient} ${cfg.border} overflow-hidden animate-slide-up`}>

          {/* Header */}
          <div className="px-6 pt-6 pb-4 border-b border-white/5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                  result.verdict === 'FRAUD' ? 'bg-red-500/20' :
                  result.verdict === 'SUSPICIOUS' ? 'bg-amber-500/20' : 'bg-emerald-500/20'
                }`}>
                  <cfg.icon size={30} className={cfg.text} />
                </div>
                <div>
                  <div className={`text-xl font-extrabold ${cfg.text}`}>{cfg.label}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                      {result.risk_level} RISK
                    </span>
                    <span className="text-xs text-white/40">Transaction #{result.transaction_id}</span>
                  </div>
                </div>
              </div>
              <button onClick={reset} className="text-white/20 hover:text-white/60 transition-colors p-1">
                <RotateCcw size={18} />
              </button>
            </div>

            <ScoreMeter score={result.fraud_score} verdict={result.verdict} />

            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-3">
              {[
                ['Amount', `₹${result.amount.toLocaleString('en-IN')}`],
                ['Platform', result.platform],
                ['ML Score', `${result.fraud_score.toFixed(3)}`],
              ].map(([k, v]) => (
                <div key={k} className="bg-white/5 rounded-xl px-3 py-2.5 text-center">
                  <div className="text-xs text-white/30 mb-1">{k}</div>
                  <div className="font-semibold text-sm">{v}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="px-6 py-5 space-y-5">
            {/* Behavioral Flags */}
            {result.behavior_flags?.length > 0 && (
              <div>
                <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <Activity size={12} /> Behavioral Intelligence
                </div>
                <ul className="space-y-2">
                  {result.behavior_flags.map((f, i) => (
                    <li key={i} className="flex items-start gap-2.5 bg-white/3 rounded-xl px-3 py-2.5">
                      <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${RISK_COLOR[result.risk_level]}`} />
                      <span className="text-sm text-white/70">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Feature Contributions */}
            {result.feature_contributions && Object.keys(result.feature_contributions).length > 0 && (
              <div>
                <div className="text-xs font-bold text-white/40 uppercase tracking-wide mb-3">Risk Factor Breakdown</div>
                <div className="bg-white/3 rounded-xl px-4 py-3">
                  {Object.entries(result.feature_contributions)
                    .filter(([, v]) => v > 0)
                    .sort(([,a],[,b]) => b - a)
                    .map(([label, value]) => (
                      <FeatureBar key={label} label={label} value={value} />
                    ))}
                </div>
              </div>
            )}

            {/* Pattern Match */}
            <PatternCard result={result} />

            {/* Action Panel */}
            {result.verdict !== 'SAFE' && <ActionPanel result={result} />}

            {/* Safe message */}
            {result.verdict === 'SAFE' && (
              <div className="bg-emerald-950/30 border border-emerald-500/20 rounded-xl p-4 flex items-start gap-3">
                <ShieldCheck size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-emerald-300 mb-1">Transaction looks safe</div>
                  <p className="text-xs text-white/50 leading-relaxed">
                    No fraud patterns detected. Always stay cautious — never share your UPI PIN or OTP with anyone.
                    National Cyber Helpline: <span className="text-emerald-400 font-medium">1930</span>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
