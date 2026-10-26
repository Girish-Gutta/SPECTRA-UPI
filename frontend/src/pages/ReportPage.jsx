import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  AlertTriangle, ArrowRight, CheckCircle2, Flag, Info, Loader2, Lock, ShieldCheck,
} from 'lucide-react'
import { publicContentAPI, reportAPI } from '../lib/api'
import TurnstileWidget from '../components/TurnstileWidget'

const FALLBACK_TYPES = [
  { code: 'FP-001', title: 'SIM Swap Fraud' },
  { code: 'FP-002', title: 'Fake Collect Request' },
  { code: 'FP-003', title: 'Fake QR Code Scam' },
  { code: 'FP-004', title: 'OTP / Vishing Fraud' },
  { code: 'FP-005', title: 'OLX / Marketplace Fraud' },
  { code: 'FP-006', title: 'KYC Expiry / Account Block Scam' },
  { code: 'FP-007', title: 'Advance Fee / Lottery Fraud' },
  { code: 'FP-008', title: 'Remote Access / Screen Share Fraud' },
]

const EMPTY_FORM = {
  entity_value: '',
  entity_type: 'auto',
  scam_type_code: '',
  amount_lost: '',
  incident_date: '',
  description: '',
  evidence_url: '',
  contact_email: '',
}

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message).filter(Boolean).join(' ')
  if (err?.message === 'Network Error') return 'Could not reach the server. Check your connection and try again.'
  return 'Could not submit the report. Please try again.'
}

