import { ShieldCheck, AlertTriangle, XCircle } from 'lucide-react'

const config = {
  SAFE:       { icon: ShieldCheck,   cls: 'badge-safe',  label: 'Safe' },
  SUSPICIOUS: { icon: AlertTriangle, cls: 'badge-warn',  label: 'Suspicious' },
  FRAUD:      { icon: XCircle,       cls: 'badge-fraud', label: 'Fraud' },
}

export default function VerdictBadge({ verdict }) {
  const { icon: Icon, cls, label } = config[verdict] ?? config.SUSPICIOUS
  return (
    <span className={cls}>
      <Icon size={11} />
      {label}
    </span>
  )
}
