import { Link } from 'react-router-dom'
import { Zap } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-center px-4">
      <div>
        <div className="text-8xl font-extrabold text-white/5 mb-4">404</div>
        <div className="flex items-center justify-center gap-2 mb-4">
          <Zap size={20} className="text-brand-400" />
          <span className="font-bold">SPECTRA-UPI</span>
        </div>
        <h1 className="text-2xl font-bold mb-2">Page not found</h1>
        <p className="text-white/40 mb-8">The page you're looking for doesn't exist.</p>
        <Link to="/" className="btn-primary px-8 py-3 inline-block">Go Home</Link>
      </div>
    </div>
  )
}
