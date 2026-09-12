import { useState } from 'react'
import { txAPI } from '../lib/api'
import { ShieldCheck, AlertTriangle, XCircle, Info, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const PLATFORMS = ['Google Pay', 'PhonePe', 'Paytm', 'BHIM']

const verdictConfig = {
  SAFE:       { icon: ShieldCheck,   color: 'text-safe',  bg: 'bg-safe/10  border-safe/20',  label: 'Transaction is SAFE' },
  SUSPICIOUS: { icon: AlertTriangle, color: 'text-warn',  bg: 'bg-warn/10  border-warn/20',  label: 'SUSPICIOUS — Proceed with caution' },
  FRAUD:      { icon: XCircle,       color: 'text-fraud', bg: 'bg-fraud/10 border-fraud/20', label: 'HIGH FRAUD RISK — Do not proceed' },
}

export default function FraudCheck() {
  const today = new Date()
  const defaultDate = `${String(today.getDate()).padStart(2,'0')}/${String(today.getMonth()+1).padStart(2,'0')}/${today.getFullYear()}`
  const defaultTime = `${String(today.getHours()).padStart(2,'0')}:${String(today.getMinutes()).padStart(2,'0')}`

  const [form, setForm] = useState({
    amount: '', platform: '', tx_date: defaultDate, tx_time: defaultTime,
    location_change: false, new_recipient: true, failed_attempts: 0, device_count: 1,
  })
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors]   = useState({})

  const validate = () => {
    const e = {}
    if (!form.amount || isNaN(form.amount) || Number(form.amount) <= 0) e.amount = 'Enter a valid amount'
    if (!form.platform)      e.platform = 'Select a platform'
    if (!form.tx_date)       e.tx_date  = 'Enter a date'
    if (!form.tx_time)       e.tx_time  = 'Enter a time'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await txAPI.check({ ...form, amount: parseFloat(form.amount) })
      setResult(res.data)
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prediction failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => { setResult(null); setForm(f => ({ ...f, amount: '', platform: '' })) }

  const cfg = result ? verdictConfig[result.verdict] : null

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Fraud Check</h1>
        <p className="text-white/40 mt-1 text-sm">Enter your transaction details to get an instant ML-powered risk score</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        {/* Amount + Platform */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Amount (₹)</label>
            <input type="number" min="1" max="200000" step="0.01"
              className={`input ${errors.amount ? 'border-red-500' : ''}`}
              placeholder="e.g. 5000"
              value={form.amount}
              onChange={e => { setForm(f => ({ ...f, amount: e.target.value })); setErrors(v => ({ ...v, amount: '' })) }}
            />
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

        {/* Date + Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Date (DD/MM/YYYY)</label>
            <input className={`input ${errors.tx_date ? 'border-red-500' : ''}`}
              placeholder="12/09/2026" value={form.tx_date}
              onChange={e => setForm(f => ({ ...f, tx_date: e.target.value }))} />
            {errors.tx_date && <p className="text-red-400 text-xs mt-1">{errors.tx_date}</p>}
          </div>
          <div>
            <label className="label">Time (HH:MM 24h)</label>
            <input className={`input ${errors.tx_time ? 'border-red-500' : ''}`}
              placeholder="14:30" value={form.tx_time}
              onChange={e => setForm(f => ({ ...f, tx_time: e.target.value }))} />
            {errors.tx_time && <p className="text-red-400 text-xs mt-1">{errors.tx_time}</p>}
          </div>
        </div>

        {/* Risk context toggles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-white/60 bg-white/3 rounded-xl p-1">
            <div className="flex items-center gap-2 px-3 py-1">
              <Info size={14} className="text-brand-400 shrink-0" />
              <span>Risk context (optional — improves accuracy)</span>
            </div>
          </div>

          {[
            { key: 'new_recipient',   label: 'Sending to a new/unknown recipient',       type: 'bool' },
            { key: 'location_change', label: 'Transaction from a different location',     type: 'bool' },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center justify-between cursor-pointer group">
              <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors">{label}</span>
              <button type="button"
                onClick={() => setForm(f => ({ ...f, [key]: !f[key] }))}
                className={clsx('w-10 h-5 rounded-full transition-all relative',
                  form[key] ? 'bg-brand-600' : 'bg-white/10')}>
                <span className={clsx('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all shadow',
                  form[key] ? 'left-5' : 'left-0.5')} />
              </button>
            </label>
          ))}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Failed attempts before this</label>
              <select className="input" value={form.failed_attempts}
                onChange={e => setForm(f => ({ ...f, failed_attempts: parseInt(e.target.value) }))}>
                {[0,1,2,3].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Devices on account</label>
              <select className="input" value={form.device_count}
                onChange={e => setForm(f => ({ ...f, device_count: parseInt(e.target.value) }))}>
                {[1,2,3,4].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full py-3">
          {loading
            ? <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing…
              </span>
            : '🔍 Analyze Transaction'}
        </button>
      </form>

      {/* Result Card */}
      {result && cfg && (
        <div className={`card border ${cfg.bg} animate-slide-up`}>
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <cfg.icon size={28} className={cfg.color} />
              <div>
                <div className={`text-lg font-bold ${cfg.color}`}>{cfg.label}</div>
                <div className="text-sm text-white/40">Transaction #{result.transaction_id}</div>
              </div>
            </div>
            <button onClick={reset} className="text-white/30 hover:text-white/60 transition-colors">
              <RotateCcw size={18} />
            </button>
          </div>

          {/* Confidence meter */}
          <div className="mb-5">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-white/50">Fraud Probability</span>
              <span className={`font-bold ${cfg.color}`}>{result.confidence_pct}%</span>
            </div>
            <div className="h-3 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${result.confidence_pct}%`,
                  background: result.confidence_pct > 65
                    ? '#ef4444' : result.confidence_pct > 35
                    ? '#f59e0b' : '#10b981'
                }} />
            </div>
            <div className="flex justify-between text-xs text-white/25 mt-1">
              <span>0% — Safe</span><span>50%</span><span>100% — Fraud</span>
            </div>
          </div>

          {/* Summary row */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            {[
              ['Amount',   `₹${result.amount.toLocaleString('en-IN')}`],
              ['Platform', result.platform],
              ['Score',    result.fraud_score.toFixed(4)],
              ['Verdict',  result.verdict],
            ].map(([k, v]) => (
              <div key={k} className="bg-white/5 rounded-xl px-4 py-3">
                <div className="text-xs text-white/40 mb-1">{k}</div>
                <div className="font-semibold text-sm">{v}</div>
              </div>
            ))}
          </div>

          {/* Risk factors */}
          {result.top_risk_factors?.length > 0 && (
            <div>
              <div className="text-sm font-medium text-white/60 mb-2">Risk Factors Detected</div>
              <ul className="space-y-2">
                {result.top_risk_factors.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <AlertTriangle size={14} className="text-warn mt-0.5 shrink-0" />
                    <span className="text-white/70">{f}</span>
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
