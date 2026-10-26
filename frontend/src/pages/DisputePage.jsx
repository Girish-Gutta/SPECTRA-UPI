import { useCallback, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  AlertTriangle, CheckCircle2, Gavel, Info, Loader2, Lock, ShieldQuestion,
} from 'lucide-react'
import { reportAPI } from '../lib/api'
import TurnstileWidget from '../components/TurnstileWidget'

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message).filter(Boolean).join(' ')
  if (err?.message === 'Network Error') return 'Could not reach the server. Check your connection and try again.'
  return 'Could not submit the dispute. Please try again.'
}

export default function DisputePage() {
  const [params] = useSearchParams()
  const [form, setForm] = useState({
    entity_value: params.get('q') || '',
    entity_type: 'auto',
    reason: '',
    contact_email: '',
  })
  const [captchaToken, setCaptchaToken] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onCaptcha = useCallback(token => setCaptchaToken(token), [])
  const update = (field) => (event) => setForm(prev => ({ ...prev, [field]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (form.entity_value.trim().length < 2) return setError('Enter the identifier that is listed.')
    if (form.reason.trim().length < 20) return setError('Please explain the dispute in at least 20 characters.')

    setSubmitting(true)
    try {
      const res = await reportAPI.dispute({
        entity_value: form.entity_value.trim(),
        entity_type: form.entity_type,
        contact_email: form.contact_email.trim() || null,
        reason: form.reason.trim(),
        captcha_token: captchaToken || null,
      })
      setResult(res.data)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err) {
      setError(apiError(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (result) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-14 animate-fade-in">
        <div className="card text-center border-brand-500/25">
          <div className="w-14 h-14 rounded-full bg-brand-600/15 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={28} className="text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Dispute recorded</h1>
          <p className="text-sm text-white/55 leading-relaxed max-w-lg mx-auto">{result.message}</p>
          <div className="inline-flex flex-wrap items-center justify-center gap-2 mt-5 rounded-xl border border-white/10 bg-black/20 px-4 py-2.5">
            <span className="text-xs text-white/35">Reference</span>
            <span className="font-mono text-sm text-white">#DIS-{result.id}</span>
            <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
              {result.status}
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-7">
            <Link to="/" className="btn-ghost text-sm">Back to lookup</Link>
            <button onClick={() => setResult(null)} className="btn-primary text-sm">Open another dispute</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 animate-fade-in">
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-600/10 border border-brand-500/20 text-brand-300 text-xs font-semibold mb-3">
          <Gavel size={12} /> Listing dispute
        </div>
        <h1 className="text-3xl font-bold">Dispute a listing</h1>
        <p className="text-sm text-white/45 mt-2 leading-relaxed">
          If you own a UPI ID, link or number that appears in a report and believe the listing is
          mistaken, tell the moderators. Disputes do not remove a report automatically.
        </p>
      </div>

      <div className="card border-white/10 mb-5 flex items-start gap-3">
        <ShieldQuestion size={17} className="text-brand-400 mt-0.5 shrink-0" />
        <div className="text-xs text-white/45 leading-relaxed">
          <p className="font-semibold text-white/70 mb-1">What happens next</p>
          A moderator reviews the dispute alongside the original reports. They may ask for proof of ownership,
          clear the listing, or leave it in place. There is no automated email — keep your reference number.
        </div>
      </div>

      <form onSubmit={submit} className="card space-y-5">
        <div>
          <label className="label" htmlFor="entity_value">Listed identifier</label>
          <input
            id="entity_value"
            value={form.entity_value}
            onChange={update('entity_value')}
            className="input font-mono text-sm"
            placeholder="name@bank · https://... · +919876543210"
            required
          />
        </div>

        <div>
          <label className="label" htmlFor="entity_type">Type</label>
          <select id="entity_type" value={form.entity_type} onChange={update('entity_type')} className="input">
            <option value="auto">Auto-detect</option>
            <option value="upi_id">UPI ID</option>
            <option value="url">Link / URL</option>
            <option value="phone">Phone number</option>
            <option value="qr_payload">UPI QR payload</option>
          </select>
        </div>

        <div>
          <label className="label" htmlFor="reason">Why is this listing wrong?</label>
          <textarea
            id="reason"
            rows={6}
            value={form.reason}
            onChange={update('reason')}
            className="input resize-y"
            placeholder="Explain your relationship to the identifier and what the moderators should check. Do not include OTPs, PINs or bank passwords."
            required
          />
          <div className="flex justify-between text-[11px] text-white/30 mt-1">
            <span>At least 20 characters.</span>
            <span>{form.reason.length}/2000</span>
          </div>
        </div>

        <div>
          <label className="label" htmlFor="contact_email">Contact email (recommended)</label>
          <input
            id="contact_email"
            type="email"
            value={form.contact_email}
            onChange={update('contact_email')}
            className="input"
            placeholder="you@example.com"
            autoComplete="email"
          />
          <p className="text-[11px] text-white/30 mt-1.5">Visible only to moderators, never published.</p>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 flex items-start gap-2.5">
          <Lock size={15} className="text-brand-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-white/40 leading-relaxed">
            Anonymous disputes are accepted. A salted request hash is stored only to prevent abuse; raw IPs are not kept.
          </p>
        </div>

        <TurnstileWidget onToken={onCaptcha} />

        {error && (
          <div className="rounded-xl border border-red-500/25 bg-red-950/20 px-4 py-3 text-sm text-red-300 flex items-start gap-2">
            <AlertTriangle size={15} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="text-xs text-white/35 hover:text-white/60 flex items-center gap-1">
            <Info size={12} /> Back to lookup
          </Link>
          <button type="submit" disabled={submitting} className="btn-primary flex items-center gap-2">
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Gavel size={15} />}
            {submitting ? 'Submitting…' : 'Submit dispute'}
          </button>
        </div>
      </form>
    </div>
  )
}
