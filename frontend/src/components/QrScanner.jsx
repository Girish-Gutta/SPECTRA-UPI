import { useEffect, useRef, useState } from 'react'
import jsQR from 'jsqr'
import { Camera, Upload, X, Loader2, ImageOff } from 'lucide-react'
import toast from 'react-hot-toast'

/**
 * Browser-only QR scanner.
 *
 * The image never leaves the browser: camera frames and uploaded files are
 * decoded locally with jsQR. Only the decoded text is handed back to the
 * caller, which then asks the server to look up that identifier.
 */
export default function QrScanner({ open, onClose, onDecode }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const frameRef = useRef(0)
  const doneRef = useRef(false)
  const decodeRef = useRef(onDecode)
  const closeRef = useRef(onClose)

  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => { decodeRef.current = onDecode }, [onDecode])
  useEffect(() => { closeRef.current = onClose }, [onClose])

  useEffect(() => {
    if (!open) return

    let cancelled = false
    doneRef.current = false
    setError('')

    const stopCamera = () => {
      cancelAnimationFrame(frameRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
    }

    const finish = (text) => {
      if (doneRef.current) return
      doneRef.current = true
      stopCamera()
      decodeRef.current?.(text)
      closeRef.current?.()
    }

    const start = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError('This browser cannot access a camera. Upload a QR image instead.')
        return
      }
      setStarting(true)
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
        if (cancelled) {
          stream.getTracks().forEach(track => track.stop())
          return
        }
        streamRef.current = stream
        const video = videoRef.current
        if (!video) return
        video.srcObject = stream
        await video.play()

        const scan = () => {
          if (cancelled || doneRef.current) return
          const el = videoRef.current
          const canvas = canvasRef.current
          if (el && canvas && el.readyState >= 2 && el.videoWidth && el.videoHeight) {
            canvas.width = el.videoWidth
            canvas.height = el.videoHeight
            const ctx = canvas.getContext('2d', { willReadFrequently: true })
            ctx.drawImage(el, 0, 0, canvas.width, canvas.height)
            const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height)
            const result = jsQR(pixels.data, pixels.width, pixels.height)
            if (result?.data) {
              finish(result.data.trim())
              return
            }
          }
          frameRef.current = requestAnimationFrame(scan)
        }
        frameRef.current = requestAnimationFrame(scan)
      } catch (err) {
        if (cancelled) return
        setError(
          err?.name === 'NotAllowedError' || err?.name === 'SecurityError'
            ? 'Camera permission was denied. Upload a QR image instead.'
            : 'Could not start the camera. Upload a QR image instead.'
        )
      } finally {
        if (!cancelled) setStarting(false)
      }
    }

    start()
    return () => { cancelled = true; stopCamera() }
  }, [open])

  useEffect(() => {
    if (open) return
    cancelAnimationFrame(frameRef.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
  }, [open])

  const handleFile = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const objectUrl = URL.createObjectURL(file)
    try {
      const image = await new Promise((resolve, reject) => {
        const img = new Image()
        img.onload = () => resolve(img)
        img.onerror = reject
        img.src = objectUrl
      })
      const canvas = document.createElement('canvas')
      canvas.width = image.naturalWidth
      canvas.height = image.naturalHeight
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      ctx.drawImage(image, 0, 0)
      const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height)
      const result = jsQR(pixels.data, pixels.width, pixels.height)
      if (!result?.data) {
        toast.error('No QR code was found in that image. Try a clearer photo.')
        return
      }
      onDecode?.(result.data.trim())
      onClose?.()
    } catch {
      toast.error('Could not read that image. Please try a different file.')
    } finally {
      URL.revokeObjectURL(objectUrl)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Scan a UPI QR code">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md card bg-gray-900 border-white/10 animate-slide-up">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="font-bold flex items-center gap-2"><Camera size={18} className="text-brand-400" /> Scan a QR code</h2>
            <p className="text-xs text-white/40 mt-1">Decoded locally in your browser. Images are never uploaded.</p>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white p-1" aria-label="Close scanner">
            <X size={20} />
          </button>
        </div>

        <div className="relative aspect-square rounded-xl overflow-hidden bg-black border border-white/10">
          <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
          <canvas ref={canvasRef} className="hidden" />
          {starting && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-white/60">
              <Loader2 size={24} className="animate-spin text-brand-400" />
              <span className="text-xs">Starting camera…</span>
            </div>
          )}
          {!starting && error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center">
              <ImageOff size={28} className="text-white/30" />
              <p className="text-sm text-white/60">{error}</p>
            </div>
          )}
          {!starting && !error && (
            <div className="pointer-events-none absolute inset-8 rounded-lg border-2 border-brand-400/70" />
          )}
        </div>

        <label className="btn-ghost w-full mt-4 flex items-center justify-center gap-2 cursor-pointer text-sm">
          <Upload size={15} /> Upload a QR image
          <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
        </label>

        <p className="text-[11px] text-white/30 mt-3 leading-relaxed">
          Only scan QR codes you are about to pay. If the code opens a link, check that link separately before paying.
        </p>
      </div>
    </div>
  )
}
