import { ShieldAlert, AlertTriangle, SearchX } from 'lucide-react'

const CONFIG = {
  HIGH_RISK: {
    icon: ShieldAlert,
    label: 'HIGH RISK / REPORTED',
    cls: 'bg-red-500/15 text-red-300 border-red-500/30',
    dot: 'bg-red-500',
  },
  SUSPICIOUS: {
    icon: AlertTriangle,
    label: 'SUSPICIOUS',
    cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    dot: 'bg-amber-500',
  },
  NO_REPORTS: {
    icon: SearchX,
    label: 'NO REPORTS FOUND',
    cls: 'bg-white/5 text-white/70 border-white/15',
    dot: 'bg-white/40',
  },
}

export default function LookupBadge({ verdict, size = 'md' }) {
  const cfg = CONFIG[verdict] ?? CONFIG.NO_REPORTS
  const Icon = cfg.icon
  const sizing = size === 'lg'
    ? 'text-sm px-4 py-2 gap-2'
    : 'text-xs px-2.5 py-1 gap-1.5'
  return (
    <span className={`inline-flex items-center rounded-full border font-semibold tracking-wide ${cfg.cls} ${sizing}`}>
      <Icon size={size === 'lg' ? 17 : 12} aria-hidden="true" />
      {cfg.label}
    </span>
  )
}

export { CONFIG as LOOKUP_VERDICT_CONFIG }
