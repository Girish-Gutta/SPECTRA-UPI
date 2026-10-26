import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft, ArrowRight, AlertTriangle, CheckCircle2, Copy, Check,
  ExternalLink, FileWarning, Flag, Gavel, LifeBuoy, Loader2, Phone,
  Search, ShieldAlert, ShieldQuestion, Clock3, Info,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { lookupAPI } from '../lib/api'
import LookupBadge from '../components/LookupBadge'

const TYPE_LABEL = {
  upi_id: 'UPI ID',
  url: 'Link / URL',
  phone: 'Phone number',
  qr_payload: 'QR payload',
}

const SEVERITY_STYLE = {
  high: 'border-red-500/25 bg-red-950/20 text-red-300',
  medium: 'border-amber-500/25 bg-amber-950/15 text-amber-300',
  low: 'border-sky-500/20 bg-sky-950/15 text-sky-300',
  info: 'border-white/10 bg-white/[0.03] text-white/55',
}

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message).filter(Boolean).join(' ')
  if (err?.message === 'Network Error') return 'Could not reach the lookup service. Check your connection.'
  return 'The lookup failed. Please try again.'
}

function formatCurrency(value) {
  if (!value) return '—'
  return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function LoadingState() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-4">
      <div className="card animate-pulse">
        <div className="h-6 w-56 bg-white/10 rounded mb-4" />
        <div className="h-4 w-full bg-white/5 rounded mb-2" />
        <div className="h-4 w-2/3 bg-white/5 rounded" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[0, 1, 2, 3].map(item => <div key={item} className="card h-24 animate-pulse" />)}
      </div>
      <div className="card h-40 animate-pulse" />
    </div>
  )
}

