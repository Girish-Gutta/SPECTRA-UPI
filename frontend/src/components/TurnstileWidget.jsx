import { useEffect, useRef, useState } from 'react'

const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY

/**
 * Cloudflare Turnstile widget (free tier).
 *
 * When VITE_TURNSTILE_SITE_KEY is absent the widget renders a short note and
 * passes a null token. The backend's CAPTCHA_DISABLED setting must match that
 * configuration, otherwise reports are rejected server-side.
 */
export default function TurnstileWidget({ onToken, className = '' }) {
  const containerRef = useRef(null)
  const widgetRef = useRef(null)
  const tokenCallback = useRef(onToken)
  const [status, setStatus] = useState(SITE_KEY ? 'loading' : 'disabled')

  useEffect(() => { tokenCallback.current = onToken }, [onToken])

  useEffect(() => {
    if (!SITE_KEY) {
      tokenCallback.current?.(null)
      return
    }

    let cancelled = false

    const render = () => {
      if (cancelled || !containerRef.current || !window.turnstile) return
      try {
        widgetRef.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          theme: 'dark',
          callback: token => { setStatus('ready'); tokenCallback.current?.(token) },
          'expired-callback': () => tokenCallback.current?.(null),
          'error-callback': () => { setStatus('error'); tokenCallback.current?.(null) },
        })
        setStatus('ready')
      } catch {
        setStatus('error')
      }
    }

    let script = document.querySelector('script[data-spectra-turnstile]')
    if (!script) {
      script = document.createElement('script')
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
      script.async = true
      script.defer = true
      script.dataset.spectraTurnstile = 'true'
      document.head.appendChild(script)
    }

    if (window.turnstile) {
      render()
    } else {
      const previous = script.onload
      script.onload = (event) => {
        previous?.(event)
        render()
      }
      script.onerror = () => { if (!cancelled) setStatus('error') }
    }

    return () => {
      cancelled = true
      if (window.turnstile && widgetRef.current != null) {
        try { window.turnstile.remove(widgetRef.current) } catch { /* already gone */ }
      }
      widgetRef.current = null
    }
  }, [])

  if (!SITE_KEY) {
    return (
      <div className={`rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-xs text-white/40 ${className}`}>
        CAPTCHA is not configured in this build. Submissions will work only if the server has
        CAPTCHA disabled as well.
      </div>
    )
  }

  return (
    <div className={className}>
      <div ref={containerRef} />
      {status === 'error' && (
        <p className="text-xs text-amber-400 mt-2">
          CAPTCHA could not load. Check your connection or disable tracking blockers, then reload.
        </p>
      )}
    </div>
  )
}

export { SITE_KEY as TURNSTILE_SITE_KEY }
