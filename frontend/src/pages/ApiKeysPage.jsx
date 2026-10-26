import { useEffect, useState } from 'react'
import {
  AlertTriangle, Check, Code2, Copy, KeyRound, Loader2, Plus, ShieldAlert, Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { keysAPI } from '../lib/api'

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message).filter(Boolean).join(' ')
  return 'The request failed. Please try again.'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState(null)
  const [copied, setCopied] = useState(false)
  const [revoking, setRevoking] = useState(null)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await keysAPI.list()
      setKeys(res.data)
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const create = async (event) => {
    event.preventDefault()
    if (name.trim().length < 2) return
    setCreating(true)
    setError('')
    try {
      const res = await keysAPI.create(name.trim())
      setNewKey(res.data)
      setName('')
      await load()
    } catch (err) {
      setError(apiError(err))
    } finally {
      setCreating(false)
    }
  }

  const revoke = async (key) => {
    if (!window.confirm(`Revoke “${key.name}”? Apps using this key will stop working immediately.`)) return
    setRevoking(key.id)
    try {
      await keysAPI.revoke(key.id)
      toast.success('API key revoked')
      setKeys(prev => prev.map(item => item.id === key.id ? { ...item, revoked: true } : item))
    } catch (err) {
      toast.error(apiError(err))
    } finally {
      setRevoking(null)
    }
  }

  const copyKey = async () => {
    if (!newKey?.key) return
    try {
      await navigator.clipboard.writeText(newKey.key)
      setCopied(true)
      toast.success('API key copied')
      setTimeout(() => setCopied(false), 1800)
    } catch {
      toast.error('Could not copy. Select the key manually.')
    }
  }

  const active = keys.filter(key => !key.revoked)
  const sample = `curl "https://your-host/api/v1/lookup?q=name@bank" \\\n  -H "X-API-Key: ${newKey?.key || 'spk_...'}"`

  return (
    <div className="max-w-3xl mx-auto space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><KeyRound size={22} className="text-brand-400" /> Developer API keys</h1>
        <p className="text-sm text-white/40 mt-1">
          Query the same scam lookup from your own app. API keys are optional — the public website never needs one.
        </p>
      </div>

      <div className="card border-white/10">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <h2 className="font-semibold">Create a key</h2>
          <span className="text-[11px] text-white/30">{active.length}/10 active</span>
        </div>
        <form onSubmit={create} className="flex flex-col sm:flex-row gap-2">
          <input
            value={name}
            onChange={event => setName(event.target.value)}
            className="input flex-1"
            placeholder="e.g. merchant-checkout (2–100 characters)"
            maxLength={100}
            required
          />
          <button type="submit" disabled={creating || name.trim().length < 2 || active.length >= 10} className="btn-primary flex items-center justify-center gap-2">
            {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />} Create key
          </button>
        </form>
        <p className="text-[11px] text-white/30 mt-2">
          Free tier. Keys are stored as hashes and cannot be shown again after you leave this page.
        </p>
      </div>

      {newKey && (
        <div className="card border-brand-500/30 bg-brand-950/20">
          <div className="flex items-start gap-2.5 mb-3">
            <ShieldAlert size={16} className="text-brand-300 mt-0.5 shrink-0" />
            <div>
              <div className="font-semibold text-brand-200">Copy this key now</div>
              <p className="text-xs text-brand-100/60 mt-0.5">{newKey.message}</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <code className="flex-1 rounded-xl border border-brand-500/25 bg-black/30 px-3 py-2.5 text-xs text-brand-100 font-mono break-all">
              {newKey.key}
            </code>
            <button onClick={copyKey} className="btn-primary text-sm flex items-center justify-center gap-2 shrink-0">
              {copied ? <Check size={15} /> : <Copy size={15} />} {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <button onClick={() => setNewKey(null)} className="text-[11px] text-white/35 hover:text-white/60 mt-3">I have saved it — hide</button>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/25 bg-red-950/20 px-4 py-3 text-sm text-red-300 flex items-start gap-2">
          <AlertTriangle size={15} className="mt-0.5 shrink-0" /> {error}
        </div>
      )}

      <div className="card">
        <h2 className="font-semibold mb-4">Your keys</h2>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 size={20} className="animate-spin text-brand-400" /></div>
        ) : keys.length === 0 ? (
          <div className="text-center py-8">
            <KeyRound size={26} className="text-white/20 mx-auto mb-2" />
            <p className="text-sm text-white/40">No API keys yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {keys.map(key => (
              <div key={key.id} className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white/85">{key.name}</span>
                    <span className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border ${
                      key.revoked
                        ? 'bg-white/5 text-white/35 border-white/10'
                        : 'bg-brand-500/10 text-brand-300 border-brand-500/20'
                    }`}>
                      {key.revoked ? 'revoked' : 'active'}
                    </span>
                  </div>
                  <div className="text-[11px] text-white/30 mt-0.5 font-mono">{key.prefix} · created {formatDate(key.created_at)}</div>
                </div>
                {!key.revoked && (
                  <button
                    onClick={() => revoke(key)}
                    disabled={revoking === key.id}
                    className="btn-ghost text-xs py-2 px-3 flex items-center gap-2 text-red-300 border-red-500/20 hover:bg-red-500/10"
                  >
                    {revoking === key.id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />} Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="font-semibold flex items-center gap-2 mb-3"><Code2 size={17} className="text-brand-400" /> How to use a key</h2>
        <pre className="rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-white/60 overflow-x-auto whitespace-pre-wrap break-all">{sample}</pre>
        <div className="text-[11px] text-white/35 mt-3 space-y-1">
          <p>The developer endpoint returns the same three outcomes as the website: HIGH RISK / REPORTED, SUSPICIOUS, NO REPORTS FOUND.</p>
          <p>It is rate-limited. Never expose a key in client-side JavaScript — call it from your server.</p>
        </div>
      </div>
    </div>
  )
}
