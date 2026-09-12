import { Link } from 'react-router-dom'
import { ShieldCheck, Zap, Brain, BarChart3, Lock, Clock } from 'lucide-react'

const features = [
  { icon: Brain,      title: 'ML-Powered Detection',  desc: 'XGBoost model trained on 50,000+ transactions. 97.4% F1 score.' },
  { icon: Zap,        title: 'Instant Results',        desc: 'Real-time fraud scoring in under 100ms — know before you pay.' },
  { icon: BarChart3,  title: 'Risk Breakdown',         desc: 'See exactly why a transaction was flagged with ranked risk factors.' },
  { icon: Clock,      title: 'Full History',           desc: 'Every check is logged. Filter, search, and export your records.' },
  { icon: Lock,       title: 'Secure Auth',            desc: 'JWT-based authentication with bcrypt-hashed passwords.' },
  { icon: ShieldCheck,title: '3 Risk Levels',          desc: 'SAFE, SUSPICIOUS, or FRAUD — with a 0–100% confidence score.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Nav */}
      <nav className="border-b border-white/5 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold tracking-wide">SPECTRA-UPI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login"    className="btn-ghost text-sm py-2 px-4">Sign In</Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-4">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-600/10 border border-brand-500/20 text-brand-400 text-sm font-medium mb-8">
          <ShieldCheck size={14} /> Powered by XGBoost ML
        </div>
        <h1 className="text-5xl lg:text-6xl font-extrabold mb-6 leading-tight">
          Detect UPI Fraud
          <br />
          <span className="bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
            Before It Happens
          </span>
        </h1>
        <p className="text-xl text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
          SPECTRA-UPI analyzes your transaction details against a trained ML model to flag
          fraudulent UPI payments with <strong className="text-white/80">97.4% accuracy</strong>.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/register" className="btn-primary px-8 py-3 text-base">
            Start Checking for Free →
          </Link>
          <Link to="/login" className="btn-ghost px-8 py-3 text-base">
            Sign In
          </Link>
        </div>

        {/* Stats bar */}
        <div className="mt-16 grid grid-cols-3 max-w-lg mx-auto gap-8 border-t border-white/5 pt-10">
          {[['97.4%', 'F1 Score'], ['0.9998', 'AUC-ROC'], ['98%', 'Fraud Recall']].map(([val, lbl]) => (
            <div key={lbl} className="text-center">
              <div className="text-3xl font-extrabold text-brand-400">{val}</div>
              <div className="text-sm text-white/40 mt-1">{lbl}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card hover:border-brand-500/30 transition-all duration-200">
              <div className="w-10 h-10 rounded-xl bg-brand-600/15 flex items-center justify-center mb-4">
                <Icon size={20} className="text-brand-400" />
              </div>
              <h3 className="font-semibold text-white mb-2">{title}</h3>
              <p className="text-sm text-white/50 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="card text-center bg-gradient-to-br from-brand-900/40 to-purple-900/20 border-brand-500/20">
          <h2 className="text-3xl font-bold mb-3">Ready to protect your payments?</h2>
          <p className="text-white/50 mb-8">Free to use. No credit card required.</p>
          <Link to="/register" className="btn-primary px-10 py-3 text-base inline-block">
            Create Account →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-6 py-6 text-center text-sm text-white/30">
        SPECTRA-UPI · Swift Payment Evaluation & Classification for Transaction Risk Analysis
      </footer>
    </div>
  )
}