export default function LookupResult() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const q = (params.get('q') || '').trim()
  const type = params.get('type') || 'auto'

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(Boolean(q))
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [newQuery, setNewQuery] = useState(q)

  useEffect(() => {
    setNewQuery(q)
    if (q.length < 2) {
      setData(null)
      setError('')
      setLoading(false)
      return
    }

    let alive = true
    setLoading(true)
    setError('')
    setData(null)

    lookupAPI.lookup(q, type)
      .then(res => { if (alive) setData(res.data) })
      .catch(err => { if (alive) setError(apiError(err)) })
      .finally(() => { if (alive) setLoading(false) })

    return () => { alive = false }
  }, [q, type])

  const copyValue = async (value) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      toast.success('Copied')
      setTimeout(() => setCopied(false), 1800)
    } catch {
      toast.error('Could not copy. Select the text manually.')
    }
  }

  const submitSearch = (event) => {
    event.preventDefault()
    const clean = newQuery.trim()
    if (clean.length < 2) return
    navigate(`/lookup?q=${encodeURIComponent(clean)}&type=auto`)
  }

  if (!q || q.length < 2) {
    return (
      <div className="max-w-xl mx-auto px-4 sm:px-6 py-20 text-center">
        <ShieldQuestion size={40} className="text-white/20 mx-auto mb-4" />
        <h1 className="text-2xl font-bold mb-2">Nothing to look up yet</h1>
        <p className="text-sm text-white/45 mb-6">Search a UPI ID, payment link, phone number or QR payload from the home page.</p>
        <Link to="/" className="btn-primary inline-flex items-center gap-2"><Search size={15} /> Go to lookup</Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <Link to="/" className="text-sm text-white/45 hover:text-white flex items-center gap-2">
          <ArrowLeft size={15} /> New lookup
        </Link>
        <div className="flex gap-2">
          <Link to={`/report?q=${encodeURIComponent(q)}`} className="btn-ghost text-sm py-2 px-3 flex items-center gap-2">
            <Flag size={14} /> Report
          </Link>
          <Link to={`/dispute?q=${encodeURIComponent(q)}`} className="btn-ghost text-sm py-2 px-3 flex items-center gap-2">
            <Gavel size={14} /> Dispute
          </Link>
        </div>
      </div>

      <form onSubmit={submitSearch} className="flex flex-col sm:flex-row gap-2 mb-6">
        <input
          value={newQuery}
          onChange={event => setNewQuery(event.target.value)}
          className="input flex-1"
          placeholder="Check another UPI ID, link, phone or QR payload"
          aria-label="Check another identifier"
        />
        <button type="submit" className="btn-primary flex items-center justify-center gap-2">
          <Search size={15} /> Check
        </button>
      </form>

      {loading && <LoadingState />}

      {!loading && error && (
        <div className="card border-red-500/20 bg-red-950/10 text-center py-12">
          <FileWarning size={30} className="text-red-400 mx-auto mb-3" />
          <h2 className="font-semibold mb-2">Could not complete this lookup</h2>
          <p className="text-sm text-white/50 max-w-md mx-auto">{error}</p>
          <p className="text-xs text-white/30 mt-4">Check the format and try again. For a UPI ID use <code>name@bank</code>.</p>
        </div>
      )}

      {!loading && !error && data && (
        <div className="space-y-5">
          {data.demo_data && (
            <div className="rounded-xl border border-sky-500/25 bg-sky-950/20 px-4 py-3 text-xs text-sky-300 flex items-start gap-2">
              <Info size={15} className="mt-0.5 shrink-0" />
              This record is seeded demo data for demonstrations. Do not treat it as a real report about a real person.
            </div>
          )}

          <section className="card">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <LookupBadge verdict={data.verdict} size="lg" />
                <h1 className="text-xl sm:text-2xl font-bold mt-3">{data.verdict_label}</h1>
                <p className="text-sm text-white/45 mt-1">
                  {data.verdict === 'HIGH_RISK' && 'At least one moderator-verified community report exists for this identifier.'}
                  {data.verdict === 'SUSPICIOUS' && 'No verified report yet, but something about this identifier or how it was shared raised a flag.'}
                  {data.verdict === 'NO_REPORTS' && 'Nothing in our community database matches this identifier. That is not proof of safety.'}
                </p>
              </div>
              <div className="text-right">
                <div className="text-[11px] uppercase tracking-wide text-white/30">Checked</div>
                <div className="text-xs text-white/50">{formatDate(data.checked_at)}</div>
              </div>
            </div>

            <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-[11px] uppercase tracking-wide text-white/30 mb-1">
                    {TYPE_LABEL[data.query.detected_type] || data.query.detected_type}
                  </div>
                  <div className="font-mono text-sm sm:text-base text-white break-all">{data.query.normalized_value}</div>
                  <div className="text-[11px] text-white/30 mt-1">Public lists show this as {data.query.masked_value}</div>
                </div>
                <button onClick={() => copyValue(data.query.normalized_value)} className="btn-ghost text-xs py-2 px-3 flex items-center gap-2 shrink-0">
                  {copied ? <Check size={13} /> : <Copy size={13} />} {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-amber-500/25 bg-amber-950/15 px-4 py-3 flex items-start gap-2.5">
              <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
              <p className="text-sm text-amber-100/85 leading-relaxed">{data.safety_note}</p>
            </div>
          </section>

          <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Verified reports', value: data.report_summary.verified_count, accent: 'text-red-300' },
              { label: 'Pending review', value: data.report_summary.pending_count, accent: 'text-amber-300' },
              { label: 'Total reports', value: data.report_summary.total_count, accent: 'text-white' },
              { label: 'Reported loss', value: formatCurrency(data.report_summary.total_reported_loss), accent: 'text-white' },
            ].map(item => (
              <div key={item.label} className="card text-center py-4">
                <div className={`text-2xl font-extrabold ${item.accent}`}>{item.value}</div>
                <div className="text-[11px] text-white/40 mt-1">{item.label}</div>
              </div>
            ))}
          </section>

          {data.incident_summary && (
            <section className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-3"><Info size={17} className="text-brand-400" /> What the reports say</h2>
              <p className="text-sm text-white/60 leading-relaxed whitespace-pre-line">{data.incident_summary}</p>
            </section>
          )}

          {data.signals?.length > 0 && (
            <section className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-4"><ShieldAlert size={17} className="text-brand-400" /> Signals</h2>
              <div className="space-y-2.5">
                {data.signals.map(signal => (
                  <div key={`${signal.source}-${signal.code}`} className={`rounded-xl border px-4 py-3 ${SEVERITY_STYLE[signal.severity] || SEVERITY_STYLE.info}`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold">{signal.label}</span>
                      <span className="text-[10px] uppercase tracking-wide opacity-60">{signal.source} · {signal.severity}</span>
                    </div>
                    <p className="text-xs opacity-75 mt-1 leading-relaxed">{signal.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {data.why_risky?.length > 0 && (
            <section className="card">
              <h2 className="font-semibold flex items-center gap-2 mb-3"><AlertTriangle size={17} className="text-amber-400" /> Why this flag was raised</h2>
              <ul className="space-y-2">
                {data.why_risky.map((reason, index) => (
                  <li key={index} className="flex items-start gap-2.5 text-sm text-white/60">
                    <span className="text-amber-400 mt-0.5">›</span> {reason}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {data.verdict === 'NO_REPORTS' && (
            <section className="card border-white/10">
              <h2 className="font-semibold flex items-center gap-2 mb-2"><CheckCircle2 size={17} className="text-white/40" /> No reports found in our database</h2>
              <p className="text-sm text-white/50 leading-relaxed">
                This identifier may be new, may be legitimate, or may simply not have been reported yet.
                Verify the payee name in your UPI app, confirm the purpose of the payment, and start with a small test transfer if you are unsure.
              </p>
            </section>
          )}

          {(data.what_to_do?.not_paid?.length > 0 || data.what_to_do?.already_paid?.length > 0) && (
            <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card border-amber-500/15">
                <h2 className="font-semibold flex items-center gap-2 mb-3"><Clock3 size={17} className="text-amber-400" /> If you have not paid yet</h2>
                <ul className="space-y-2">
                  {data.what_to_do.not_paid.map((item, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-white/60"><span className="text-amber-400">•</span>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="card border-red-500/15">
                <h2 className="font-semibold flex items-center gap-2 mb-3"><LifeBuoy size={17} className="text-red-400" /> If you already paid</h2>
                <ul className="space-y-2">
                  {data.what_to_do.already_paid.map((item, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-white/60"><span className="text-red-400">•</span>{item}</li>
                  ))}
                </ul>
              </div>
            </section>
          )}

          {data.scam_types?.length > 0 && (
            <section className="space-y-3">
              <h2 className="font-semibold px-1">Reported scam patterns</h2>
              {data.scam_types.map(item => (
                <div key={item.code} className="card">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <h3 className="font-semibold">{item.title}</h3>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-white/45">
                      {item.report_count} verified report{item.report_count === 1 ? '' : 's'}
                    </span>
                  </div>
                  {item.explanation && <p className="text-sm text-white/55 leading-relaxed">{item.explanation}</p>}
                  {item.how_it_works && <p className="text-sm text-white/40 leading-relaxed mt-2">{item.how_it_works}</p>}
                  {item.prevention_steps?.length > 0 && (
                    <ul className="mt-3 space-y-1.5">
                      {item.prevention_steps.map((step, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm text-white/55"><span className="text-brand-400">✓</span>{step}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </section>
          )}

          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.laws?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold flex items-center gap-2 mb-3"><Gavel size={17} className="text-brand-400" /> Relevant law</h2>
                <div className="space-y-3">
                  {data.laws.map(law => (
                    <div key={law.id}>
                      <div className="text-sm font-medium text-white/80">{law.act} · {law.section}</div>
                      <p className="text-xs text-white/40 mt-0.5 leading-relaxed">{law.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.helplines?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold flex items-center gap-2 mb-3"><Phone size={17} className="text-brand-400" /> Help and reporting</h2>
                <div className="space-y-3">
                  {data.helplines.map(line => (
                    <div key={line.id}>
                      <div className="text-sm font-medium text-white/80">{line.name}</div>
                      <div className="flex flex-wrap gap-3 mt-0.5">
                        {line.number && <a href={`tel:${line.number.replace(/[^\d+]/g, '')}`} className="text-xs text-brand-300 hover:text-brand-200">{line.number}</a>}
                        {line.url && <a href={line.url} target="_blank" rel="noreferrer" className="text-xs text-brand-300 hover:text-brand-200 inline-flex items-center gap-1">Website <ExternalLink size={11} /></a>}
                      </div>
                      {line.description && <p className="text-[11px] text-white/30 mt-0.5">{line.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {data.timeline?.length > 0 && (
            <section className="card">
              <h2 className="font-semibold mb-3">Verified report timeline</h2>
              <div className="space-y-2">
                {data.timeline.map((item, index) => (
                  <div key={index} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
                    <div className="flex items-center gap-2 text-sm">
                      <Clock3 size={13} className="text-white/30" />
                      <span className="text-white/55">{formatDate(item.date)}</span>
                      <span className="text-white/75">{item.scam_type_title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {item.is_demo && <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">demo</span>}
                      <span className="text-xs text-white/45">{formatCurrency(item.amount_lost)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="card text-center">
            <h2 className="font-semibold mb-1">Know something about this identifier?</h2>
            <p className="text-sm text-white/40 mb-4">Reports and disputes are free, anonymous by default, and reviewed by moderators.</p>
            <div className="flex flex-wrap justify-center gap-2">
              <Link to={`/report?q=${encodeURIComponent(data.query.normalized_value)}`} className="btn-primary text-sm flex items-center gap-2">Report this scam <ArrowRight size={14} /></Link>
              <Link to={`/dispute?q=${encodeURIComponent(data.query.normalized_value)}`} className="btn-ghost text-sm">I believe this is wrong</Link>
            </div>
          </section>

          <p className="text-[11px] text-white/25 leading-relaxed px-1">{data.disclaimer}</p>
        </div>
      )}
    </div>
  )
}
