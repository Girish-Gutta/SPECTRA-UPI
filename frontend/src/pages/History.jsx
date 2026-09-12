import { useEffect, useState, useMemo } from 'react'
import { txAPI } from '../lib/api'
import { Search, Download, Trash2, RefreshCw, Filter } from 'lucide-react'
import VerdictBadge from '../components/VerdictBadge'
import toast from 'react-hot-toast'

const VERDICTS = ['ALL', 'SAFE', 'SUSPICIOUS', 'FRAUD']

export default function History() {
  const [txs, setTxs]         = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState('ALL')
  const [sortBy, setSortBy]   = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [deleting, setDeleting] = useState(null)

  const load = () => {
    setLoading(true)
    txAPI.history(200).then(r => setTxs(r.data)).catch(() => toast.error('Failed to load history')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = useMemo(() => {
    let rows = txs
    if (filter !== 'ALL')          rows = rows.filter(t => t.verdict === filter)
    if (search.trim())             rows = rows.filter(t =>
      t.platform.toLowerCase().includes(search.toLowerCase()) ||
      t.tx_date.includes(search) ||
      String(t.amount).includes(search)
    )
    rows = [...rows].sort((a, b) => {
      let va = a[sortBy], vb = b[sortBy]
      if (typeof va === 'string') va = va.toLowerCase(), vb = vb.toLowerCase()
      return sortDir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
    })
    return rows
  }, [txs, filter, search, sortBy, sortDir])

  const handleSort = (col) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('desc') }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this transaction record?')) return
    setDeleting(id)
    try {
      await txAPI.delete(id)
      setTxs(ts => ts.filter(t => t.id !== id))
      toast.success('Record deleted')
    } catch { toast.error('Delete failed') }
    finally { setDeleting(null) }
  }

  const exportCSV = () => {
    const headers = ['ID', 'Date', 'Time', 'Platform', 'Amount', 'Verdict', 'Score']
    const rows = filtered.map(t => [t.id, t.tx_date, t.tx_time, t.platform, t.amount, t.verdict, t.fraud_score])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    const a = document.createElement('a'); a.href = url; a.download = 'spectra-upi-history.csv'; a.click()
    URL.revokeObjectURL(url)
    toast.success('CSV downloaded')
  }

  const Th = ({ col, label }) => (
    <th className="px-4 py-3 text-left text-xs font-semibold text-white/40 uppercase tracking-wide cursor-pointer hover:text-white/70 select-none"
      onClick={() => handleSort(col)}>
      {label} {sortBy === col ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Transaction History</h1>
          <p className="text-white/40 mt-1 text-sm">{txs.length} total records</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="btn-ghost flex items-center gap-2 py-2 px-3 text-sm">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button onClick={exportCSV} disabled={filtered.length === 0}
            className="btn-ghost flex items-center gap-2 py-2 px-3 text-sm">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input className="input pl-9 py-2 text-sm" placeholder="Search by platform, date, amount…"
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
          <Filter size={13} className="text-white/30 ml-1.5" />
          {VERDICTS.map(v => (
            <button key={v} onClick={() => setFilter(v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === v ? 'bg-brand-600 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'}`}>
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading
          ? <div className="flex items-center justify-center h-48">
              <RefreshCw size={22} className="text-brand-400 animate-spin" />
            </div>
          : filtered.length === 0
            ? <div className="text-center py-16 text-white/30 text-sm">
                No transactions match your filters
              </div>
            : <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-white/5">
                    <tr>
                      <Th col="id"         label="#" />
                      <Th col="tx_date"    label="Date" />
                      <Th col="tx_time"    label="Time" />
                      <Th col="platform"   label="Platform" />
                      <Th col="amount"     label="Amount" />
                      <Th col="fraud_score" label="Score" />
                      <Th col="verdict"    label="Verdict" />
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((tx, i) => (
                      <tr key={tx.id}
                        className={`border-b border-white/5 last:border-0 transition-colors ${i % 2 === 0 ? 'bg-white/1' : ''} hover:bg-white/5`}>
                        <td className="px-4 py-3 text-sm text-white/40">#{tx.id}</td>
                        <td className="px-4 py-3 text-sm">{tx.tx_date}</td>
                        <td className="px-4 py-3 text-sm text-white/60">{tx.tx_time}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center text-xs font-bold text-white/40">
                              {tx.platform.charAt(0)}
                            </div>
                            <span className="text-sm">{tx.platform}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-semibold text-sm">
                          ₹{tx.amount.toLocaleString('en-IN')}
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-white/60">
                          {(tx.fraud_score * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3">
                          <VerdictBadge verdict={tx.verdict} />
                        </td>
                        <td className="px-4 py-3">
                          <button onClick={() => handleDelete(tx.id)} disabled={deleting === tx.id}
                            className="text-white/20 hover:text-red-400 transition-colors p-1">
                            {deleting === tx.id
                              ? <RefreshCw size={14} className="animate-spin" />
                              : <Trash2 size={14} />}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
        }
      </div>

      {/* Summary footer */}
      {filtered.length > 0 && (
        <div className="flex items-center justify-between text-sm text-white/40 px-1">
          <span>Showing {filtered.length} of {txs.length} records</span>
          <span>Total: ₹{filtered.reduce((s, t) => s + t.amount, 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
        </div>
      )}
    </div>
  )
}
