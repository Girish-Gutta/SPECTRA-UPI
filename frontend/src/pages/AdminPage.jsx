import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle, Check, ExternalLink, Gavel, Loader2, RefreshCw, ShieldAlert,
  ShieldCheck, X, Inbox, Flag, Mail, Banknote,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { adminAPI } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const REPORT_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'verified', label: 'Verified' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All' },
]

const STATUS_STYLE = {
  pending: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  verified: 'bg-brand-500/10 text-brand-300 border-brand-500/20',
  rejected: 'bg-red-500/10 text-red-300 border-red-500/20',
  open: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  resolved: 'bg-brand-500/10 text-brand-300 border-brand-500/20',
}

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message).filter(Boolean).join(' ')
  return 'The action failed. Please try again.'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function StatusPill({ status }) {
  return (
    <span className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border font-semibold ${STATUS_STYLE[status] || STATUS_STYLE.pending}`}>
      {status}
    </span>
  )
}

function EmptyState({ text }) {
  return (
    <div className="card text-center py-14">
      <Inbox size={30} className="text-white/20 mx-auto mb-3" />
      <p className="text-sm text-white/40">{text}</p>
    </div>
  )
}

export default function AdminPage() {
  const { user } = useAuth()
  const [tab, setTab] = useState('reports')
  const [status, setStatus] = useState('pending')
  const [reports, setReports] = useState([])
  const [disputes, setDisputes] = useState([])
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      if (tab === 'reports') {
        const res = await adminAPI.reports(status)
        setReports(res.data)
      } else {
        const res = await adminAPI.disputes(status === 'pending' ? 'open' : status)
        setDisputes(res.data)
      }
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }, [tab, status])

  useEffect(() => { load() }, [load])

  const switchTab = (next) => {
    setTab(next)
    setStatus(next === 'reports' ? 'pending' : 'open')
  }

  const moderate = async (report, action) => {
    setBusy(`report-${report.id}`)
    try {
      const res = await adminAPI.moderate(report.id, action, notes[report.id] || '')
      toast.success(res.data.message)
      setNotes(prev => ({ ...prev, [report.id]: '' }))
      await load()
    } catch (err) {
      toast.error(apiError(err))
    } finally {
      setBusy(null)
    }
  }

  const resolveDispute = async (dispute, nextStatus) => {
    setBusy(`dispute-${dispute.id}`)
    try {
      await adminAPI.resolveDispute(dispute.id, nextStatus)
      toast.success(nextStatus === 'resolved' ? 'Dispute resolved' : 'Dispute reopened')
      await load()
    } catch (err) {
      toast.error(apiError(err))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5 animate-fade-in">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldCheck size={22} className="text-brand-400" /> Moderation
          </h1>
          <p className="text-sm text-white/40 mt-1">
            Signed in as <span className="text-white/65">{user?.full_name}</span> · role <span className="text-amber-300">{user?.role}</span>
          </p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost text-sm flex items-center gap-2 py-2 px-3">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      <div className="card border-amber-500/20 bg-amber-950/10 flex items-start gap-2.5 py-4">
        <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-100/75 leading-relaxed">
          Only verify a report after checking the details. Verified reports can produce HIGH RISK for an identifier.
          Pending or rejected reports must never be described publicly as fact.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => switchTab('reports')}
          className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors flex items-center gap-2 ${
            tab === 'reports' ? 'bg-brand-600/15 text-brand-300 border-brand-500/25' : 'bg-white/5 text-white/50 border-white/10 hover:text-white'
          }`}
        >
          <Flag size={14} /> Reports
        </button>
        <button
          onClick={() => switchTab('disputes')}
          className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors flex items-center gap-2 ${
            tab === 'disputes' ? 'bg-brand-600/15 text-brand-300 border-brand-500/25' : 'bg-white/5 text-white/50 border-white/10 hover:text-white'
          }`}
        >
          <Gavel size={14} /> Disputes
        </button>
        <div className="ml-auto">
          <select value={status} onChange={event => setStatus(event.target.value)} className="input py-2 text-sm w-40">
            {(tab === 'reports' ? REPORT_STATUSES : [
              { value: 'open', label: 'Open' },
              { value: 'resolved', label: 'Resolved' },
              { value: 'all', label: 'All' },
            ]).map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-950/20 px-4 py-3 text-sm text-red-300 flex items-start gap-2">
          <AlertTriangle size={15} className="mt-0.5 shrink-0" /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 size={24} className="animate-spin text-brand-400" /></div>
      ) : tab === 'reports' ? (
        reports.length === 0 ? <EmptyState text={status === 'pending' ? 'No reports waiting for review.' : 'No reports match this filter.'} /> : (
          <div className="space-y-3">
            {reports.map(report => (
              <article key={report.id} className="card">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs text-white/35">#REP-{report.id}</span>
                      <StatusPill status={report.status} />
                      {report.priority_flag && (
                        <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-red-500/10 text-red-300 border border-red-500/20">priority</span>
                      )}
                      <span className="text-[10px] uppercase tracking-wide text-white/30">{report.entity_type}</span>
                    </div>
                    <div className="font-mono text-sm text-white mt-1 break-all">{report.entity_value}</div>
                    <div className="text-[11px] text-white/30">Public mask: {report.entity_masked}</div>
                  </div>
                  <div className="text-right text-[11px] text-white/35">
                    <div>{formatDate(report.created_at)}</div>
                    <div className="mt-0.5">{report.scam_type_title || report.scam_type_code}</div>
                  </div>
                </div>

                <p className="text-sm text-white/60 leading-relaxed mt-3 whitespace-pre-line">{report.description}</p>

                <div className="flex flex-wrap gap-4 mt-3 text-[11px] text-white/35">
                  {report.amount_lost != null && <span className="flex items-center gap-1"><Banknote size={12} /> ₹{Number(report.amount_lost).toLocaleString('en-IN')}</span>}
                  {report.incident_date && <span>Incident: {report.incident_date}</span>}
                  {report.contact_email && <span className="flex items-center gap-1"><Mail size={12} /> {report.contact_email}</span>}
                  {report.evidence_url && (
                    <a href={report.evidence_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-brand-300 hover:text-brand-200">
                      Evidence <ExternalLink size={11} />
                    </a>
                  )}
                </div>

                {report.status === 'pending' ? (
                  <div className="mt-4 pt-4 border-t border-white/5 flex flex-col sm:flex-row gap-2">
                    <input
                      value={notes[report.id] || ''}
                      onChange={event => setNotes(prev => ({ ...prev, [report.id]: event.target.value }))}
                      className="input py-2 text-sm flex-1"
                      placeholder="Moderator note (optional)"
                      maxLength={1000}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => moderate(report, 'verify')}
                        disabled={busy === `report-${report.id}`}
                        className="btn-primary text-sm py-2 px-3 flex items-center gap-2 bg-brand-700 hover:bg-brand-600"
                      >
                        {busy === `report-${report.id}` ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Verify
                      </button>
                      <button
                        onClick={() => moderate(report, 'reject')}
                        disabled={busy === `report-${report.id}`}
                        className="btn-ghost text-sm py-2 px-3 flex items-center gap-2 text-red-300 border-red-500/20 hover:bg-red-500/10"
                      >
                        <X size={14} /> Reject
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 pt-3 border-t border-white/5 text-[11px] text-white/30">
                    Reviewed {formatDate(report.reviewed_at)} by moderator #{report.reviewed_by ?? '—'}
                  </div>
                )}
              </article>
            ))}
          </div>
        )
      ) : (
        disputes.length === 0 ? <EmptyState text={status === 'open' ? 'No open disputes.' : 'No disputes match this filter.'} /> : (
          <div className="space-y-3">
            {disputes.map(dispute => (
              <article key={dispute.id} className="card">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-white/35">#DIS-{dispute.id}</span>
                      <StatusPill status={dispute.status} />
                    </div>
                    <div className="font-mono text-sm text-white mt-1 break-all">{dispute.entity_value}</div>
                    <div className="text-[11px] text-white/30">Public mask: {dispute.entity_masked}</div>
                  </div>
                  <div className="text-right text-[11px] text-white/35">{formatDate(dispute.created_at)}</div>
                </div>
                <p className="text-sm text-white/60 leading-relaxed mt-3 whitespace-pre-line">{dispute.reason}</p>
                <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-4 border-t border-white/5">
                  <div className="text-[11px] text-white/35 flex items-center gap-1">
                    <Mail size={12} /> {dispute.contact_email || 'No contact email supplied'}
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/lookup?q=${encodeURIComponent(dispute.entity_value)}&type=auto`} className="btn-ghost text-xs py-2 px-3">Open lookup</Link>
                    {dispute.status === 'open' ? (
                      <button
                        onClick={() => resolveDispute(dispute, 'resolved')}
                        disabled={busy === `dispute-${dispute.id}`}
                        className="btn-primary text-xs py-2 px-3 flex items-center gap-2"
                      >
                        {busy === `dispute-${dispute.id}` ? <Loader2 size={13} className="animate-spin" /> : <ShieldAlert size={13} />} Mark resolved
                      </button>
                    ) : (
                      <button
                        onClick={() => resolveDispute(dispute, 'open')}
                        disabled={busy === `dispute-${dispute.id}`}
                        className="btn-ghost text-xs py-2 px-3"
                      >
                        Reopen
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )
      )}
    </div>
  )
}
