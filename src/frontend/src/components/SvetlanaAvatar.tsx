import { useEffect, useRef } from 'react'
import { API_BASE_URL } from '../api/client'

type Props = {
  size?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  className?: string
}

export default function SvetlanaAvatar({ size = 'md', interactive = false, className = '' }: Props) {
  const ref = useRef<HTMLIFrameElement>(null)
  const dims = size === 'lg' ? 'h-64 w-full' : size === 'sm' ? 'h-12 w-12' : 'h-24 w-24'
  const portraitUrl = `${API_BASE_URL}/static/svetlana/face.png`

  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      if (e.source === ref.current?.contentWindow && e.data?.type === 'svetlana.ready') {
        ref.current?.contentWindow?.postMessage({ type: 'svetlana.emotion', name: 'smile', duration: 1800 }, window.location.origin)
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [])

  return (
    <div className={`${dims} ${className} relative overflow-hidden rounded-2xl border border-slate-200 bg-[#10131a] shadow-lg`} aria-label="Светлана">
      {interactive ? (
        <iframe
          ref={ref}
          title="Светлана — 3D AI-ассистент"
          src="/svetlana/index.html"
          className="h-full w-full border-0"
          loading="lazy"
          sandbox="allow-scripts allow-same-origin"
        />
      ) : (
        <img src={portraitUrl} alt="Светлана" className="h-full w-full object-cover object-top" loading="lazy" />
      )}
      <span className="absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" />
    </div>
  )
}

export function commandSvetlana(iframe: HTMLIFrameElement | null, payload: Record<string, unknown>) {
  iframe?.contentWindow?.postMessage({ type: 'svetlana.command', payload }, window.location.origin)
}