export default function ReportPage() {
  const [params] = useSearchParams()
  const [form, setForm] = useState({ ...EMPTY_FORM, entity_value: params.get('q') || '' })
  const [scamTypes, setScamTypes] = useState(FALLBACK_TYPES)
  const [captchaToken, setCaptchaToken] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onCaptcha = useCallback(token => setCaptchaToken(token), [])

  useEffect(() => {
    let alive = true
    publicContentAPI.awareness()
      .then(res => {
        if (!alive) return
        const types = (res.data?.patterns || []).map(item => ({ code: item.id, title: item.name }))
        if (types.length) setScamTypes(types)
      })
      .catch(() => {})
    return () => { alive = false }
  }, [])

  const update = (field) => (event) => setForm(prev => ({ ...prev, [field]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setError('')

    if (form.entity_value.trim().length < 2) return setError('Enter the UPI ID, link, phone number or QR payload.')
    if (!form.scam_type_code) return setError('Choose the scam type that best matches.')
    if (form.description.trim().length < 10) return setError('Describe what happened in at least 10 characters.')

    setSubmitting(true)
    try {
      const payload = {
        entity_value: form.entity_value.trim(),
        entity_type: form.entity_type,
        scam_type_code: form.scam_type_code,
        amount_lost: form.amount_lost === '' ? null : Number(form.amount_lost),
        incident_date: form.incident_date || null,
        description: form.description.trim(),
        evidence_url: form.evidence_url.trim() || null,
        contact_email: form.contact_email.trim() || null,
        captcha_token: captchaToken || null,
      }
      const res = await reportAPI.create(payload)
      setResult(res.data)
      setForm(prev => ({ ...EMPTY_FORM, entity_value: prev.entity_value }))
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
          <h1 className="text-2xl font-bold mb-2">Report received</h1>
          <p className="text-sm text-white/55 leading-relaxed max-w-lg mx-auto">{result.message}</p>
          <div className="inline-flex flex-wrap items-center justify-center gap-2 mt-5 rounded-xl border border-white/10 bg-black/20 px-4 py-2.5">
            <span className="text-xs text-white/35">Reference</span>
            <span className="font-mono text-sm text-white">#REP-{result.id}</span>
            <span className="text-white/15">·</span>
            <span className="text-xs text-white/35">Identifier</span>
            <span className="font-mono text-xs text-white/70">{result.masked_value}</span>
            <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
              {result.status}
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-7">
            <Link to="/" className="btn-ghost text-sm">Back to lookup</Link>
            <button onClick={() => setResult(null)} className="btn-primary text-sm">Submit another report</button>
          </div>
          <p className="text-[11px] text-white/30 mt-5">
            Keep the reference number. Your report stays private until a moderator reviews it.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 animate-fade-in">
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-semibold mb-3">
          <Flag size={12} /> Community report
        </div>
        <h1 className="text-3xl font-bold">Report a UPI scam</h1>
        <p className="text-sm text-white/45 mt-2 leading-relaxed">
          Tell others what happened. A moderator reviews every report before it becomes public.
          No account is needed.
        </p>
      </div>

      <div className="card border-amber-500/20 bg-amber-950/10 mb-5 flex items-start gap-2.5">
        <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-100/75 leading-relaxed">
          Do not include your UPI PIN, OTP, card number, bank password or another person's private data.
          Reports are allegations, not proof of a crime.
        </p>
      </div>

      <form onSubmit={submit} className="card space-y-5">
        <div>
          <label className="label" htmlFor="entity_value">UPI ID, link, phone number or QR payload</label>
          <input
            id="entity_value"
            value={form.entity_value}
            onChange={update('entity_value')}
            className="input font-mono text-sm"
            placeholder="name@bank · https://... · +919876543210"
            required
          />
          <p className="text-[11px] text-white/30 mt-1.5">Use the exact value you paid or were asked to pay.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
            <label className="label" htmlFor="scam_type_code">Scam type</label>
            <select id="scam_type_code" value={form.scam_type_code} onChange={update('scam_type_code')} className="input" required>
              <option value="">Choose one…</option>
              {scamTypes.map(item => <option key={item.code} value={item.code}>{item.title}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label" htmlFor="amount_lost">Amount lost (₹, optional)</label>
            <input
              id="amount_lost"
              type="number"
              min="0"
              max="100000000"
              step="0.01"
              value={form.amount_lost}
              onChange={update('amount_lost')}
              className="input"
              placeholder="0"
            />
          </div>
          <div>
            <label className="label" htmlFor="incident_date">Date of incident (optional)</label>
            <input
              id="incident_date"
              type="date"
              max={new Date().toISOString().slice(0, 10)}
              value={form.incident_date}
              onChange={update('incident_date')}
              className="input"
            />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="description">What happened?</label>
          <textarea
            id="description"
            rows={5}
            value={form.description}
            onChange={update('description')}
            className="input resize-y"
            placeholder="How did they contact you? What did they ask for? What did you pay?"
            required
          />
          <div className="flex justify-between text-[11px] text-white/30 mt-1">
            <span>At least 10 characters. Do not include OTPs or PINs.</span>
            <span>{form.description.length}/2000</span>
          </div>
        </div>

        <div>
          <label className="label" htmlFor="evidence_url">Evidence link (optional)</label>
          <input
            id="evidence_url"
            value={form.evidence_url}
            onChange={update('evidence_url')}
            className="input"
            placeholder="https://… a screenshot, chat export or public post"
          />
          <p className="text-[11px] text-white/30 mt-1.5">
            The link is stored for moderators only and is never fetched or rendered publicly. Do not link to private data.
          </p>
        </div>

        <div>
          <label className="label" htmlFor="contact_email">Contact email (optional)</label>
          <input
            id="contact_email"
            type="email"
            value={form.contact_email}
            onChange={update('contact_email')}
            className="input"
            placeholder="you@example.com"
            autoComplete="email"
          />
          <p className="text-[11px] text-white/30 mt-1.5">Never shown publicly. There is no automated email — moderators may use it for follow-up.</p>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 flex items-start gap-2.5">
          <Lock size={15} className="text-brand-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-white/40 leading-relaxed">
            We store a salted hash derived from the request IP to stop duplicate spam — never the raw IP.
            If you are signed in, the report is linked to your account so you can track it as verified.
          </p>
        </div>

        <TurnstileWidget onToken={onCaptcha} />

        {error && (
          <div className="rounded-xl border border-red-500/25 bg-red-950/20 px-4 py-3 text-sm text-red-300 flex items-start gap-2">
            <AlertTriangle size={15} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-2 text-[11px] text-white/30">
            <ShieldCheck size={13} /> Reports are reviewed before publishing.
          </div>
          <button type="submit" disabled={submitting} className="btn-primary flex items-center gap-2">
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Flag size={15} />}
            {submitting ? 'Submitting…' : 'Submit report'}
          </button>
        </div>
      </form>

      <div className="mt-5 card flex items-start gap-3">
        <Info size={16} className="text-white/30 mt-0.5 shrink-0" />
        <div className="text-xs text-white/40 leading-relaxed">
          Already lost money? Call <a href="tel:1930" className="text-brand-300 hover:text-brand-200">1930</a> and report at
          <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="text-brand-300 hover:text-brand-200 ml-1 inline-flex items-center gap-1">cybercrime.gov.in <ArrowRight size={11} /></a>.
          Also inform your bank immediately.
        </div>
      </div>
    </div>
  )
}
