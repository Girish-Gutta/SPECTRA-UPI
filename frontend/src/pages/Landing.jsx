import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Search, ScanLine, ShieldAlert, ArrowRight, AlertTriangle, CheckCircle2,
  Users, FileCheck2, Database, Sparkles, ExternalLink,
} from 'lucide-react'
import { publicContentAPI } from '../lib/api'
import QrScanner from '../components/QrScanner'

const DEMO_VALUES = [
  { value: 'demo.kyc-alert@exampleupi', label: 'verified demo UPI' },
  { value: 'demo.collect@exampleupi', label: 'pending demo UPI' },
]

const TYPE_OPTIONS = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'upi_id', label: 'UPI ID' },
  { value: 'url', label: 'Link / URL' },
  { value: 'phone', label: 'Phone number' },
]

function Stat({ icon: Icon, value, label, loading }) {
  return (
    <div className="card text-center py-5">
      <Icon size={17} className="text-brand-400 mx-auto mb-2" />
      <div className="text-2xl font-extrabold text-white">{loading ? '—' : value}</div>
      <div className="text-[11px] text-white/40 mt-1">{label}</div>
    </div>
  )
}

export default function Landing() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [type, setType] = useState('auto')
  const [scannerOpen, setScannerOpen] = useState(false)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  useEffect(() => {
    let alive = true
    publicContentAPI.stats()
      .then(res => { if (alive) setStats(res.data) })
      .catch(() => {})
      .finally(() => { if (alive) setStatsLoading(false) })
    return () => { alive = false }
  }, [])

  const runLookup = (value = query, selectedType = type) => {
    const clean = value.trim()
    if (clean.length < 2) return
    navigate(`/lookup?q=${encodeURIComponent(clean)}&type=${encodeURIComponent(selectedType)}`)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    runLookup()
  }

  const handleDecoded = (text) => {
    setQuery(text)
    runLookup(text, 'auto')
  }

  const topTypes = stats?.top_scam_types_this_month ?? []

  return (
    <div className="animate-fade-in">
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pt-14 sm:pt-20 pb-10 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-600/10 border border-brand-500/20 text-brand-300 text-xs font-semibold mb-6">
          <Sparkles size={13} /> Free community lookup · No login needed
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold leading-tight tracking-tight">
          Check before you pay.
          <br />
          <span className="bg-gradient-to-r from-brand-300 via-emerald-300 to-amber-300 bg-clip-text text-transparent">
            Look up a UPI scam.
          </span>
        </h1>
        <p className="text-base sm:text-lg text-white/50 max-w-2xl mx-auto mt-6 leading-relaxed">
          Search a UPI ID, payment link, phone number or QR payload against community reports.
          Moderators verify reports before they can raise a red flag.
        </p>

        <form onSubmit={handleSubmit} className="card mt-9 text-left border-white/10 bg-gray-900/60">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
              <input
                value={query}
                onChange={event => setQuery(event.target.value)}
                className="input pl-11"
                placeholder="e.g. name@bank, https://site.example/pay, +919876543210"
                aria-label="UPI ID, link, phone number or QR payload"
                autoComplete="off"
              />
            </div>
            <div className="flex gap-3">
              <select value={type} onChange={event => setType(event.target.value)} className="input lg:w-40" aria-label="Identifier type">
                {TYPE_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
              <button type="submit" disabled={query.trim().length < 2} className="btn-primary flex items-center gap-2 shrink-0">
                Check <ArrowRight size={16} />
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 mt-3">
            <button type="button" onClick={() => setScannerOpen(true)} className="btn-ghost text-xs py-2 px-3 flex items-center gap-2">
              <ScanLine size={14} /> Scan a QR code instead
            </button>
            <span className="text-[11px] text-white/30 hidden sm:inline">No sign-up. No payment. Your search is not tied to your account.</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-white/5">
            <span className="text-[11px] text-white/30">Try demo data:</span>
            {DEMO_VALUES.map(item => (
              <button
                key={item.value}
                type="button"
                onClick={() => { setQuery(item.value); runLookup(item.value, 'auto') }}
                className="text-[11px] px-2.5 py-1.5 rounded-lg border border-white/10 bg-white/5 text-white/55 hover:text-white hover:border-brand-500/30 transition-colors"
                title={item.label}
              >
                {item.value}
              </button>
            ))}
          </div>
        </form>
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Stat icon={FileCheck2} value={(stats?.total_verified_reports ?? 0).toLocaleString('en-IN')} label="Verified reports" loading={statsLoading} />
          <Stat icon={ShieldAlert} value={(stats?.total_reported_entities ?? 0).toLocaleString('en-IN')} label="Reported identifiers" loading={statsLoading} />
          <Stat icon={Database} value={(stats?.total_entities ?? 0).toLocaleString('en-IN')} label="Identifiers checked" loading={statsLoading} />
          <Stat icon={Users} value={(stats?.top_scam_types_this_month?.[0]?.title ?? '—')} label="Top scam type this month" loading={statsLoading} />
        </div>
        {topTypes.length > 0 && (
          <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
            {topTypes.map(item => (
              <span key={item.code} className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/45">
                {item.title} · {item.count}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-14">
        <h2 className="text-xl font-bold text-center mb-6">How the lookup works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              icon: Search,
              title: '1. Search an identifier',
              text: 'Paste a UPI ID, link, phone number or UPI QR payload. We normalize it so small formatting tricks do not hide a repeat offender.',
            },
            {
              icon: ShieldAlert,
              title: '2. See what the community reported',
              text: 'Only moderator-verified reports can produce HIGH RISK. Pending reports contribute at most SUSPICIOUS and are never published as fact.',
            },
            {
              icon: CheckCircle2,
              title: '3. Decide, with context',
              text: 'Read the signals, scam type, prevention steps and official helplines. Then verify through your bank before sending money.',
            },
          ].map(({ icon: Icon, title, text }) => (
            <div key={title} className="card">
              <div className="w-10 h-10 rounded-xl bg-brand-600/15 flex items-center justify-center mb-4">
                <Icon size={19} className="text-brand-400" />
              </div>
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-14">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card border-amber-500/20 bg-amber-950/10">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={18} className="text-amber-400" />
              <h2 className="font-semibold">What a lookup cannot tell you</h2>
            </div>
            <ul className="space-y-2.5 text-sm text-white/60">
              <li>No reports found does <strong className="text-white/85">not</strong> mean an identifier is safe.</li>
              <li>A report is one user's allegation, not a criminal finding or court order.</li>
              <li>New scam identifiers appear every day and may not be listed yet.</li>
              <li>Never share your UPI PIN or OTP with anyone, including someone who claims to be from a bank.</li>
            </ul>
          </div>

          <div className="card border-brand-500/15">
            <div className="flex items-center gap-2 mb-3">
              <ShieldAlert size={18} className="text-brand-400" />
              <h2 className="font-semibold">Help keep the list useful</h2>
            </div>
            <p className="text-sm text-white/50 leading-relaxed mb-5">
              Lost money or received a suspicious request? File a report. If you are the owner of a listed
              identifier and believe it is wrong, open a dispute. Both are free and do not require an account.
            </p>
            <div className="flex flex-wrap gap-2">
              <Link to="/report" className="btn-primary text-sm flex items-center gap-2">Report a scam <ArrowRight size={15} /></Link>
              <Link to="/dispute" className="btn-ghost text-sm">Dispute a listing</Link>
              <Link to="/awareness" className="btn-ghost text-sm">Learn the patterns</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16">
        <div className="card text-center bg-gradient-to-br from-brand-900/40 to-amber-900/10 border-brand-500/20">
          <h2 className="text-2xl font-bold mb-2">Already lost money?</h2>
          <p className="text-sm text-white/50 mb-6 max-w-xl mx-auto">
            Call the national cyber helpline <a href="tel:1930" className="text-white font-semibold hover:text-brand-300">1930</a> and
            report at <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="text-white font-semibold hover:text-brand-300">cybercrime.gov.in</a>.
            Report to your bank immediately — early reporting improves the chance of a hold.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <a href="tel:1930" className="btn-primary text-sm">Call 1930</a>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="btn-ghost text-sm flex items-center gap-2">
              File a cybercrime complaint <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </section>

      <QrScanner open={scannerOpen} onClose={() => setScannerOpen(false)} onDecode={handleDecoded} />
    </div>
  )
}
